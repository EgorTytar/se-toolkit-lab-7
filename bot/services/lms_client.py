import httpx
from config import LMS_API_URL, LMS_API_KEY


class LMSClient:
    def __init__(self):
        self.base_url = LMS_API_URL
        self.headers = {
            "Authorization": f"Bearer {LMS_API_KEY}"
        }

    def _get(self, path: str, params=None):
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    f"{self.base_url}{path}",
                    headers=self.headers,
                    params=params
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code} {e.response.reason_phrase}"}
        except Exception as e:
            return {"error": str(e)}

    def get_items(self):
        return self._get("/items/")

    def get_pass_rates(self, lab: str):
        return self._get("/analytics/pass-rates", params={"lab": lab})
