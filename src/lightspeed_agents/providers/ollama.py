import os
import requests

from lightspeed_agents.providers.base import LLMProvider


class OllamaProvider(LLMProvider):

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def complete(
        self,
        prompt: str,
        system: str = "",
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=120,
        )
        response.raise_for_status()

        return response.json()["message"]["content"]
