import coloredstrings as cs


def log(msg: str) -> None:
    print(f"[{cs.style.blue('INFO')}]: {msg}")
