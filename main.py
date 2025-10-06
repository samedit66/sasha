import asyncio
import os

import aiogram
import dotenv

from sasha.middlewares import guard, shell
from src.sasha import (
    handlers,
    utils,
)


def main():
    dotenv.load_dotenv()

    utils.log("loaded .env file, starting bot up...")

    asyncio.run(run_bot())


async def run_bot():
    bot = aiogram.Bot(token=os.environ["BOT_TOKEN"])
    dp = aiogram.Dispatcher()

    allowed_ids = [
        int(i) for i in os.environ.get("ALLOWED_IDS", "").split(",")
    ]
    dp.message.middleware(guard.GuardMiddleware(allowed_ids))
    dp.message.middleware(shell.ShellMiddleware("bash", ["-lc"]))

    dp.include_routers(handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    main()
