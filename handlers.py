from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated, ChatPermissions
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR
from get_users_from_chat import get_chat_members
from filters import ChatTypeFilter, ActionsFilter, ACTIONS, BotCommandsFilter, PingFilter
import re
from db_utils import db_ops

router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)


async def get_name_by_id(message, user_id) -> str:
    with db_ops() as cur:
        cur.execute(
            f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE user_id = ?', (user_id, ))
        name, nickname = cur.fetchall()[0]
    if nickname:
        name = nickname
    return name


async def get_name_by_username(message, username) -> str:
    with db_ops() as cur:
        cur.execute(
            f'SELECT real_name, nickname FROM chat{str(message.chat.id)[1:]} WHERE username = ?', (username,))
        name, nickname = cur.fetchall()[0]
    if nickname:
        name = nickname
    return name


async def reply_mention_handler(message: Message) -> (int, str):
    with db_ops() as cur:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            name = (await get_name_by_id(message, user_id))
            return user_id, name
        else:
            mention = re.search(r'@(\w+)', message.text)
            if mention:
                name = (await get_name_by_username(message, mention.group(1)))
                cur.execute(f'SELECT user_id FROM chat{str(message.chat.id)[1:]} WHERE username = ?',
                            (mention.group(1),))
                user_id = cur.fetchall()[0][0]
                return user_id, name
            else:
                return None, None


async def check_admin(message: Message) -> bool:
    with db_ops() as cur:
        cur.execute(f'SELECT is_admin FROM chat{str(message.chat.id)[1:]} WHERE user_id = ?', (message.from_user.id,))
        if cur.fetchall()[0][0]:
            return True
        else:
            return False


@router.message(Command('start', 'старт'))
async def start_handler(message: Message):
    await get_chat_members(message.chat.id)
    await message.reply('Бот успешно добавлен в чат!')


@router.message(PingFilter())
async def ping_handler(message: Message):
    await message.reply('Понг')


@router.message(F.text, ActionsFilter())
async def actions_handling(message: Message):
    for action in ACTIONS:
        if action[0] in message.text.lower():
            sender_name = (await get_name_by_id(message, message.from_user.id))
            receiver_id, receiver_name = (await reply_mention_handler(message))
            if receiver_name:
                await message.reply(f'<a href="tg://user?id={message.from_user.id}">{sender_name}</a> {action[1]} '
                                    f'<a href="tg://user?id={receiver_id}">{receiver_name}</a>')
                return


@router.message(F.text, BotCommandsFilter())
async def commands_handling(message: Message):
    if message.text.lower().startswith('чай ник'):
        await set_nickname(message)
    elif message.text.lower().startswith('чай мой ник'):
        await check_nickname(message)
    elif message.text.lower().startswith('чай бан'):
        await ban(message)
    elif message.text.lower().startswith('чай разбан') or message.text.lower().startswith('чай анбан'):
        await unban(message)
    elif message.text.lower().startswith('чай мут'):
        await mute(message)
    elif message.text.lower().startswith('чай анмут') or message.text.lower().startswith('чай размут'):
        await unmute(message)
    elif message.text.lower().startswith('чай админы'):
        await admins(message)
    elif message.text.lower().startswith('чай +адм'):
        await promote_admin(message)
    elif message.text.lower().startswith('чай -адм'):
        await demote_admin(message)


async def set_nickname(message):
    name = (await get_name_by_id(message, message.from_user.id))
    with db_ops() as cur:
        if message.text.lower().startswith('чай ник сброс'):
            cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?',
                        (None, message.from_user.id))
            await message.reply(f'Никнейм <a href="tg://user?id={message.from_user.id}">{name}</a> сброшен')
        else:
            cur.execute(f'UPDATE chat{str(message.chat.id)[1:]} SET nickname = ? WHERE user_id = ?',
                        (message.text[8:], message.from_user.id))
            await message.reply(
                f'Никнейм <a href="tg://user?id={message.from_user.id}">{name}</a> установлен как {message.text[8:]}')


async def check_nickname(message):
    with db_ops() as cur:
        cur.execute(f'SELECT nickname FROM chat{str(message.chat.id)[1:]} where user_id = ?', (message.from_user.id,))
        nickname = cur.fetchone()[0]
    if nickname:
        await message.reply(f'Ваш никнейм - {nickname}')
    else:
        await message.reply('У вас не установлен никнейм')


async def ban(message: Message):
    if await check_admin(message):
        to_ban_id, name = (await reply_mention_handler(message))
        await message.chat.ban(user_id=to_ban_id)
        await message.reply(f'Пользователь <a href="tg://user?id={to_ban_id}">{name}</a> успешно забанен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def unban(message: Message):
    if await check_admin(message):
        to_unban_id, name = (await reply_mention_handler(message))
        await message.chat.unban(user_id=to_unban_id)
        await message.reply(f'Пользователь <a href="tg://user?id={to_unban_id}">{name}</a> успешно разбанен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def mute(message: Message):
    if await check_admin(message):
        try:
            minutes = int(message.text.split(sep=' ')[-1])
        except ValueError:
            await message.reply('Укажите время в минутах')
            return
        to_mute_id, name = (await reply_mention_handler(message))
        await message.chat.restrict(
            user_id=to_mute_id, until_date=datetime.now() + timedelta(minutes=minutes), permissions=ChatPermissions(can_send_messages=False))
        await message.reply(
            f'Пользователь <a href="tg://user?id={to_mute_id}">{name}</a> успешно замьючен на {minutes} минут')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def unmute(message: Message):
    if await check_admin(message):
        to_unmute_id, name = (await reply_mention_handler(message))
        await message.chat.restrict(user_id=to_unmute_id, permissions=ChatPermissions(can_send_messages=True))
        await message.reply(f'Пользователь <a href="tg://user?id={to_unmute_id}">{name}</a> успешно размьючен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def admins(message: Message):
    answer = 'Список админов чата:\n\n'
    with db_ops() as cur:
        cur.execute(f'SELECT * FROM chat{str(message.chat.id)[1:]} WHERE is_admin = ?', (True,))
        for user in cur.fetchall():
            name = (await get_name_by_id(message, user[2]))
            answer += f'\t<a href="tg://user?id={user[2]}">{name}</a>\n'
    await message.reply(answer)


async def promote_admin(message: Message):
    if await check_admin(message):
        to_promote_id, name = (await reply_mention_handler(message))
        await message.chat.promote(user_id=to_promote_id, can_manage_chat=True, can_delete_messages=True,
                                   can_restrict_members=True, can_promote_members=True, can_change_info=True,
                                   can_invite_users=True, can_post_messages=True, can_edit_messages=True,
                                   can_pin_messages=True)
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def demote_admin(message: Message):
    if await check_admin(message):
        to_demote_id, name = (await reply_mention_handler(message))
        await message.chat.promote(user_id=to_demote_id, can_manage_chat=False, can_delete_messages=False,
                                   can_restrict_members=False, can_promote_members=False, can_change_info=False,
                                   can_invite_users=False, can_post_messages=False, can_edit_messages=False,
                                   can_pin_messages=False)
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


@router.message(F.new_chat_members)
async def somebody_added(message: Message):
    with db_ops() as cur:
        for user in message.new_chat_members:
            cur.execute(f'INSERT OR IGNORE INTO chat{str(message.chat.id)[1:]} (username, user_id, is_admin, real_name) '
                        f'values (?, ?, ?, ?)',
                        (user.username, user.id, False, user.first_name + ' ' + user.last_name
                            if user.last_name is not None else user.first_name))


@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) >> (ADMINISTRATOR | CREATOR)))
async def admin_promoted_reaction(event: ChatMemberUpdated):
    with db_ops() as cur:
        cur.execute(f'UPDATE chat{str(event.chat.id)[1:]} SET is_admin = ? WHERE user_id = ?',
                    (True, event.new_chat_member.user.id))
    name = (await get_name_by_id(event, event.new_chat_member.user.id))
    await event.answer(f'<a href="tg://user?id={event.new_chat_member.user.id}">{name}</a> '
                       f'был(а) повышен(а) до Администратора')


@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) << (ADMINISTRATOR | CREATOR)))
async def admin_demoted_reaction(event: ChatMemberUpdated):
    with db_ops() as cur:
        cur.execute(f'UPDATE chat{str(event.chat.id)[1:]} SET is_admin = ? WHERE user_id = ?',
                    (False, event.new_chat_member.user.id))
    name = (await get_name_by_id(event, event.new_chat_member.user.id))
    await event.answer(f'<a href="tg://user?id={event.new_chat_member.user.id}">{name}</a> '
                       f'был(а) снят(а) с должности Администратора')
