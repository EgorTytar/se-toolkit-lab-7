from handlers.core import basic


def route(command: str) -> str:
    if command.startswith("/start"):
        return basic.start()
    elif command.startswith("/help"):
        return basic.help_cmd()
    elif command.startswith("/health"):
        return basic.health()
    elif command.startswith("/labs"):
        return basic.labs()
    elif command.startswith("/scores"):
        return basic.scores(command)
    else:
        return basic.unknown()
