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
                resp = client.get(f"{self.base_url}{path}", headers=self.headers, params=params)
                resp.raise_for_status()
                return resp.json()
        except httpx.ConnectError:
            return {"error": f"connection refused ({self.base_url})"}
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code} {e.response.reason_phrase}"}
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, data=None):
        """Generic POST request"""
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{self.base_url}{path}", headers=self.headers, json=data)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    # 1. List labs/tasks
    def get_items(self):
        return self._get("/items/")

    # 2. Get learners/students
    def get_learners(self):
        return self._get("/learners/")

    # 3. Score distribution per lab
    def get_scores(self, lab_id: int):
        return self._get("/analytics/scores", params={"lab": f"lab-{lab_id:02}"})

    # 4. Pass rates per lab
    def get_pass_rates(self, lab_id: int):
        data = self._get("/analytics/pass-rates", params={"lab": f"lab-{lab_id:02}"})
        if isinstance(data, list):
            for task in data:
                task["avg_score"] = float(task.get("avg_score") or 0)
        return data

    # 5. Timeline per lab
    def get_timeline(self, lab_id: int):
        return self._get("/analytics/timeline", params={"lab": f"lab-{lab_id:02}"})

    # 6. Groups per lab
    def get_groups(self, lab_id: int):
        data = self._get("/analytics/groups", params={"lab": lab_id})
        groups = []
        for g in data:
            if isinstance(g, dict):
                groups.append({
                    "name": g.get("group", "Unnamed Group"),
                    "avg_score": g.get("avg_score", 0),
                    "students": g.get("students", 0)
                })
        return groups

    # 7. Top learners
    def get_top_learners(self, lab_id: int, limit: int = 5):
        return self._get("/analytics/top-learners", params={"lab": lab_id, "limit": limit})

    # 8. Completion rate per lab
    def get_completion_rate(self, lab_id: int):
        data = self._get("/analytics/completion-rate", params={"lab": f"lab-{lab_id:02}"})
        return data.get("completion_rate") if isinstance(data, dict) else None

    # 9. Trigger backend sync
    def trigger_sync(self):
        return self._post("/pipeline/sync")
