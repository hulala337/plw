"""Offline contract/security tests plus an actual stdio MCP subprocess handshake."""
import asyncio
import base64
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import httpx
from PIL import Image
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import server as s


def png():
    stream = io.BytesIO()
    Image.new("RGBA", (16, 16), (30, 120, 200, 255)).save(stream, "PNG")
    return stream.getvalue()


class Contracts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=s.HERE)
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-test-secret-123", "XINGAI_BASE_URL": "https://xingai.ai", "XINGAI_OUTPUT_ROOT": str(self.root), "XINGAI_VIDEO_ADAPTER": "unconfirmed"})
        self.env.start()
        self.config = s.Settings()
        self.config.mapping = {"models": [{"id": "fixture-image", "source": "mock contract only", "capabilities": {"image_edit": True}, "image_adapter": "openai-images"}], "preferred": {}}
        self.calls = []
        self.polls = 0

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def handler(self, req):
        self.calls.append(req)
        path = req.url.path
        if path == "/v1/models":
            return httpx.Response(200, json={"data": [{"id": "fixture-chat", "supported_endpoint_types": ["openai"]}, {"id": "fixture-image", "supported_endpoint_types": ["image-generation"]}, {"id": "fixture-video", "supported_endpoint_types": ["openai-video"]}, {"id": "image-name-is-not-evidence", "supported_endpoint_types": []}]})
        if path == "/v1/chat/completions":
            return httpx.Response(200, json={"model": "fixture-chat-actual", "choices": [{"message": {"content": "OK " + self.config.key}}]})
        if path in {"/v1/images/generations", "/v1/images/edits"}:
            return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(png()).decode()}]})
        if path == "/v1/video/generations":
            return httpx.Response(200, json={"task_id": "task1", "status": "queued"})
        if path == "/v1/video/generations/task1":
            self.polls += 1
            return httpx.Response(200, json={"status": "in_progress"} if self.polls == 1 else {"status": "completed", "url": "https://xingai.ai/media/result.mp4"})
        if path == "/media/result.mp4":
            self.assertNotIn("authorization", req.headers)
            return httpx.Response(200, content=b"\x00\x00\x00\x18ftypisom" + b"\0" * 16)
        raise AssertionError(path)

    def api(self, handler=None):
        return s.XingAI(self.config, httpx.MockTransport(handler or self.handler))

    async def test_discovery_and_no_name_guessing(self):
        r = await s.dispatch("xingai_list_models", {}, self.api())
        self.assertTrue(r["success"])
        self.assertIsNone(r["models"][-1]["supports_image"])
        self.assertTrue(r["models"][1]["supports_image"])

    async def test_chat_auto_and_redaction(self):
        r = await s.dispatch("xingai_chat", {"messages": [{"role": "user", "content": "test"}]}, self.api())
        self.assertTrue(r["success"])
        self.assertEqual(r["model"], "fixture-chat-actual")
        self.assertNotIn(self.config.key, json.dumps(r))
        self.assertEqual(r["selection_reason"], "only_confirmed_candidate")

    async def test_ambiguous_auto_returns_candidates(self):
        def ambiguous(req):
            return httpx.Response(200, json={"data": [{"id": "one", "supported_endpoint_types": ["openai"]}, {"id": "two", "supported_endpoint_types": ["openai"]}]})
        args = {"messages": [{"role": "user", "content": "test"}]}
        r = await s.dispatch("xingai_chat", args, self.api(ambiguous))
        self.assertEqual(r["error_type"], "model_selection_required")
        self.assertEqual(len(r["candidates"]), 2)
        self.config.mapping["preferred"]["chat"] = "two"
        selected, reason = await self.api(ambiguous).select("auto", "chat")
        self.assertEqual(selected["id"], "two")
        self.assertIn("validated", reason)

    async def test_image_generation_and_edit(self):
        args = {"prompt": "fixture", "output_path": "new.png"}
        r = await s.dispatch("xingai_generate_image", args, self.api())
        self.assertTrue(r["success"], r)
        self.assertEqual(Path(r["output_path"]).read_bytes(), png())
        self.assertEqual(r["mime_type"], "image/png")
        self.assertNotIn("b64_json", json.dumps(r))
        args.update(output_path="edit.png", reference_images=[r["output_path"]])
        r = await s.dispatch("xingai_generate_image", args, self.api())
        self.assertTrue(r["success"], r)
        self.assertIn(b'name="image"', self.calls[-1].content)
        self.assertEqual(self.calls[-1].url.path, "/v1/images/edits")

    async def test_no_overwrite_or_escape_or_ads(self):
        existing = self.root / "keep.png"
        existing.write_bytes(b"original")
        for path in ["keep.png", "../escape.png", "C:/Windows/new.png", "bad.png:stream", "NUL.png", "bad.exe", "//server/share/a.png"]:
            r = await s.dispatch("xingai_generate_image", {"prompt": "fixture", "output_path": path}, self.api())
            self.assertFalse(r["success"], path)
        self.assertEqual(existing.read_bytes(), b"original")
        self.assertFalse(self.calls)

    async def test_reference_and_input_errors(self):
        cases = [("xingai_chat", {"messages": []}), ("xingai_chat", {"messages": [{"role": "user", "content": "test"}], "temperature": 5}), ("xingai_generate_image", {"prompt": "x", "output_path": "x.png", "reference_images": ["a", "b"]}), ("xingai_generate_video", {"prompt": "x", "output_path": "x.mp4", "duration": -1}), ("xingai_list_models", {"extra": "secret"}), ("xingai_generate_video", {"prompt": "x", "output_path": "x.mp4", "task_id": "../bad"})]
        for name, args in cases:
            r = await s.dispatch(name, args, self.api())
            self.assertEqual(r["error_type"], "invalid_arguments")
            self.assertFalse(r["retryable"])
        r = await s.dispatch("xingai_generate_image", {"prompt": "x", "output_path": "x.png", "reference_images": ["https://example.com/x.png"]}, self.api())
        self.assertFalse(r["success"])
        self.assertFalse(self.calls)

    async def test_image_response_validation(self):
        for item, expected in [({"b64_json": "@@"}, "invalid_media"), ({"b64_json": base64.b64encode(b"not an image").decode()}, "invalid_media"), ({}, "invalid_response")]:
            def handler(req):
                return self.handler(req) if req.url.path == "/v1/models" else httpx.Response(200, json={"data": [item]})
            r = await s.dispatch("xingai_generate_image", {"prompt": "x", "output_path": "x.png"}, self.api(handler))
            self.assertEqual(r["error_type"], expected)
        r = await s.dispatch("xingai_generate_image", {"prompt": "x", "output_path": "x.jpg"}, self.api())
        self.assertEqual(r["error_type"], "mime_mismatch")
        self.assertFalse((self.root / "x.jpg").exists())

    async def test_http_errors_and_config_fallback(self):
        for status in [401, 403, 429, 500]:
            r = await s.dispatch("xingai_list_models", {}, self.api(lambda req: httpx.Response(status, json={"error": self.config.key})))
            self.assertFalse(r["success"])
            self.assertEqual(r["retryable"], status in {429, 500})
            self.assertNotIn(self.config.key, json.dumps(r))
        r = await s.dispatch("xingai_list_models", {}, self.api(lambda req: httpx.Response(404)))
        self.assertTrue(r["success"])
        self.assertEqual(r["source"], "explicit_configuration_fallback")
        self.assertEqual(r["models"][0]["availability"], "configured_not_verified")
        self.config.mapping = {"models": []}
        r = await s.dispatch("xingai_list_models", {}, self.api(lambda req: httpx.Response(404)))
        self.assertEqual(r["error_type"], "endpoint_not_found")

    async def test_video_default_and_async_resume(self):
        args = {"prompt": "fixture", "output_path": "new.mp4"}
        r = await s.dispatch("xingai_generate_video", args, self.api())
        self.assertEqual(r["error_type"], "interface_unconfirmed")
        self.assertFalse(any(x.method == "POST" for x in self.calls))
        self.config.video_adapter = "newapi-video-generations"
        with patch.object(s.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("8.8.8.8", 443))]), patch.object(s.asyncio, "sleep", new=unittest.mock.AsyncMock()):
            r = await s.dispatch("xingai_generate_video", args, self.api())
            self.assertTrue(r["success"], r)
            self.assertEqual(r["task_id"], "task1")
            self.calls.clear()
            args.update(output_path="resumed.mp4", task_id="task1")
            r = await s.dispatch("xingai_generate_video", args, self.api())
            self.assertTrue(r["success"], r)
            self.assertFalse(any(x.method == "POST" for x in self.calls))

    async def test_download_policy(self):
        api = self.api()
        for url in ["http://xingai.ai/a", "https://untrusted.example/a", "file:///etc/passwd", "https://xingai.ai:123/a", "https://user:pass@xingai.ai/a"]:
            with self.assertRaises(s.ToolError):
                await api.download(url, 1024)
        with patch.object(s.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaises(s.ToolError):
                await api.download("https://xingai.ai/a", 1024)

    async def test_video_pending_and_failure_keep_task_id(self):
        self.config.video_adapter = "newapi-video-generations"
        args = {"prompt": "fixture", "output_path": "new.mp4"}
        with patch.object(s.time, "monotonic", side_effect=[0, 121]):
            r = await s.dispatch("xingai_generate_video", args, self.api())
        self.assertEqual(r["error_type"], "video_pending")
        self.assertEqual(r["task_id"], "task1")
        def failed(req):
            if req.url.path.endswith("/task1"):
                return httpx.Response(200, json={"status": "failed"})
            return self.handler(req)
        args["task_id"] = "task1"
        r = await s.dispatch("xingai_generate_video", args, self.api(failed))
        self.assertEqual(r["error_type"], "video_task_failed")
        self.assertEqual(r["task_id"], "task1")
        def disconnected(req):
            if req.url.path.endswith("/task1"):
                raise httpx.ReadTimeout("SENSITIVE-NETWORK-DETAIL")
            return self.handler(req)
        r = await s.dispatch("xingai_generate_video", args, self.api(disconnected))
        self.assertEqual(r["task_id"], "task1")
        self.assertNotIn("SENSITIVE-NETWORK-DETAIL", json.dumps(r))

    async def test_missing_key_tls_and_uncertain_submission(self):
        self.config.key = ""
        r = await s.dispatch("xingai_list_models", {}, self.api())
        self.assertEqual(r["error_type"], "missing_api_key")
        self.config.key = "synthetic-key"
        def tls(req):
            raise httpx.ConnectError("CERTIFICATE_VERIFY_FAILED secret")
        r = await s.dispatch("xingai_list_models", {}, self.api(tls))
        self.assertEqual(r["error_type"], "tls_error")
        self.assertFalse(r["retryable"])
        def timed_out(req):
            if req.method == "POST":
                raise httpx.ReadTimeout("private payload")
            return self.handler(req)
        r = await s.dispatch("xingai_generate_image", {"prompt": "fixture", "output_path": "x.png"}, self.api(timed_out))
        self.assertEqual(r["error_type"], "timeout")
        self.assertTrue(r["submission_uncertain"])
        self.assertFalse(r["retryable"])

    async def test_size_bound_and_unknown_tool(self):
        with patch.object(s, "MAX_JSON", 8):
            r = await s.dispatch("xingai_list_models", {}, self.api())
        self.assertEqual(r["error_type"], "response_too_large")
        r = await s.dispatch("does_not_exist", {}, self.api())
        self.assertEqual(r["error_type"], "unknown_tool")


class Stdio(unittest.IsolatedAsyncioTestCase):
    async def test_real_mcp_protocol_and_no_secret_logs(self):
        marker = "synthetic-secret-not-for-logs"
        env = dict(os.environ, OPENAI_API_KEY=marker, XINGAI_BASE_URL="not-a-url")
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as logs:
            params = StdioServerParameters(command=sys.executable, args=[str(s.HERE / "server.py")], env=env)
            async with stdio_client(params, errlog=logs) as (read, write):
                async with ClientSession(read, write) as session:
                    init = await session.initialize()
                    self.assertEqual(init.serverInfo.name, "xingai-multimodel")
                    tools = await session.list_tools()
                    self.assertEqual({x.name for x in tools.tools}, set(s.SPECS))
                    legal = {"xingai_list_models": {}, "xingai_chat": {"messages": [{"role": "user", "content": "PROMPT-LOG-CANARY"}]}, "xingai_generate_image": {"prompt": "PROMPT-LOG-CANARY", "output_path": "a.png"}, "xingai_generate_video": {"prompt": "PROMPT-LOG-CANARY", "output_path": "a.mp4"}}
                    legal['xingai_generate_project_image'] = {'task':'simple icon','asset_id':'TEST','output_path':'a.png'}
                    for name, args in legal.items():
                        result = await session.call_tool(name, args)
                        self.assertEqual(result.structuredContent["error_type"], "configuration_error")
                        self.assertNotIn(marker, result.model_dump_json())
                    result = await session.call_tool("xingai_chat", {"messages": []})
                    self.assertEqual(result.structuredContent["error_type"], "invalid_arguments")
            logs.seek(0)
            log = logs.read()
            self.assertNotIn(marker, log)
            self.assertNotIn("PROMPT-LOG-CANARY", log)
            self.assertNotIn("Authorization", log)


if __name__ == "__main__":
    unittest.main()
