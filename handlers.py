from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command('start'))
async def start_handler(message: Message):
    await message.reply('Чтобы воспользоваться ботом, добавьте его в свой чат')
