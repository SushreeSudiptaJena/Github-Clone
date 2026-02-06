import os
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .llm_service import call_chat, stream_chat

app = FastAPI(title="AI Chat API (Simple)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str
    # Optional: client can send conversation context if your llm_service supports it
    history: Optional[list[dict]] = None


@app.get("/api/health")
async def health():
    return {"status": "ok", "env": os.getenv("APP_ENV", "development")}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        # Adjust if your call_chat signature differs
        text = await call_chat(prompt=req.prompt, history=req.history)
        return {"response": text}
    except TypeError:
        # fallback if your call_chat only accepts prompt
        text = await call_chat(req.prompt)
        return {"response": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")

    async def gen() -> AsyncGenerator[bytes, None]:
        try:
            try:
                async for chunk in stream_chat(prompt=req.prompt, history=req.history):
                    yield chunk.encode("utf-8")
            except TypeError:
                async for chunk in stream_chat(req.prompt):
                    yield chunk.encode("utf-8")
        except Exception as e:
            yield f"\n[stream error] {e}\n".encode("utf-8")

    return StreamingResponse(
        gen(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
