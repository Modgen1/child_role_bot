from datetime import datetime, timedelta
from aiogram.types import Message, ChatPermissions
import re

from db_utils import db_ops


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
            user_id=to_mute_id, until_date=datetime.now() + timedelta(minutes=minutes),
            permissions=ChatPermissions(can_send_messages=False))
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


async def check_rel(first_id, second_id, chat_id):
    with db_ops as cur:
        cur.execute(f'SELECT id, accepted, score, last_action FROM relationships{str(chat_id)[1:]} '
                    f'WHERE (from_id = ? and to_id = ?) or (to_id = ? and first_id = ?)',
                    (first_id, second_id, first_id, second_id))
        fetched = cur.fetchall()
        if fetched:
            return fetched[0]
        else:
            return None


async def rel_start(message: Message):
    to_add_id, to_add_name = (await reply_mention_handler(message))  # TODO Сделать проверку на None
    if to_add_id == 6663096339:
        await message.reply('')  # TODO
        return
    fetched = await check_rel(message.from_user.id, to_add_id, message.chat.id)
    if fetched:
        if fetched[1]:
            await message.reply('')  # TODO
        else:
            await message.reply('')  # TODO
    else:
        with db_ops as cur:
            cur.execute(f'INSERT INTO relationships{str(message.chat.id)[1:]} (from_id, to_id, accepted) '
                        f'VALUES (?, ?, ?)', (message.from_user.id, to_add_id, False))
        await message.reply('')  # TODO


async def rel_stop(message: Message):
    pass  # TODO


async def rel_agree(message: Message):
    pass  # TODO


async def rel_cancel(message: Message):
    pass  # TODO


async def rel_personal_status(message: Message):
    pass  # TODO


async def rel_total_status(message: Message):
    pass  # TODO


async def rel_gift(message: Message):
    pass  # TODO
