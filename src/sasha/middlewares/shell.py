import aiogram

from sasha.core import shell


class ShellMiddleware(aiogram.BaseMiddleware):
    """
    Middleware that injects instance of `shell.Command` to have access to remote shell.
    """

    def __init__(
        self, 
        shell_name: str,
        shell_args: list[str] | None = None,
        default_timeout: int = 30,
    ) -> None:
        super().__init__()
        self.shell = shell.Command(
            shell_name=shell_name,
            shell_args=shell_args,
            default_timeout=default_timeout,
        )

    async def __call__(self, handler, event, data):
        data["terminal"] = self.shell
        return await handler(event, data)
