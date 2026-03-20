"""
LMS Telegram Bot - Entry Point

Usage:
    uv run bot.py --test "your question"  # Test mode (Task 3)
    uv run bot.py                          # Run as Telegram bot (Task 4)
"""
import sys
from handlers.router import route


if __name__ == "__main__":
    # Test mode: --test "query"
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        if len(sys.argv) < 3:
            print("Usage: uv run bot.py --test \"your question\"")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        result = route(query)
        print(result)
    else:
        print("Bot is running! Type 'exit' or 'quit' to stop.")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit"):
                break
            result = route(user_input)
            print(f"Bot: {result}")
