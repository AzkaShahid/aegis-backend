import json

import httpx


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:1.7b"


async def generate_response(
    messages: list[dict],
) -> str:
    """
    Generate a complete response from Ollama.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "think": False,
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=300.0,
        write=30.0,
        pool=30.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        response = await client.post(
            OLLAMA_URL,
            json=payload,
        )

        response.raise_for_status()

        data = response.json()

    return data["message"]["content"]


async def stream_response(
    messages: list[dict],
):
    """
    Stream response tokens from Ollama.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "think": False,
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=300.0,
        write=30.0,
        pool=30.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout
    ) as client:

        async with client.stream(
            "POST",
            OLLAMA_URL,
            json=payload,
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():

                if not line:
                    continue

                data = json.loads(line)

                if data.get("done"):
                    break

                content = (
                    data
                    .get("message", {})
                    .get("content", "")
                )

                if content:
                    yield content