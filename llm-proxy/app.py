import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

UPSTREAM = "https://openrouter.ai/api"
API_KEY = os.environ["LLM_API_KEY"]
# Route every completion to DeepSeek's official hosting; no fallbacks.
PROVIDER_PIN = {"order": ["DeepSeek"], "allow_fallbacks": False}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=300) as client:
        app.state.client = client
        yield


app = FastAPI(lifespan=lifespan)


@app.api_route("/{path:path}", methods=["POST", "GET"])
async def proxy(path: str, request: Request):
    client: httpx.AsyncClient = request.app.state.client
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = None
    if path.endswith("chat/completions") and isinstance(body, dict):
        model = str(body.get("model", ""))
        # Cognee prefixes models with "openrouter/" to force litellm routing;
        # OpenRouter expects the bare slug.
        if model.startswith("openrouter/"):
            model = model[len("openrouter/"):]
            body["model"] = model
        if "minimax" in model:
            # Cognee uses response_format for extraction. Venice does not support it,
            # so use providers that advertise structured-output support.
            body["provider"] = {
                "order": ["CoreWeave", "Together"],
                "allow_fallbacks": False,
            }
        else:
            # Curator/summarization/recall: DeepSeek V4 Flash at max reasoning.
            body["provider"] = PROVIDER_PIN
            body["reasoning"] = {"effort": "max"}
    headers = {"Authorization": f"Bearer {API_KEY}"}
    t0 = time.time()
    if body is not None:
        resp = await client.post(f"{UPSTREAM}/{path}", json=body, headers=headers)
    else:
        resp = await client.get(f"{UPSTREAM}/{path}", headers=headers)
    dt = time.time() - t0
    in_chars = sum(len(str(m.get("content", ""))) for m in body.get("messages", [])) if isinstance(body, dict) else 0
    out_chars = len(resp.content)
    print(f"proxy {path}: {resp.status_code} {dt:.1f}s in={in_chars} out={out_chars}", flush=True)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
