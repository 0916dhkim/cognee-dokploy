import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

UPSTREAM = "https://api.voyageai.com"
API_KEY = os.environ["VOYAGE_API_KEY"]

app = FastAPI()


@app.post("/v1/embeddings")
async def embeddings(request: Request):
    body = await request.json()
    # Voyage rejects encoding_format=float (accepts base64 only) and
    # dimensions (uses output_dimension). Omitting both yields float output.
    body.pop("encoding_format", None)
    if "dimensions" in body:
        body["output_dimension"] = body.pop("dimensions")
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{UPSTREAM}/v1/embeddings",
            json=body,
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
    return JSONResponse(status_code=resp.status_code, content=resp.json())
