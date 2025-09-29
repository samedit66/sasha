import asyncio
import os

import aiogram
import dotenv


def main():
    print("Hello from friday!")
    dotenv.load_dotenv()
    asyncio.run(run_bot())


async def run_bot():
    bot = aiogram.Bot(token=os.environ["BOT_TOKEN"])
    dp = aiogram.Dispatcher()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    main()
