from handlers import basic

def route(command: str) -> str:
    if command.startswith("/start"):
        return basic.start()
    elif command.startswith("/help"):
        return basic.help_cmd()
    elif command.startswith("/health"):
        return basic.health()
    elif command.startswith("/labs"):
        return basic.labs()
    else:
        return basic.unknown()
