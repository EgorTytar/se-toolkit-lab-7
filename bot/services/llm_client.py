import httpx
from config import LLM_API_BASE_URL, LLM_API_KEY, LLM_API_MODEL

class LLMClient:
    def __init__(self):
        if not LLM_API_KEY or not LLM_API_BASE_URL or not LLM_API_MODEL:
            raise ValueError("LLM environment variables are not set")
        self.base_url = LLM_API_BASE_URL.rstrip("/")
        self.api_key = LLM_API_KEY
        self.model = LLM_API_MODEL

    async def chat(self, context: dict):
        """
        context: dict with keys like 'query', 'labs', 'scores'
        Returns a string response from the LLM.
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant for lab analytics."},
            {"role": "user", "content": str(context)}
        ]

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages
                }
            )
            resp.raise_for_status()
            data = resp.json()
            # LiteLLM style: choices[0].message.content
            return data["choices"][0]["message"]["content"]
