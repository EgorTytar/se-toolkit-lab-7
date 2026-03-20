import httpx
from config import LMS_API_URL, LMS_API_KEY

class LMSClient:
    def __init__(self):
        self.base_url = LMS_API_URL
        self.headers = {"Authorization": f"Bearer {LMS_API_KEY}"}

    def _get(self, path: str, params=None):
        """Generic GET request with error handling"""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{self.base_url}{path}", headers=self.headers, params=params)
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

    def get_pass_rates(self, lab_title: str):
        """Fetch per-task pass rates for a given lab"""
        data = self._get("/analytics/pass-rates", params={"lab": lab_title})
        if isinstance(data, dict) and "error" in data:
            return data
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        for task in tasks:
            rate = task.get("pass_rate") or task.get("avg_score") or 0.0
            try:
                task["pass_rate"] = float(rate)
            except (ValueError, TypeError):
                task["pass_rate"] = 0.0
        return tasks

    def get_groups(self, lab_id: int):
        """Fetch group-level analytics for a lab"""
        lab_str = f"lab-{lab_id:02}"  # Matches API: lab-03
        data = self._get("/analytics/groups", params={"lab": lab_str})

        if isinstance(data, dict) and "error" in data:
            return [{"name": "error", "avg_score": 0, "students": 0}]

        groups = []
        for g in data:
            if isinstance(g, dict):
                name = g.get("group", "Unnamed Group")
                avg_score = float(g.get("avg_score", 0))
                students = int(g.get("students", 0))
            else:
                name = str(g)
                avg_score = 0
                students = 0
            groups.append({"name": name, "avg_score": avg_score, "students": students})

        groups.sort(key=lambda x: x["avg_score"], reverse=True)
        return groups
