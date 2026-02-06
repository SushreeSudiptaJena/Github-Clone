import os
import asyncio
from typing import AsyncGenerator
import httpx
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# Try to keep backward compatibility: if OPENAI_API_KEY is present we will use the OpenAI client; otherwise fall back to Hugging Face if available, otherwise a local echo.

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


async def call_gemini(prompt: str, model: str = "gemini-1.5") -> str:
    """
    Call Gemini API for full response (non-streaming).
    """
    if not GEMINI_API_KEY:
        return "(local) Echo: " + prompt

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_output_tokens": 512
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, headers=headers, json=payload) as resp:
            data = await resp.json()
            # Parse Gemini response
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return "(gemini-error) " + str(data)

        

async def stream_gemini(prompt: str, model: str = "gemini-1.5") -> AsyncGenerator[str, None]:
    """
    Stream Gemini API responses chunk by chunk (SSE style).
    """
    if not GEMINI_API_KEY:
        for part in f"(local) Echo: {prompt}".split():
            await asyncio.sleep(0.01)
            yield part + " "
        return

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_output_tokens": 512,
        "stream": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_URL, headers=headers, json=payload) as resp:
            async for line_bytes in resp.content:
                line = line_bytes.decode().strip()
                if line.startswith("data: "):
                    line_json = line[6:]
                    if line_json == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(line_json)
                        text = chunk_data["choices"][0]["delta"].get("content")
                        if text:
                            yield text
                    except Exception:
                        continue

try:
    import openai
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
except Exception:
    openai = None

async def call_chat(prompt: str, model: str = "gpt2") -> str:
    """Call an LLM. Priority: Hugging Face (if HUGGINGFACE_API_TOKEN set) -> OpenAI (if OPENAI_API_KEY set) -> local echo fallback."""
    # Hugging Face Inference (async)
    if HUGGINGFACE_API_TOKEN:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
            resp = await client.post(f"https://api-inference.huggingface.co/models/{model}", headers=headers, json={"inputs": prompt})
            if resp.status_code != 200:
                # Return error as string for downstream handling
                return f"(hf-error) {resp.text}"
            j = resp.json()
            # Many HF models return [{'generated_text': '...'}]
            if isinstance(j, list) and len(j) and isinstance(j[0], dict):
                return j[0].get('generated_text', str(j[0]))
            if isinstance(j, dict):
                # Some models return {'generated_text': '...'}
                return j.get('generated_text', str(j))
            return str(j)

    # OpenAI (blocking call in a thread)
    if OPENAI_API_KEY and openai is not None:
        loop = asyncio.get_event_loop()
        def _blocking_call():
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                max_tokens=512,
                temperature=0.2,
            )
            return resp.choices[0].message.content
        result = await loop.run_in_executor(None, _blocking_call)
        return result

    # Local fallback for dev/test
    return f"(local) Echo: {prompt}"


async def stream_chat(prompt: str, model: str = "gemini-1.5") -> AsyncGenerator[str, None]:
    if GEMINI_API_KEY:
        async for chunk in stream_gemini(prompt, model=model):
            yield chunk
        return
    """Streaming wrapper — if provider doesn't support streaming, simulate it by chunking the full reply."""
    # If Hugging Face token provided, do a normal call and yield chunks
    if HUGGINGFACE_API_TOKEN:
        text = await call_chat(prompt, model=model)
        for part in text.split():
            await asyncio.sleep(0.01)
            yield part + ' '
        return

    # OpenAI streaming if available
    if OPENAI_API_KEY and openai is not None:
        loop = asyncio.get_event_loop()
        def _streaming():
            for chunk in openai.ChatCompletion.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                max_tokens=512,
                temperature=0.2,
                stream=True,
            ):
                yield chunk
        gen = _streaming()
        for chunk in gen:
            try:
                delta = chunk.get('choices', [])[0].get('delta', {})
                text = delta.get('content')
                if text:
                    yield text
            except Exception:
                continue
        return

    # Local fallback streaming
    for part in (f"(local) Echo: {prompt}").split():
        await asyncio.sleep(0.01)
        yield part + ' '
    return
