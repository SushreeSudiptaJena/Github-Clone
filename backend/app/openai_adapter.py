import os
import openai
import asyncio
from typing import AsyncGenerator

openai.api_key = os.getenv("OPENAI_API_KEY")

async def call_chat(prompt: str, model: str = "gpt-4o-mini") -> str:
    # If no API key provided, return a simple fallback response (useful for local dev/tests)
    if not openai.api_key:
        return f"(local) Echo: {prompt}"

    # Simple non-streaming call
    loop = asyncio.get_event_loop()
    def _blocking_call():
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            max_tokens=512,
            temperature=0.2,
        )
        # This returns a dict-like object
        return resp.choices[0].message.content

    result = await loop.run_in_executor(None, _blocking_call)
    return result

async def stream_chat(prompt: str, model: str = "gpt-4o-mini") -> AsyncGenerator[str, None]:
    # If no API key provided, simulate streaming by yielding small chunks
    if not openai.api_key:
        for part in (f"(local) Echo: {prompt}").split():
            await asyncio.sleep(0.01)
            yield part + ' '
        return

    loop = asyncio.get_event_loop()

    def _streaming():
        # openai.ChatCompletion.create(stream=True) returns a generator of chunks
        for chunk in openai.ChatCompletion.create(
            model=model,
            messages=[{"role":"user","content":prompt}],
            max_tokens=512,
            temperature=0.2,
            stream=True,
        ):
            # chunk can be data like {'choices': [{'delta': {'content': '...'}, 'finish_reason': None}]}
            yield chunk

    # Run the blocking generator in a thread and yield text pieces
    gen = _streaming()
    for chunk in gen:
        # Extract text if present
        try:
            delta = chunk.get('choices', [])[0].get('delta', {})
            text = delta.get('content')
            if text:
                yield text
        except Exception:
            continue
