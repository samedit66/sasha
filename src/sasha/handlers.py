import aiogram
from aiogram import types
from aiogram.filters import command


router = aiogram.Router()


@router.message(command.Command("check", "health", "check_health"))
async def check_health(message: types.Message) -> None:
    await message.reply("Alive!")
