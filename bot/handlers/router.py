import os
import sys
import json
from services.lms_client import LMSClient
import httpx
from typing import Any, Dict, List, Optional

# Load LLM settings from environment
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL")
LLM_API_MODEL = os.getenv("LLM_API_MODEL")

client = LMSClient()

# System prompt that encourages tool use
SYSTEM_PROMPT = """You are an analytics assistant for a learning management system. 
You have access to backend tools that provide real data about labs, students, scores, and pass rates.

When the user asks a question:
1. First, determine which tool(s) you need to call to get the data
2. Call the tools with the correct parameters
3. Once you have the data, analyze it and provide a clear, helpful answer

Always use tools to get actual data - don't make up numbers or guess.
If the user's question is unclear, ask for clarification.
If the user greets you or asks what you can do, explain your capabilities briefly.
"""

# Inline keyboard buttons for common actions (Telegram format)
KEYBOARD_BUTTONS = [
    ["📋 List Labs", "📊 View Scores"],
    ["📈 Pass Rates", "🏆 Top Students"],
    ["👥 Groups", "📅 Timeline"],
    ["✅ Completion Rate", "🔄 Refresh Data"],
]


def get_keyboard_hint() -> str:
    """Return a hint about available keyboard buttons."""
    return "\n\n💡 Quick actions: List Labs | View Scores | Pass Rates | Top Students | Groups | Timeline"

# -----------------------------
# Define backend tools for LLM (OpenAI tool calling format)
# -----------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get list of all labs and tasks. Use this first when user asks about available labs or needs lab identifiers.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get all enrolled learners and their group assignments. Use when user asks about students, enrollment, or who is in the system.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution (4 buckets) for a specific lab. Use when user asks about score distribution or how scores are spread.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01', 'lab-03'. Use format 'lab-XX' with zero padding."}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average pass rates and attempt counts for a specific lab. Use when user asks about pass rates, difficulty, or task performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01', 'lab-03'. Use format 'lab-XX' with zero padding."}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get submission timeline showing submissions per day for a lab. Use when user asks about when students submitted or activity over time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01', 'lab-03'. Use format 'lab-XX' with zero padding."}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group scores and student counts for a lab. Use when user asks about group performance, which group is best, or group comparisons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01', 'lab-03'. Use format 'lab-XX' with zero padding."}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by score for a lab. Use when user asks about top students, leaderboard, or best performers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01', 'lab-03'. Use format 'lab-XX' with zero padding."},
                    "limit": {"type": "integer", "description": "Number of top learners to return, e.g. 5, 10. Default is 5."}
                },
                "required": ["lab", "limit"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate percentage for a lab. Use when user asks about completion rate or how many students finished.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01', 'lab-03'. Use format 'lab-XX' with zero padding."}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Trigger ETL pipeline to refresh data from the autochecker. Use when user asks to refresh data, sync, or update the latest submissions.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# -----------------------------
# Tool execution mapping
# -----------------------------
def _summarize_result(result: Any) -> str:
    """Create a brief summary of the result for debug logging."""
    if isinstance(result, list):
        return f"{len(result)} items"
    elif isinstance(result, dict):
        if "error" in result:
            return f"error: {result['error']}"
        return f"{len(result)} keys"
    else:
        return str(result)[:50]


def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments. Returns the tool result."""
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
            # POST request for sync
            with httpx.Client(timeout=10.0) as http_client:
                resp = http_client.post(
                    f"{client.base_url}/pipeline/sync",
                    headers=client.headers
                )
                resp.raise_for_status()
                result = resp.json()
        else:
            result = {"error": f"Unknown tool: {name}"}
    except Exception as e:
        result = {"error": str(e)}

    print(f"[tool] Result: {_summarize_result(result)}", file=sys.stderr)
    return result


# -----------------------------
# Intent router: plain text -> LLM -> backend -> LLM -> answer
# -----------------------------
def route(user_input: str) -> str:
    """
    Route user input through LLM tool calling loop.
    
    Flow:
    1. Send user message + tool definitions to LLM
    2. LLM returns tool calls (or direct answer for greetings)
    3. Execute tools and collect results
    4. Feed tool results back to LLM
    5. LLM produces final answer
    """
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

    # Build conversation messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    # Tool calling loop - iterate until LLM produces final answer
    max_iterations = 5  # Prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call LLM with tool definitions
        payload = {
            "model": LLM_API_MODEL,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",  # Let LLM decide whether to use tools
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            # LLM_API_BASE_URL already includes /v1, so just add /chat/completions
            resp = httpx.post(
                f"{LLM_API_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0  # Increased timeout for multi-step queries
            )
            resp.raise_for_status()
            llm_response = resp.json()
        except httpx.HTTPStatusError as e:
            return f"LLM error: HTTP {e.response.status_code} {e.response.reason_phrase}"
        except httpx.ReadTimeout:
            return "LLM error: request timed out. Try a simpler query."
        except Exception as e:
            return f"LLM error: {str(e)}"

        # Parse LLM response
        choice = llm_response.get("choices", [{}])[0]
        message = choice.get("message", {})
        
        # Check if LLM wants to call tools
        tool_calls = message.get("tool_calls", [])
        
        if not tool_calls:
            # LLM produced final answer (no tool calls)
            content = message.get("content", "")
            return content or "I didn't understand. Here's what I can do: ask me about labs, scores, pass rates, groups, or top learners."

        # Execute each tool call
        tool_results = []
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            tool_name = function.get("name")
            tool_args_str = function.get("arguments", "{}")
            
            try:
                tool_args = json.loads(tool_args_str) if tool_args_str else {}
            except json.JSONDecodeError:
                tool_args = {}

            result = call_tool(tool_name, tool_args)
            tool_results.append({
                "tool_call_id": tool_call.get("id"),
                "result": result
            })

        # Feed tool results back to LLM
        print(f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM", file=sys.stderr)
        
        # Add assistant's message with tool calls to conversation
        messages.append(message)
        
        # Add tool results as separate messages (OpenAI format)
        for tool_result in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": tool_result["tool_call_id"],
                "content": json.dumps(tool_result["result"], default=str)
            })

    return "I'm having trouble processing this request. Please try rephrasing your question."
