from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from get_users_from_chat import get_chat_members
from filters import ChatTypeFilter, ActionsFilter, ACTIONS, BotCommandsFilter
import re
from db_utils import db_ops

router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)


@router.message(Command('start'))
async def start_handler(message: Message):
    await get_chat_members(message.chat.id)
    await message.reply('Бот успешно добавлен в чат!')


@router.message(ActionsFilter())
async def message_handling(message: Message):
    for action in ACTIONS:
        if action[0] in message.text.lower():
            if message.reply_to_message:
                await message.reply(f'{message.from_user.first_name} {action[1]} {message.reply_to_message.from_user.first_name}')
            else:
                mention = re.search(r'@(\w+)', message.text)
                if mention:
                    with db_ops() as cur:
                        cur.execute(f'SELECT first_name FROM chat{str(message.chat.id)[1:]} WHERE username = ?', (mention.group(1),))
                        first_name = cur.fetchall()[0]
                        await message.reply(f'{message.from_user.first_name} обнял(а) {first_name}')


@router.message(BotCommandsFilter())
async def commands_handling(message: Message):
    if 'имя' in message:
        pass
