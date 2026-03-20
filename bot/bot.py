import argparse
import sys
from handlers.router import route


def run_test_mode(input_text: str):
    response = route(input_text)
    print(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, help="Run in test mode with input command")

    args = parser.parse_args()

    if args.test:
        run_test_mode(args.test)
        sys.exit(0)

    # Placeholder for Telegram mode (Task 2+)
    print("Telegram mode not implemented yet")


if __name__ == "__main__":
    main()
