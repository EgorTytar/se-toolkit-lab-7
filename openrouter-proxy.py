from fastapi import FastAPI, Request
import httpx

app = FastAPI()

OPENROUTER_URL = "https://openrouter.ai/api/v1"
API_KEY = "sk-or-REPLACE_ME"

@app.api_route("/v1/{path:path}", methods=["GET", "POST"])
async def proxy(path: str, request: Request):
    url = f"{OPENROUTER_URL}/v1/{path}"

    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {API_KEY}"
    headers["HTTP-Referer"] = "http://localhost"
    headers["X-Title"] = "se-toolkit-lab"

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method,
            url,
            headers=headers,
            content=await request.body()
        )

    return resp.json()
