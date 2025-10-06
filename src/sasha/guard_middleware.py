import aiogram


class GuardMiddleware(aiogram.BaseMiddleware):
    """
    Middleware that only allows certain user IDs to execute remote commands.
    It drops updates from any user whose id is not listed in allowed ones.
    """

    def __init__(self, allowed_ids: list[int]) -> None:
        super().__init__()
        self.allowed_ids = allowed_ids

    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        if user_id not in self.allowed_ids:
            return

        return await handler(event, data)
