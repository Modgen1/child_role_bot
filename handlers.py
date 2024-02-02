from aiogram import Router, F
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


@router.message(Command('start', 'старт'))
async def start_handler(message: Message):
    await get_chat_members(message.chat.id)
    await message.reply('Бот успешно добавлен в чат!')


@router.message(ActionsFilter())
async def message_handling(message: Message):
    for action in ACTIONS:
        if action[0] in message.text.lower():
            with db_ops() as cur:
                cur.execute(f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE user_id = {message.from_user.id}')
                sender_name, sender_nickname = cur.fetchall()[0]
                if sender_nickname:
                    sender_name = sender_nickname
                if message.reply_to_message:
                    cur.execute(f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE user_id = {message.reply_to_message.from_user.id}')
                    receiver_name, receiver_nickname = cur.fetchall()[0]
                    if receiver_nickname:
                        receiver_name = receiver_nickname
                else:
                    mention = re.search(r'@(\w+)', message.text)
                    if mention:
                        cur.execute(f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE username = ?', (mention.group(1),))
                        receiver_name, receiver_nickname = cur.fetchall()[0]
                        if receiver_nickname:
                            receiver_name = receiver_nickname
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
                await message.reply(f'Никнейм {message.from_user.first_name} сброшен')
            else:
                cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?', (message.text[8:], message.from_user.id))
                await message.reply(f'Никнейм {message.from_user.first_name} установлен как {message.text[8:]}')
    elif message.text.lower().startswith('чай мой ник'):
        with db_ops() as cur:
            cur.execute(f'SELECT nickname FROM chat{str(message.chat.id)[1:]} where user_id = ?', (message.from_user.id,))
            nickname = cur.fetchone()[0]
        if nickname:
            await message.reply(f'Ваш никнейм - {nickname}')
        else:
            await message.reply('У вас не установлен никнейм')


@router.message(F.new_chat_members)
async def somebody_added(message: Message):
    with db_ops() as cur:
        for user in message.new_chat_members:
            cur.execute(f'INSERT INTO chat{str(message.chat.id)[1:]} (username, user_id, real_name) values (?, ?, ?)', (user.username, user.id, (user.first_name + ' ' + user.last_name) if user.last_name is not None else user.first_name))
