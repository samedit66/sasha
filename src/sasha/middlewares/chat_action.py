import aiogram
from aiogram.dispatcher import flags
from aiogram.utils import chat_action


class ChatActionMiddleware(aiogram.BaseMiddleware):
    async def __call__(self, handler, event, data):
        long_operation_type = flags.get_flag(data, "long_operation")

        if not long_operation_type:
            return await handler(event, data)

        async with chat_action.ChatActionSender(
            action=long_operation_type,
            chat_id=event.chat.id,
            bot=data["bot"],
        ):
            return await handler(event, data)
