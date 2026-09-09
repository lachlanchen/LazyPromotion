"""FastAPI wrapper for the edge image-quality baseline."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request

from iqa import assess_encoded


app = FastAPI(
    title="Interpretable edge image-quality baseline",
    version="0.1.0",
    description="Non-diagnostic reference API; thresholds require domain calibration.",
)
MAX_BODY_BYTES = 12 * 1024 * 1024


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/assess")
async def assess_image(request: Request) -> dict:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].lower()
    if content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=415, detail="send image/jpeg or image/png bytes")
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="invalid Content-Length") from exc
        if declared_length < 0:
            raise HTTPException(status_code=400, detail="invalid Content-Length")
        if declared_length > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="image exceeds the 12 MiB example limit")
    payload = await request.body()
    if len(payload) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="image exceeds the 12 MiB example limit")
    try:
        return assess_encoded(payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
