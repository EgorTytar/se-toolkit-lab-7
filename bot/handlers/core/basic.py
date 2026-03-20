from services.lms_client import LMSClient

from services.lms_client import LMSClient

# global client
client = LMSClient()


def start():
    return "Welcome to the LMS Bot! 👋"


def help_cmd():
    return (
        "Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show commands\n"
        "/health - Backend status\n"
        "/labs - List labs\n"
        "/scores <lab> - Show lab scores"
    )


def health():
    data = client.get_items()

    if "error" in data:
        return f"Backend error: {data['error']}"

    return f"Backend is healthy. {len(data)} items available."


def labs():
    """Return list of labs with proper titles"""
    data = client.get_items()
    
    if "error" in data:
        return f"Backend error: {data['error']}"

    labs_list = [item for item in data if item.get("type") == "lab"]

    if not labs_list:
        return "No labs found."

    output = "Available labs:\n"
    for lab in labs_list:
        # Use 'title' instead of 'name'
        output += f"- {lab.get('title', 'Unknown')}\n"

    return output.strip()


def scores(command: str):
    """Return per-task pass rates for a given lab"""
    parts = command.strip().split()

    if len(parts) < 2:
        return "Usage: /scores <lab>"

    lab_id = parts[1]
    data = client.get_pass_rates(lab_id)

    if "error" in data:
        return f"Backend error: {data['error']}"

    # If backend wraps tasks in a key
    if isinstance(data, dict) and "tasks" in data:
        tasks = data["tasks"]
    else:
        tasks = data

    if not tasks:
        return f"No data found for {lab_id}"

    output = f"Pass rates for {lab_id}:\n"

    for task in tasks:
        # try multiple possible keys
        name = task.get("task") or task.get("name") or "Unknown"
        rate = task.get("pass_rate", 0.0)
        attempts = task.get("attempts", 0)
        output += f"- {name}: {rate:.1f}% ({attempts} attempts)\n"

    return output.strip()

def unknown():
    return "Unknown command. Try /help"
