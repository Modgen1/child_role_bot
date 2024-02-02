from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from get_users_from_chat import get_chat_members
from filters import ChatTypeFilter, ActionsFilter, ACTIONS, BotCommandsFilter
import re
from db_utils import db_ops

router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)


async def get_name_by_id(message, user_id) -> str:
    with db_ops() as cur:
        cur.execute(
            f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE user_id = {user_id}')
        name, nickname = cur.fetchall()[0]
    if nickname:
        name = nickname
    return name


async def get_name_by_username(message, username) -> str:
    with db_ops() as cur:
        cur.execute(
            f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE username = {username}')
        name, nickname = cur.fetchall()[0]
    if nickname:
        name = nickname
    return name


async def reply_mention_handler(message: Message) -> (int, str):
    with db_ops() as cur:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            name = await get_name_by_id(message, message.reply_to_message.from_user.id)
            return user_id, name
        else:
            mention = re.search(r'@(\w+)', message.text)
            if mention:
                name = await get_name_by_username(message, mention.group(1))
                cur.execute(f'SELECT user_id FROM chat{str(message.chat.id)[1:]} WHERE nickname = ?',
                            (mention.group(1)))
                user_id = cur.fetchall()[0]
                return user_id, name
            else:
                return None, None


async def check_admin(message: Message) -> bool:
    with db_ops() as cur:
        cur.execute(f'SELECT is_admin FROM chat{str(message.chat.id)[1:]} WHERE user_id = ?', (message.from_user.id,))
        if cur.fetchall()[0]:
            return True
        else:
            return False


@router.message(Command('start', 'старт'))
async def start_handler(message: Message):
    await get_chat_members(message.chat.id)
    await message.reply('Бот успешно добавлен в чат!')


@router.message(ActionsFilter())
async def actions_handling(message: Message):
    for action in ACTIONS:
        if action[0] in message.text.lower():
            sender_name = await get_name_by_id(message, message.from_user.id)
            receiver_id, receiver_name = await reply_mention_handler(message)
            if receiver_name:
                await message.reply(f'{sender_name} {action[1]} {receiver_name}')
                return


@router.message(BotCommandsFilter())
async def commands_handling(message: Message):
    if message.text.lower().startswith('чай ник'):
        await set_nickname(message)
    elif message.text.lower().startswith('чай мой ник'):
        await check_nickname(message)
    elif message.text.lower().startswith('чай бан'):
        await ban(message)
    elif message.text.lower().startswith('чай разбан'):
        await unban(message)


async def set_nickname(message):
    with db_ops() as cur:
        if message.text.lower().startswith('чай ник сброс'):
            cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?',
                        (None, message.from_user.id))
            await message.reply(f'Никнейм {message.from_user.first_name} сброшен')
        else:
            cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?',
                        (message.text[8:], message.from_user.id))
            await message.reply(f'Никнейм {message.from_user.first_name} установлен как {message.text[8:]}')


async def check_nickname(message):
    with db_ops() as cur:
        cur.execute(f'SELECT nickname FROM chat{str(message.chat.id)[1:]} where user_id = ?', (message.from_user.id,))
        nickname = cur.fetchone()[0]
    if nickname:
        await message.reply(f'Ваш никнейм - {nickname}')
    else:
        await message.reply('У вас не установлен никнейм')


async def ban(message: Message):
    if check_admin(message):
        to_ban_id, name = await reply_mention_handler(message)
        await message.chat.ban(user_id=to_ban_id)
        await message.reply(f'Пользователь {name} успешно забанен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def unban(message: Message):
    if check_admin(message):
        to_unban_id, name = await reply_mention_handler(message)
        await message.chat.unban(user_id=to_unban_id)
        await message.reply(f'Пользователь {name} успешно разбанен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


@router.message(F.new_chat_members)
async def somebody_added(message: Message):
    with db_ops() as cur:
        for user in message.new_chat_members:
            cur.execute(f'INSERT INTO chat{str(message.chat.id)[1:]} (username, user_id, real_name) values (?, ?, ?)',
                        (user.username, user.id, user.first_name + ' ' + user.last_name if
                         user.last_name is not None else user.first_name))


@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) >> (ADMINISTRATOR | CREATOR)))
async def admin_promoted(event: ChatMemberUpdated):
    with db_ops() as cur:
        cur.execute(f'UPDATE chat{str(event.chat.id)[1:]} SET is admin = ? WHERE user_id = ?',
                    (True, event.new_chat_member.user.id))
    name = get_name_by_id(event, event.new_chat_member.user.id)
    await event.answer(f"{name} был(а) повышен(а) до Администратора")


@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) << (ADMINISTRATOR | CREATOR)))
async def admin_demoted(event: ChatMemberUpdated):
    with db_ops() as cur:
        cur.execute(f'UPDATE chat{str(event.chat.id)[1:]} SET is admin = ? WHERE user_id = ?',
                    (False, event.new_chat_member.user.id))
    name = get_name_by_id(event, event.new_chat_member.user.id)
    await event.answer(f"{name} был(а) снят(а) с должности Администратора")
