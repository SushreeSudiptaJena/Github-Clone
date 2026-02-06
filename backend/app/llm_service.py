import os
import json
from typing import AsyncGenerator, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


def _to_ollama_messages(prompt: str, history: Optional[list[dict]] = None) -> list[dict]:
    msgs: list[dict] = []
    if history:
        for m in history:
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            content = m.get("content")
            if role in ("system", "user", "assistant") and isinstance(content, str) and content.strip():
                msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": prompt})
    return msgs


async def call_chat(prompt: str, history: Optional[list[dict]] = None, model: str = OLLAMA_MODEL) -> str:
    """
    Local LLM via Ollama (non-streaming).
    Requires Ollama running at OLLAMA_HOST.
    """
    payload = {"model": model, "messages": _to_ollama_messages(prompt, history), "stream": False}

    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        if r.status_code >= 400:
            return f"(ollama-http-{r.status_code}) {r.text}"
        data = r.json()
        return (data.get("message") or {}).get("content") or ""


async def stream_chat(
    prompt: str, history: Optional[list[dict]] = None, model: str = OLLAMA_MODEL
) -> AsyncGenerator[str, None]:
    """
    Local LLM via Ollama (streaming). Yields text chunks.
    """
    payload = {"model": model, "messages": _to_ollama_messages(prompt, history), "stream": True}

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{OLLAMA_HOST}/api/chat", json=payload) as r:
            if r.status_code >= 400:
                yield f"(ollama-http-{r.status_code}) {await r.aread()!r}"
                return

            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = evt.get("message") or {}
                chunk = msg.get("content")
                if chunk:
                    yield chunk
                if evt.get("done") is True:
                    return
