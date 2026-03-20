from services.lms_client import LMSClient

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
    data = client.get_items()

    if "error" in data:
        return f"Backend error: {data['error']}"

    labs = [item for item in data if item.get("type") == "lab"]

    if not labs:
        return "No labs found."

    output = "Available labs:\n"
    for lab in labs:
        output += f"- {lab.get('name')}\n"

    return output.strip()


def scores(command: str):
    parts = command.split()

    if len(parts) < 2:
        return "Usage: /scores <lab>"

    lab = parts[1]
    data = client.get_pass_rates(lab)

    if "error" in data:
        return f"Backend error: {data['error']}"

    if not data:
        return f"No data found for {lab}"

    output = f"Pass rates for {lab}:\n"

    for task in data:
        name = task.get("task", "Unknown")
        rate = task.get("pass_rate", 0)
        attempts = task.get("attempts", 0)

        output += f"- {name}: {rate:.1f}% ({attempts} attempts)\n"

    return output.strip()


def unknown():
    return "Unknown command. Try /help"
