import httpx
from config import LMS_API_URL, LMS_API_KEY


class LMSClient:
    def __init__(self):
        self.base_url = LMS_API_URL
        self.headers = {"Authorization": f"Bearer {LMS_API_KEY}"}

    def _get(self, path: str, params=None):
        """Generic GET request with error handling"""
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
        """Fetch all items (labs and tasks)"""
        return self._get("/items/")

    def get_pass_rates(self, lab: str):
        """
        Fetch per-task pass rates for a given lab.
        Returns a list of tasks with 'task', 'pass_rate', 'attempts'.
        """
        data = self._get("/analytics/pass-rates", params={"lab": lab})

        # Propagate error if backend call failed
        if isinstance(data, dict) and "error" in data:
            return data

        # Handle backend wrapping tasks in a "tasks" key
        if isinstance(data, dict) and "tasks" in data:
            tasks = data["tasks"]
        else:
            tasks = data

        # Ensure 'pass_rate' is a float, using 'avg_score' if 'pass_rate' missing
        for task in tasks:
            rate = task.get("pass_rate") or task.get("avg_score") or 0.0
            try:
                task["pass_rate"] = float(rate)
            except (ValueError, TypeError):
                task["pass_rate"] = 0.0

        return tasks
