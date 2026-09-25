"""Independent XingAI stdio MCP server. Never logs prompts, headers or API bodies."""
from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import io
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import socket
import stat
import time
from typing import Any, Literal
from urllib.parse import urlsplit

import httpx
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from image_routing import analyze, load_pool

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
MAX_JSON = 48 * 1024 * 1024
MAX_MEDIA = 32 * 1024 * 1024
MAX_VIDEO = 128 * 1024 * 1024
MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
SUFFIXES = {"image/png": {".png"}, "image/jpeg": {".jpg", ".jpeg"}, "image/webp": {".webp"}, "video/mp4": {".mp4"}}
ENDPOINTS = {"openai": "/v1/chat/completions", "image-generation": "/v1/images/generations", "openai-video": "/v1/videos", "openai-response": "/v1/responses", "anthropic": "/v1/messages", "gemini": "/v1beta/models/{model}:generateContent"}
# Endpoint types observed in XingAI /api/pricing. Not inferred from model names.
TASK_ENDPOINT = {"chat": "openai", "image": "image-generation", "video": "openai-video"}


class ToolError(Exception):
    def __init__(self, kind: str, message: str, retryable: bool = False, **details: Any):
        self.payload = dict(success=False, error_type=kind, message=message, retryable=retryable, **details)
        super().__init__(kind)  # No upstream exception text retained.


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class ListArgs(Args):
    task_type: Literal["chat", "image", "video"] | None = None


class Message(Args):
    role: Literal["system", "developer", "user", "assistant"]
    content: str = Field(min_length=1, max_length=200000)


class ChatArgs(Args):
    model: str = Field(default="auto", min_length=1, max_length=200)
    messages: list[Message] = Field(min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=131072)


class ImageArgs(Args):
    model: str = Field(default="auto", min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=32000)
    output_path: str = Field(min_length=1, max_length=1024)
    size: str | None = Field(default=None, min_length=1, max_length=40)
    quality: str | None = Field(default=None, min_length=1, max_length=40)
    reference_images: list[str] | None = Field(default=None, max_length=1)


class VideoArgs(Args):
    model: str = Field(default="auto", min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=32000)
    output_path: str = Field(min_length=1, max_length=1024)
    duration: float | None = Field(default=None, gt=0, le=120)
    reference_image: str | None = None
    task_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,200}$")


class ProjectImageArgs(Args):
    task: str = Field(min_length=1, max_length=32000)
    asset_id: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')
    output_path: str = Field(min_length=1, max_length=1024)
    reference_images: list[str] = Field(default_factory=list, max_length=1)
    quality_hint: str | None = Field(default=None, max_length=1000)


class Settings:
    def __init__(self):
        self.key = os.getenv("OPENAI_API_KEY", "")
        self.base = os.getenv("XINGAI_BASE_URL", "https://xingai.ai").rstrip("/")
        if self.base.endswith("/v1"):
            self.base = self.base[:-3]
        u = urlsplit(self.base)
        if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment or u.path:
            raise ToolError("configuration_error", "XINGAI_BASE_URL must be an HTTPS origin (optionally ending in /v1).")
        self.host = u.hostname
        root = Path(os.getenv("XINGAI_OUTPUT_ROOT", str(HERE / "outputs")))
        self.output_root = root if root.is_absolute() else PROJECT / root
        self.output_root = self.output_root.absolute()
        if not self.output_root.resolve().is_relative_to(PROJECT) or self.output_root.resolve() == PROJECT:
            raise ToolError("configuration_error", "Output root must be a dedicated directory inside the project.")
        self.download_hosts = {self.host} | {h.strip().lower() for h in os.getenv("XINGAI_DOWNLOAD_HOSTS", "").split(",") if h.strip()}
        self.mapping: dict = {"models": [], "preferred": {}}
        path = os.getenv("XINGAI_MODEL_CONFIG")
        if path:
            p = safe_path(path, PROJECT)
            if p.stat().st_size > 1024 * 1024:
                raise ToolError("configuration_error", "Model config exceeds 1 MiB.")
            try:
                self.mapping = json.loads(p.read_text(encoding="utf-8-sig"))
            except (ValueError, OSError):
                raise ToolError("configuration_error", "Cannot read model configuration JSON.") from None
        validate_mapping(self.mapping)
        self.video_adapter = os.getenv("XINGAI_VIDEO_ADAPTER", "unconfirmed")
        if self.video_adapter not in {"unconfirmed", "newapi-video-generations"}:
            raise ToolError("configuration_error", "Unknown video adapter.")


def safe_path(value: str, root: Path) -> Path:
    """Confine paths and reject links, Windows ADS/devices and traversal on every OS."""
    if not value or "\x00" in value or value.startswith(("\\\\", "//")):
        raise ToolError("unsafe_path", "Invalid or network path.")
    p = Path(value)
    for part in p.parts:
        if part == p.anchor:
            continue
        if part in {"..", ".git"} or ":" in part or part.endswith((" ", ".")) or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part):
            raise ToolError("unsafe_path", "Unsafe path component.")
    p = p if p.is_absolute() else root / p
    for parent in [p, *p.parents]:
        if parent.is_symlink() or (parent.exists() and getattr(parent.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ToolError("unsafe_path", "Symlinks and reparse points are not permitted.")
    p = p.resolve()
    if not p.is_relative_to(root.resolve()):
        raise ToolError("unsafe_path", "Path is outside its permitted root.")
    return p


def validate_mapping(data: Any) -> None:
    if not isinstance(data, dict) or not isinstance(data.get("models", []), list) or not isinstance(data.get("preferred", {}), dict):
        raise ToolError("configuration_error", "Invalid model config structure.")
    seen = set()
    for row in data.get("models", []):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"] or row["id"] in seen or not isinstance(row.get("source"), str) or not row["source"]:
            raise ToolError("configuration_error", "Each configured model needs a unique id and evidence source.")
        seen.add(row["id"])
        caps = row.get("capabilities", {})
        if not isinstance(caps, dict) or any(k not in {"chat", "image", "image_edit", "video"} or not isinstance(v, bool) for k, v in caps.items()):
            raise ToolError("configuration_error", "Invalid capability mapping.")
        if row.get("image_adapter", "openai-images") not in {"openai-images", "unconfirmed"}:
            raise ToolError("configuration_error", "Unknown image adapter.")
    if any(k not in {"chat", "image", "video", "image_edit"} or not isinstance(v, str) for k, v in data.get("preferred", {}).items()):
        raise ToolError("configuration_error", "Invalid model preferences.")


def image_info(raw: bytes) -> tuple[str, tuple[int, int]]:
    try:
        with Image.open(io.BytesIO(raw)) as im:
            fmt, size = im.format, im.size
            if fmt not in MIME or size[0] * size[1] > 40_000_000:
                raise ToolError("invalid_media", "Only bounded PNG/JPEG/WebP images are supported.")
            im.verify()
            return MIME[fmt], size
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ToolError("invalid_media", "Image decoding/validation failed.") from None


class XingAI:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.s = settings
        self.transport = transport

    async def generate_project_image(self, a: ProjectImageArgs) -> dict:
        route = analyze(a.task, a.asset_id, a.quality_hint, bool(a.reference_images))
        generation_entered = False
        try:
            self.output(a.output_path)
            for ref in a.reference_images:
                self.reference(ref)
            try:
                pool, evidence = load_pool(safe_path(str(HERE / 'image_models.toml'), PROJECT))
            except (OSError, ValueError):
                raise ToolError('configuration_error', 'Invalid image_models.toml; no generation submitted.') from None
            model = pool[route['difficulty']]
            route['selected_model'] = model
            verification = evidence.get(model, {})
            if not isinstance(verification, dict) or verification.get('generation_verified') is not True or verification.get('origin') != self.s.base or not verification.get('source'):
                raise ToolError('model_not_verified', 'Selected tier lacks successful generation evidence for this origin. No downgrade, fallback or image was generated.')
            catalog = await self.models()
            if catalog['source'] != 'api':
                raise ToolError('discovery_required', 'Project routing requires live model discovery, not fallback availability.')
            match = next((x for x in catalog['models'] if x['id']==model), None)
            needed = 'image_edit' if a.reference_images else 'image'
            if not match or match['capabilities'].get(needed) is not True:
                raise ToolError('capability_unconfirmed', 'Selected pool model is absent or lacks the required generation/edit capability.')
            if a.reference_images and verification.get('editing_verified') is not True:
                raise ToolError('capability_unconfirmed', 'Reference editing has not been verified for this pool model.')
            # Durable per-asset reservation: repeated/concurrent calls cannot buy
            # another image by changing output_path. Failed/uncertain requests
            # retain the reservation for explicit human reconciliation.
            ledger = safe_path(str(HERE / 'outputs' / 'project_image_attempts'), PROJECT)
            ledger.mkdir(parents=True, exist_ok=True)
            receipt = safe_path(str(ledger / (hashlib.sha256(a.asset_id.upper().encode()).hexdigest() + '.json')), PROJECT)
            try:
                with receipt.open('x', encoding='utf-8') as f:
                    json.dump({'asset_id': a.asset_id, 'selected_model': model,
                               'output_path': a.output_path, 'state': 'reserved_no_automatic_retry'}, f)
            except FileExistsError:
                raise ToolError('asset_already_attempted', 'This asset already has a generation reservation. Reconcile its result before an explicitly authorized rework; no new image submitted.') from None
            # Reuse the existing adapter; it submits n=1 once and never retries.
            generation_entered = True
            result = await self.generate_image(ImageArgs(model=model, prompt=a.task,
                output_path=a.output_path, reference_images=a.reference_images))
            saved = safe_path(result['output_path'], self.s.output_root)
            if not saved.is_file():
                raise ToolError('file_validation_failed', 'API completed but the output file is missing.')
            mime, _ = image_info(saved.read_bytes())
            return {**result, **route, 'mime_type': mime, 'generated_count': 1}
        except ToolError as exc:
            exc.payload.update(route)
            exc.payload['generated_count'] = None if generation_entered else 0
            if generation_entered:
                exc.payload['retryable'] = False
                exc.payload['message'] += ' Do not automatically retry or switch models; generation may have been accepted.'
            raise

    async def request(self, method: str, path: str, *, auth: bool = True, **kwargs) -> tuple[dict, int]:
        try:
            return await self._request(method, path, auth=auth, **kwargs)
        except httpx.HTTPError as exc:
            tls = "CERTIFICATE_VERIFY_FAILED" in str(exc)
            timeout = isinstance(exc, httpx.TimeoutException)
            raise ToolError("tls_error" if tls else "timeout" if timeout else "network_error", "TLS validation failed." if tls else "Network request failed. A submitted generation may already be accepted; never blindly repeat a POST.", method == "GET" and not tls, endpoint=path, submission_uncertain=method == "POST" and not tls) from None

    async def _request(self, method: str, path: str, *, auth: bool = True, **kwargs) -> tuple[dict, int]:
        if auth and not self.s.key:
            raise ToolError("missing_api_key", "Set OPENAI_API_KEY in the server process environment.")
        headers = {"Authorization": "Bearer " + self.s.key} if auth else {}
        async with httpx.AsyncClient(transport=self.transport, timeout=httpx.Timeout(180, connect=15), follow_redirects=False) as client:
            async with client.stream(method, self.s.base + path, headers=headers, **kwargs) as r:
                status = r.status_code
                if not 200 <= status < 300:
                    kind = {401: "authentication_error", 403: "permission_denied", 404: "endpoint_not_found", 405: "method_not_supported", 429: "rate_limited"}.get(status, "api_error")
                    raise ToolError(kind, "XingAI rejected the request; upstream body omitted to protect credentials and prompts.", status in {408, 429} or status >= 500, http_status=status, endpoint=path)
                data = bytearray()
                async for chunk in r.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_JSON:
                        raise ToolError("response_too_large", "API response exceeds the configured bound.")
                try:
                    body = json.loads(data)
                except ValueError:
                    raise ToolError("invalid_response", "API returned non-JSON content.", http_status=status) from None
                if not isinstance(body, dict) or body.get("error") or body.get("success") is False:
                    raise ToolError("api_error", "API returned an error or invalid response object.", http_status=status)
                return body, status

    async def models(self, task: str | None = None) -> dict:
        source = "api"
        warning = None
        try:
            body, status = await self.request("GET", "/v1/models")
            rows = body.get("data")
            if not isinstance(rows, list) or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) for x in rows):
                raise ToolError("invalid_response", "Models response must contain data[] with string ids.")
        except ToolError as exc:
            # Never conceal authentication/rate limit/network errors with a fake list.
            if exc.payload.get("http_status") not in {404, 405, 501} or not self.s.mapping.get("models"):
                raise
            rows = self.s.mapping["models"]
            source, status, warning = "explicit_configuration_fallback", None, exc.payload
        overrides = {x["id"]: x for x in self.s.mapping.get("models", [])}
        try:
            _, registry = load_pool(safe_path(str(HERE / 'image_models.toml'), PROJECT))
        except (OSError, ValueError):
            registry = {}  # Discovery remains usable without optional pool metadata.
        normalized = []
        for row in rows:
            endpoints = row.get("supported_endpoint_types", [])
            if not isinstance(endpoints, list) or any(not isinstance(x, str) for x in endpoints):
                endpoints = []
            caps = {t: True if e in endpoints else None for t, e in TASK_ENDPOINT.items()}
            caps["image_edit"] = None  # Generation capability does not establish edit support.
            override = overrides.get(row["id"], {})
            caps.update(override.get("capabilities", {}))
            item = {"id": row["id"], "provider": row.get("owned_by", row.get("provider")), "provider_source": "API owned_by (not independently verified)", "type": [k for k, v in caps.items() if v is True] or ["unknown"], "capabilities": caps, "supports_image": caps["image"], "supports_video": caps["video"], "supports_text_chat": caps["chat"], "supported_endpoint_types": endpoints, "endpoints": {e: ENDPOINTS[e] for e in endpoints if e in ENDPOINTS}, "evidence": override.get("source", "/v1/models supported_endpoint_types"), "availability": "listed_by_api" if source == "api" else "configured_not_verified", "image_adapter": override.get("image_adapter", "openai-images" if "image-generation" in endpoints else "unconfirmed")}
            record = registry.get(row['id'], {})
            if isinstance(record, dict) and record.get('origin') == self.s.base:
                item['capability_verification'] = {
                    k: record.get(k, 'unverified') if record.get(k) in {'verified', 'unverified'} else 'unverified'
                    for k in ('image_generation', 'image_editing', 'reference_image')}
                item['verification_source'] = record.get('source')
            if task is None or caps[task] is True:
                normalized.append(item)
        return dict(success=True, source=source, endpoint="/v1/models", http_status=status, models=normalized, warning=warning, note="Null capability means unknown. Endpoint availability does not guarantee account quota or a successful generation. No model-name guessing.")

    async def select(self, requested: str, task: str) -> tuple[dict, str]:
        catalog = await self.models()
        models = catalog["models"]
        eligible = [x for x in models if x["capabilities"].get(task) is True]
        if requested != "auto":
            match = next((x for x in models if x["id"] == requested), None)
            if not match:
                raise ToolError("model_not_available", "Requested model is not in discovery/configuration.")
            if match not in eligible:
                raise ToolError("capability_unconfirmed", "Requested model capability is not established; provide an evidence-backed mapping.", candidates=[match])
            return match, "explicit_model"
        preference = self.s.mapping.get("preferred", {}).get(task)
        match = next((x for x in eligible if x["id"] == preference), None)
        if match:
            return match, "configured_preference_validated_against_discovery"
        if len(eligible) == 1:
            return eligible[0], "only_confirmed_candidate"
        raise ToolError("model_selection_required", "No unique safe automatic choice. Choose a discovered candidate or configure a preference; no ranking is invented.", candidates=eligible or models, task_type=task)

    def output(self, value: str, video: bool = False) -> Path:
        p = safe_path(value, self.s.output_root)
        allowed = {".mp4"} if video else {".png", ".jpg", ".jpeg", ".webp"}
        if p.suffix.lower() not in allowed:
            raise ToolError("unsafe_path", "Output extension must match the supported media type.")
        if p.exists():
            raise ToolError("output_exists", "Output already exists; choose a unique filename.")
        return p

    def reference(self, value: str) -> tuple[bytes, str]:
        p = safe_path(value, PROJECT)
        if not p.is_file() or p.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ToolError("invalid_reference", "Reference must be a local PNG/JPEG/WebP inside the project.")
        if p.stat().st_size > 4 * 1024 * 1024:
            raise ToolError("invalid_reference", "Reference exceeds the adapter's conservative 4 MiB limit.")
        raw = p.read_bytes()
        mime, _ = image_info(raw)
        return raw, mime

    async def download(self, url: str, limit: int) -> bytes:
        u = urlsplit(url)
        if u.scheme != "https" or not u.hostname or u.hostname.lower() not in self.s.download_hosts or u.username or u.password or u.port not in {None, 443}:
            raise ToolError("download_host_not_allowed", "Media URL must be HTTPS on an explicitly allowed host; configure XINGAI_DOWNLOAD_HOSTS after checking the provider CDN. A generated result may already exist; do not blindly regenerate.", download_host=u.hostname)
        addresses = await asyncio.to_thread(socket.getaddrinfo, u.hostname, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
            raise ToolError("unsafe_download_url", "Private/local download addresses are forbidden.")
        # Separate client: never forward API Authorization to a CDN or redirect.
        async with httpx.AsyncClient(transport=self.transport, timeout=180, follow_redirects=False) as client:
            async with client.stream("GET", url) as r:
                if r.status_code != 200:
                    raise ToolError("download_failed", "Download failed or redirected; automatic redirects are disabled.", r.status_code >= 500, http_status=r.status_code)
                raw = bytearray()
                async for chunk in r.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > limit:
                        raise ToolError("response_too_large", "Media exceeds the download limit.")
                return bytes(raw)

    def save(self, path: Path, raw: bytes, mime: str) -> None:
        if path.suffix.lower() not in SUFFIXES[mime]:
            raise ToolError("mime_mismatch", "Output extension does not match actual media bytes; no file saved.", mime_type=mime)
        safe_path(str(path), self.s.output_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_path(str(path), self.s.output_root)
        # Exclusive creation avoids overwriting even if two calls race.
        try:
            with path.open("xb") as f:
                try:
                    f.write(raw)
                except BaseException:
                    f.close()
                    path.unlink(missing_ok=True)
                    raise
        except FileExistsError:
            raise ToolError("output_exists", "Output already exists; choose a unique filename.") from None

    async def chat(self, a: ChatArgs) -> dict:
        model, reason = await self.select(a.model, "chat")
        body, status = await self.request("POST", "/v1/chat/completions", json={**a.model_dump(exclude_none=True), "model": model["id"], "stream": False})
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ToolError("invalid_response", "Chat response has no choices.")
        return dict(success=True, model=body.get("model") or model["id"], requested_model=model["id"], model_source="response" if body.get("model") else "request (server omitted model)", selection_reason=reason, http_status=status, api_status="completed", endpoint="/v1/chat/completions", choices=choices, usage=body.get("usage"))

    async def generate_image(self, a: ImageArgs) -> dict:
        target = self.output(a.output_path)
        refs = [self.reference(x) for x in (a.reference_images or [])]
        model, reason = await self.select(a.model, "image_edit" if refs else "image")
        if model["image_adapter"] != "openai-images":
            raise ToolError("interface_unconfirmed", "No verified image adapter is configured for this model.")
        payload = {"model": model["id"], "prompt": a.prompt, "n": 1}
        if a.size is not None:
            payload["size"] = a.size
        if a.quality is not None:
            payload["quality"] = a.quality
        endpoint = "/v1/images/edits" if refs else "/v1/images/generations"
        if refs:
            raw, mime = refs[0]
            # Single reference only; never silently discard additional references.
            body, status = await self.request("POST", endpoint, data={k: str(v) for k, v in payload.items()}, files={"image": ("reference" + next(iter(SUFFIXES[mime])), raw, mime)})
        else:
            body, status = await self.request("POST", endpoint, json=payload)
        items = body.get("data")
        if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], dict):
            raise ToolError("invalid_response", "Expected exactly one generated image.")
        entry = items[0]
        if isinstance(entry.get("b64_json"), str):
            try:
                raw = base64.b64decode(entry["b64_json"], validate=True)
            except (ValueError, binascii.Error):
                raise ToolError("invalid_media", "Invalid image base64.") from None
        elif isinstance(entry.get("url"), str):
            raw = await self.download(entry["url"], MAX_MEDIA)
        else:
            raise ToolError("invalid_response", "Image response has neither base64 nor a URL.")
        if len(raw) > MAX_MEDIA:
            raise ToolError("response_too_large", "Image exceeds the media limit.")
        mime, dimensions = image_info(raw)
        self.save(target, raw, mime)
        return dict(success=True, model=body.get("model") or model["id"], requested_model=model["id"], model_source="response" if body.get("model") else "request (server omitted model)", selection_reason=reason, http_status=status, api_status="completed", endpoint=endpoint, output_path=str(target), mime_type=mime, dimensions=list(dimensions), bytes=len(raw), reference_count=len(refs))

    async def generate_video(self, a: VideoArgs) -> dict:
        target = self.output(a.output_path, video=True)
        ref = self.reference(a.reference_image) if a.reference_image else None
        if self.s.video_adapter == "unconfirmed":
            catalog = await self.models("video")
            raise ToolError("interface_unconfirmed", "XingAI advertises /v1/videos but linked New API docs specify /v1/video/generations. Their equivalence is unconfirmed; no task was created.", candidates=catalog["models"], advertised_endpoint="/v1/videos", documented_endpoint="/v1/video/generations")
        model, reason = await self.select(a.model, "video")
        endpoint = "/v1/video/generations"
        task_id = a.task_id
        if not task_id:
            payload: dict = {"model": model["id"], "prompt": a.prompt}
            if a.duration is not None:
                payload["duration"] = a.duration
            if ref:
                payload["image"] = "data:" + ref[1] + ";base64," + base64.b64encode(ref[0]).decode()
            body, status = await self.request("POST", endpoint, json=payload)
            task_id = body.get("task_id")
            if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", task_id):
                raise ToolError("invalid_response", "Video creation did not return a safe task_id. Do not blindly resubmit.")
        deadline = time.monotonic() + 120
        try:
            while time.monotonic() < deadline:
                body, status = await self.request("GET", endpoint + "/" + task_id)
                state = body.get("status")
                if state == "failed":
                    raise ToolError("video_task_failed", "Video task failed; upstream message omitted.")
                if state == "completed":
                    if not isinstance(body.get("url"), str):
                        raise ToolError("invalid_response", "Completed video has no result URL.")
                    raw = await self.download(body["url"], MAX_VIDEO)
                    if len(raw) < 12 or raw[4:8] != b"ftyp":
                        raise ToolError("invalid_media", "Video does not have an MP4 container signature.")
                    self.save(target, raw, "video/mp4")
                    return dict(success=True, model=body.get("model") or model["id"], model_source="response" if body.get("model") else "request (server omitted model)", selection_reason=reason, output_path=str(target), mime_type="video/mp4", api_status=state, http_status=status, task_id=task_id, endpoint=endpoint)
                if state not in {"queued", "in_progress"}:
                    raise ToolError("invalid_response", "Unknown video task state.")
                await asyncio.sleep(2)
            raise ToolError("video_pending", "Video still pending. Resume with the returned task_id; do not create a duplicate.", True)
        except ToolError as exc:
            exc.payload.update(task_id=task_id, model=model["id"])
            raise
        except (httpx.HTTPError, OSError):
            raise ToolError("network_error", "Video polling/download failed. Resume the same task_id.", True, task_id=task_id, model=model["id"]) from None


SPECS = {
    "xingai_generate_project_image": (ProjectImageArgs, "Route a project image with a deterministic 100-point rubric and mandatory asset importance floors through fixed simple/medium/complex configuration; tiers may share a model. Generates exactly one image; no comparisons, retries or silent downgrades. Unverified tiers fail closed."),
    "xingai_list_models": (ListArgs, "Discover real XingAI model IDs, endpoint types and tri-state capabilities. Optional task_type filter. No model-name guessing."),
    "xingai_chat": (ChatArgs, "Call a discovered text/chat model. model=auto uses evidence and explicit preferences, otherwise returns candidates. Text messages only."),
    "xingai_generate_image": (ImageArgs, "Generate one image to a new file under the output root. Optional single LOCAL reference routes to edits only with explicit edit capability evidence. Never returns image bytes."),
    "xingai_generate_video": (VideoArgs, "Generate/poll/download video only with a confirmed configured adapter. Default returns interface_unconfirmed. task_id resumes an existing task without resubmission."),
}


def scrub(value: Any, key: str) -> Any:
    if isinstance(value, str):
        if key:
            value = value.replace(key, "[REDACTED]")
        value = re.sub(r"(?i)Bearer\s+[^\s\"']+", "Bearer [REDACTED]", value)
        value = re.sub(r"sk-[A-Za-z0-9_*-]{8,}", "[REDACTED]", value)
        # A chat endpoint can return image data from a media model. Do not expose it.
        return re.sub(r"data:(?:image|video)/[^;\s]+;base64,[A-Za-z0-9+/=]+", "[MEDIA_OMITTED]", value)
    if isinstance(value, dict):
        return {scrub(k, key): scrub(v, key) for k, v in value.items() if k.lower() not in {"authorization", "api_key", "b64_json"}}
    if isinstance(value, list):
        return [scrub(x, key) for x in value]
    return value


async def dispatch(name: str, arguments: dict, service: XingAI | None = None) -> dict:
    key = os.getenv("OPENAI_API_KEY", "")
    try:
        if name not in SPECS:
            raise ToolError("unknown_tool", "Unknown tool name.")
        args = SPECS[name][0].model_validate(arguments)
        api = service or XingAI(Settings())
        key = api.s.key
        if name == "xingai_list_models":
            result = await api.models(args.task_type)
        else:
            handler = {"xingai_generate_project_image": api.generate_project_image, "xingai_chat": api.chat, "xingai_generate_image": api.generate_image, "xingai_generate_video": api.generate_video}[name]
            result = await handler(args)
    except ValidationError:
        result = dict(success=False, error_type="invalid_arguments", message="Arguments do not match the tool schema; no request was made.", retryable=False)
    except ToolError as exc:
        result = exc.payload
    except httpx.TimeoutException:
        result = dict(success=False, error_type="timeout", message="Request timed out; generation may have been accepted. Do not blindly retry billable POST requests.", retryable=False)
    except httpx.HTTPError as exc:
        tls = "CERTIFICATE_VERIFY_FAILED" in str(exc)
        result = dict(success=False, error_type="tls_error" if tls else "network_error", message="TLS certificate validation failed." if tls else "Network request failed; no raw network details logged.", retryable=not tls)
    except OSError:
        result = dict(success=False, error_type="io_error", message="File or network I/O failed; check paths and permissions.", retryable=False)
    except Exception:
        result = dict(success=False, error_type="internal_error", message="Unexpected internal failure; no raw exception or prompt logged.", retryable=False)
    return scrub(result, key)


server = Server("xingai-multimodel", instructions="Use XingAI for model discovery and delegated chat/media tasks. Start with xingai_list_models. model=auto never guesses capabilities; inspect candidates when selection is ambiguous. Outputs are local files, not production-approved assets. Do not automatically retry uncertain billable requests. Video task_id resumes polling. No tool changes project business logic or asset-production state.")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [types.Tool(name=name, description=description, inputSchema=cls.model_json_schema(), annotations=types.ToolAnnotations(readOnlyHint=name == "xingai_list_models", destructiveHint=False, openWorldHint=True)) for name, (cls, description) in SPECS.items()]


@server.call_tool(validate_input=False)
async def call_tool(name: str, arguments: dict) -> types.CallToolResult:
    result = await dispatch(name, arguments)
    return types.CallToolResult(content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))], structuredContent=result, isError=not result["success"])


async def main() -> None:
    # The stdio channel is exclusively MCP; disable SDK/HTTP logs that may include inputs.
    logging.disable(logging.CRITICAL)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
