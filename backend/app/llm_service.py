import os
import asyncio
from typing import AsyncGenerator
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# Try to keep backward compatibility: if OPENAI_API_KEY is present we will use the OpenAI client; otherwise fall back to Hugging Face if available, otherwise a local echo.
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

async def stream_chat(prompt: str, model: str = "gpt2") -> AsyncGenerator[str, None]:
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
