import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response

UPSTREAM = "https://openrouter.ai/api"
API_KEY = os.environ["LLM_API_KEY"]
# Route every completion to DeepSeek's official hosting; no fallbacks.
PROVIDER_PIN = {"order": ["DeepSeek"], "allow_fallbacks": False}

app = FastAPI()


@app.api_route("/{path:path}", methods=["POST", "GET"])
async def proxy(path: str, request: Request):
    body = None
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = None
    if path.endswith("chat/completions") and isinstance(body, dict):
        body["provider"] = PROVIDER_PIN
        body["reasoning"] = {"effort": "max"}
    headers = {"Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(timeout=300) as client:
        if body is not None:
            resp = await client.post(f"{UPSTREAM}/{path}", json=body, headers=headers)
        else:
            resp = await client.get(f"{UPSTREAM}/{path}", headers=headers)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
