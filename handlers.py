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
            with db_ops() as cur:
                cur.execute(f'SELECT nickname FROM chat{str(message.chat.id)[1:]} WHERE user_id = {message.from_user.id}')
                sender_name = cur.fetchone()[0]
                if not sender_name:
                    sender_name = message.from_user.first_name
                if message.reply_to_message:
                    cur.execute(f'SELECT nickname FROM chat{str(message.chat.id)[1:]} WHERE user_id = {message.reply_to_message.from_user.id}')
                    receiver_name = cur.fetchone()[-1]
                    if not receiver_name:
                        receiver_name = message.reply_to_message.from_user.first_name
                else:
                    mention = re.search(r'@(\w+)', message.text)
                    if mention:
                        cur.execute(f'SELECT first_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE username = ?', (mention.group(1),))
                        first_name, nickname = cur.fetchall()[0]
                        if nickname:
                            receiver_name = nickname
                        else:
                            receiver_name = first_name
                    else:
                        break
            await message.reply(f'{sender_name} {action[1]} {receiver_name}')
            break


@router.message(BotCommandsFilter())
async def commands_handling(message: Message):
    if message.text.lower().startswith('чай ник'):
        with db_ops() as cur:
            if message.text.lower().startswith('чай ник сброс'):
                cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?', (None, message.from_user.id))
                await message.reply(f'Ник {message.from_user.first_name} сброшен')
            else:
                cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?', (message.text[8:], message.from_user.id))
                await message.reply(f'Ник {message.from_user.first_name} установлен как {message.text[8:]}')
