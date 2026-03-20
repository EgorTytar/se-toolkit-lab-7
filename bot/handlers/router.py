import os
import sys
import json
from services.lms_client import LMSClient
import httpx

# Optional: for easier typing
from typing import Any, Dict

# Load LLM settings from environment
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL")
LLM_API_MODEL = os.getenv("LLM_API_MODEL")

client = LMSClient()


# -----------------------------
# Define backend tools for LLM
# -----------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get all labs and tasks",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get enrolled students and groups",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution for a lab",
            "parameters": {
                "type": "object",
                "properties": {"lab": {"type": "string", "description": "Lab ID, e.g. 'lab-01'"}},
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task averages and attempts for a lab",
            "parameters": {
                "type": "object",
                "properties": {"lab": {"type": "string"}},
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submission timeline for a lab",
            "parameters": {
                "type": "object",
                "properties": {"lab": {"type": "string"}},
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get group performance for a lab",
            "parameters": {
                "type": "object",
                "properties": {"lab": {"type": "string"}},
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string"},
                    "limit": {"type": "integer"}
                },
                "required": ["lab", "limit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate for a lab",
            "parameters": {
                "type": "object",
                "properties": {"lab": {"type": "string"}},
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL sync to refresh backend data",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# -----------------------------
# Tool execution mapping
# -----------------------------
def call_tool(name: str, arguments: Dict[str, Any]):
    print(f"[tool] LLM called: {name}({arguments})", file=sys.stderr)
    try:
        if name == "get_items":
            result = client.get_items()
        elif name == "get_learners":
            result = client._get("/learners/")
        elif name == "get_scores":
            lab = arguments.get("lab")
            result = client._get("/analytics/scores", params={"lab": lab})
        elif name == "get_pass_rates":
            lab = arguments.get("lab")
            result = client.get_pass_rates(lab)
        elif name == "get_timeline":
            lab = arguments.get("lab")
            result = client._get("/analytics/timeline", params={"lab": lab})
        elif name == "get_groups":
            lab = arguments.get("lab")
            result = client._get("/analytics/groups", params={"lab": lab})
        elif name == "get_top_learners":
            lab = arguments.get("lab")
            limit = arguments.get("limit", 5)
            result = client._get("/analytics/top-learners", params={"lab": lab, "limit": limit})
        elif name == "get_completion_rate":
            lab = arguments.get("lab")
            result = client._get("/analytics/completion-rate", params={"lab": lab})
        elif name == "trigger_sync":
            result = client._get("/pipeline/sync")
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e)}

    print(f"[tool] Result: {result}", file=sys.stderr)
    return result


# -----------------------------
# Intent router: plain text -> LLM -> backend
# -----------------------------
def route(user_input: str) -> str:
    # Short-circuit known slash commands
    if user_input.startswith("/"):
        from handlers.core import basic
        if user_input.startswith("/start"):
            return basic.start()
        if user_input.startswith("/help"):
            return basic.help_cmd()
        if user_input.startswith("/health"):
            return basic.health()
        if user_input.startswith("/labs"):
            return basic.labs(client)
        if user_input.startswith("/scores"):
            return basic.scores(user_input)
        return basic.unknown()

    # LLM routing for natural language
    payload = {
        "model": LLM_API_MODEL,
        "input": user_input,
        "functions": TOOLS,
        "temperature": 0.2,
    }

    headers = {"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"}

    try:
        # Call LLM
        resp = httpx.post(f"{LLM_API_BASE_URL}/completions", headers=headers, json=payload, timeout=10.0)
        resp.raise_for_status()
        llm_output = resp.json()
        # Parse the LLM tool call
        tool_call = llm_output.get("tool_call")  # assuming Qwen Code proxy returns this
        if tool_call:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("arguments", {})
            result = call_tool(tool_name, tool_args)
            # Feed result back to LLM for final summary
            # Optional: one more LLM call with tool result can be implemented here
            return json.dumps(result, indent=2)  # simple: return raw JSON
        else:
            # LLM returned plain text instead of a tool call
            return llm_output.get("output_text") or "I didn't understand. Here's what I can do..."
    except httpx.HTTPStatusError as e:
        return f"LLM error: HTTP {e.response.status_code}"
    except Exception as e:
        return f"LLM error: {str(e)}"
