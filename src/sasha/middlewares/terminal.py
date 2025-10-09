import aiogram

from src.sasha.core import terminal


class TerminalMiddleware(aiogram.BaseMiddleware):
    """
    Middleware that injects instance of `shell.Terminal` to have access to remote shell.
    """

    def __init__(self, term: terminal.Terminal) -> None:
        super().__init__()
        self.term = term

    async def __call__(self, handler, event, data):
        data["term"] = self.term
        return await handler(event, data)
