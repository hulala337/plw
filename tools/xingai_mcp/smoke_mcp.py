"""Live MCP smoke test. --image-model opts into one billable test image.

Models must first be discovered, never assumed. Outputs are ignored local test
artifacts, not Pelican production assets. No prompt or credentials are logged.
"""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = Path(__file__).resolve().parent


async def run(args):
    results = {}
    env = dict(os.environ)
    env["XINGAI_VIDEO_ADAPTER"] = "unconfirmed"  # This smoke test never buys a video.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as logs:
        params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], env=env)
        async with stdio_client(params, errlog=logs) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=240)) as session:
                init = await session.initialize()
                results["initialize"] = {"server": init.serverInfo.name, "protocol": init.protocolVersion}
                results["tools"] = [t.name for t in (await session.list_tools()).tools]

                async def call(name, payload):
                    r = (await session.call_tool(name, payload)).structuredContent
                    if not isinstance(r, dict):
                        raise RuntimeError("Tool did not return structured JSON")
                    summary = {k: v for k, v in r.items() if k not in {"models", "choices", "candidates", "usage"}}
                    if "models" in r:
                        summary["count"] = len(r["models"])
                    if "candidates" in r:
                        summary["candidate_count"] = len(r["candidates"])
                    print(json.dumps({"tool": name, "result": summary}, ensure_ascii=True), flush=True)
                    return r, summary

                catalog, results["list_models"] = await call("xingai_list_models", {})
                rows = catalog.get("models", [])
                if catalog["success"]:
                    _, results["auto_chat"] = await call("xingai_chat", {"model": "auto", "messages": [{"role": "user", "content": "Reply with OK."}], "max_tokens": 8})
                    chat = args.chat_model
                    if chat:
                        assert any(x["id"] == chat and x["supports_text_chat"] for x in rows), "Chat test model not discovered"
                        _, results["chat"] = await call("xingai_chat", {"model": chat, "messages": [{"role": "user", "content": "Reply with OK."}], "max_tokens": 8})
                    if args.image_model:
                        assert any(x["id"] == args.image_model and x["supports_image"] for x in rows), "Image test model not discovered"
                        filename = "smoke_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + ".png"
                        _, results["image"] = await call("xingai_generate_image", {"model": args.image_model, "prompt": "An original watercolor study of a green leaf on a plain cream background, no words.", "output_path": filename, "size": "1024x1024"})
                    else:
                        _, results["image_auto"] = await call("xingai_generate_image", {"model": "auto", "prompt": "An original watercolor study of a green leaf.", "output_path": "smoke_auto.png"})
                _, results["video"] = await call("xingai_generate_video", {"model": "auto", "prompt": "A leaf moving gently in the breeze.", "output_path": "smoke_video.mp4", "duration": 4})
                _, results["invalid_arguments"] = await call("xingai_chat", {"messages": []})
        logs.seek(0)
        log = logs.read()
        key = os.getenv("OPENAI_API_KEY", "")
        assert not key or key not in log, "Credential detected in server logs"
        assert "Authorization" not in log
        assert "Reply with OK." not in log
        results["stderr_security"] = {"secret_found": False, "authorization_header_found": False, "test_prompt_found": False, "bytes": len(log.encode())}
    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    (out / "live_smoke_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Live smoke report saved under ignored outputs/live_smoke_report.json")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chat-model", help="A real discovered model ID; submits one short request")
    p.add_argument("--image-model", help="A real discovered model ID; submits one billable image request")
    asyncio.run(run(p.parse_args()))
