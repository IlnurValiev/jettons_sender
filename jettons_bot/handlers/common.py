from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from jettons_bot.get_message import get_text

router = Router()

@router.message(CommandStart())
async def start(message: Message, command: CommandObject):
    text = await get_text("start")
    await message.answer(text)