from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram import F
import db_utils
from filters import ChatTypeFilter


router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)


@router.message(Command('start'))
async def start_handler(message: Message):
    db_utils.db_init(message.chat.id)
    await message.reply('Бот успешно добавлен в чат!')


@router.message(F.text)
async def message_handling(message: Message):
    print(message.text)
    if message.text:
        print('y')
        await message.answer(f'{message.from_user} ответил {message.reply_to_message.from_user}')
    else:
        print('n')
        await message.answer('df')
