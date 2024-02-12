import math
from datetime import datetime, timedelta
from random import randint
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
                if not user_id:
                    return None, None
                return user_id, name
            else:
                return None, None


async def _check_admin(message: Message) -> bool:
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
    if await _check_admin(message):
        to_ban_id, name = (await reply_mention_handler(message))
        if not to_ban_id:
            await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
            return
        await message.chat.ban(user_id=to_ban_id)
        await message.reply(f'Пользователь <a href="tg://user?id={to_ban_id}">{name}</a> успешно забанен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def unban(message: Message):
    if await _check_admin(message):
        to_unban_id, name = (await reply_mention_handler(message))
        if not to_unban_id:
            await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
            return
        await message.chat.unban(user_id=to_unban_id)
        await message.reply(f'Пользователь <a href="tg://user?id={to_unban_id}">{name}</a> успешно разбанен')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def mute(message: Message):
    if await _check_admin(message):
        try:
            minutes = int(message.text.split(sep=' ')[-1])
        except ValueError:
            await message.reply('Укажите время в минутах')
            return
        to_mute_id, name = (await reply_mention_handler(message))
        if not to_mute_id:
            await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
            return
        await message.chat.restrict(
            user_id=to_mute_id, until_date=datetime.now() + timedelta(minutes=minutes),
            permissions=ChatPermissions(can_send_messages=False))
        await message.reply(
            f'Пользователь <a href="tg://user?id={to_mute_id}">{name}</a> успешно замьючен на {minutes} минут')
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def unmute(message: Message):
    if await _check_admin(message):
        to_unmute_id, name = (await reply_mention_handler(message))
        if not to_unmute_id:
            await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
            return
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
    if await _check_admin(message):
        to_promote_id, name = (await reply_mention_handler(message))
        if not to_promote_id:
            await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
            return
        await message.chat.promote(user_id=to_promote_id, can_manage_chat=True, can_delete_messages=True,
                                   can_restrict_members=True, can_promote_members=True, can_change_info=True,
                                   can_invite_users=True, can_post_messages=True, can_edit_messages=True,
                                   can_pin_messages=True)
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def demote_admin(message: Message):
    if await _check_admin(message):
        to_demote_id, name = (await reply_mention_handler(message))
        if not to_demote_id:
            await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
            return
        await message.chat.promote(user_id=to_demote_id, can_manage_chat=False, can_delete_messages=False,
                                   can_restrict_members=False, can_promote_members=False, can_change_info=False,
                                   can_invite_users=False, can_post_messages=False, can_edit_messages=False,
                                   can_pin_messages=False)
    else:
        await message.reply('У вас недостаточно прав для выполнения этой функции')


async def _check_rel(first_id, second_id, chat_id):
    with db_ops() as cur:
        cur.execute(f'SELECT id, from_id, to_id, accepted, score, last_action FROM relationships{str(chat_id)[1:]} '
                    f'WHERE (from_id = ? and to_id = ?) or (to_id = ? and from_id = ?)',
                    (first_id, second_id, first_id, second_id))
        return cur.fetchall()


async def rel_start(message: Message):
    to_add_id, to_add_name = (await reply_mention_handler(message))
    if not to_add_id:
        await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
        return
    if to_add_id == 6663096339:
        await message.reply(f'<b>Вы не можете начать отношения с <a href="tg://user?id=6663096339">Чайлдботом</a>.</b>')
        return
    fetched = await _check_rel(message.from_user.id, to_add_id, message.chat.id)
    if fetched:
        if fetched[0][3]:
            await message.reply(f'<b>Вы уже находитесь в отношениях с '
                                f'<a href="tg://user?id={to_add_id}">{to_add_name}</a>.</b>')
        else:
            if message.from_user.id == fetched[0][1]:
                await message.reply(f'<b>Вы уже предложили <a href="tg://user?id={to_add_id}">{to_add_name}</a> '
                                    f'вступить в отношения, ожидайте ответа.</b>')
            else:
                await message.reply(f'<b>Пользователь <a href="tg://user?id={to_add_id}">{to_add_name}</a> уже '
                                    f'предложил(а) вам начать отношения, чтобы согласиться, ответьте на его\её '
                                    f'сообщение командой "Чай согласиться".</b>')
    else:
        name = (await get_name_by_id(message, message.from_user.id))
        with db_ops() as cur:
            cur.execute(f'INSERT INTO relationships{str(message.chat.id)[1:]} (from_id, to_id, accepted) '
                        f'VALUES (?, ?, ?)', (message.from_user.id, to_add_id, False))
        await message.reply(f'<b><a href="tg://user?id={to_add_id}">{to_add_name}</a>! '
                            f'<a href="tg://user?id={message.from_user.id}">{name}</a> предложил(а) вам начать отношения! '
                            f'Чтобы согласиться, ответьте на его сообщение командой "Чай согласиться". '
                            f'Если же вы желаете отказаться, ответьте командой "Чай отказаться".</b>')


async def rel_stop(message: Message):
    to_stop_id, to_stop_name = (await reply_mention_handler(message))
    if not to_stop_id:
        await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
        return
    fetched = await _check_rel(message.from_user.id, to_stop_id, message.chat.id)
    if fetched:
        with db_ops() as cur:
            cur.execute(f'DELETE FROM relationships{str(message.chat.id)[1:]} WHERE id = ?', (fetched[0][0], ))
        if fetched[0][3]:
            await message.reply(f'<b>Вы расстались с <a href="tg://user?id={to_stop_id}">{to_stop_name}</a>.</b>')
        else:
            await message.reply(f'<b>Вы отказались от предложения отношений с '
                                f'<a href="tg://user?id={to_stop_id}">{to_stop_name}</a>.</b>')
    else:
        await message.reply(f'<b>Вы не состоите в отношениях с '
                            f'<a href="tg://user?id={to_stop_id}">{to_stop_name}</a>.</b>')


async def rel_agree(message: Message):
    to_agree_id, to_agree_name = (await reply_mention_handler(message))
    if not to_agree_id:
        await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
        return
    fetched = await _check_rel(message.from_user.id, to_agree_id, message.chat.id)
    if fetched:
        if fetched[0][3]:
            await message.reply(f'<b>Вы уже находитесь в отношениях с '
                                f'<a href="tg://user?id={to_agree_id}">{to_agree_name}</a>.</b>')
        else:
            if message.from_user.id == fetched[0][2]:
                with db_ops() as cur:
                    cur.execute(f'UPDATE relationships{str(message.chat.id)[1:]} SET accepted = ?, score = ?, '
                                f'start_date = ? WHERE from_id = ? and to_id = ?',
                                (True, 0, datetime.now(), to_agree_id, message.from_user.id))
                    await message.reply(f'<b>Вы вступили в отношения с '
                                        f'<a href="tg://user?id={to_agree_id}">{to_agree_name}</a>. Поздравляем!</b>')
            else:
                await message.reply('<b>Вы не можете согласиться на отношения, которые вы сами начали.</b>')
    else:
        await message.reply(f'<b>Не обнаружено предложений на отношения от пользователя '
                            f'<a href="tg://user?id={to_agree_id}">{to_agree_name}</a>.</b>')


async def rel_reject(message: Message):
    to_reject_id, to_reject_name = (await reply_mention_handler(message))
    if not to_reject_id:
        await message.reply(f'<b>Пользователь не обнаружен в чате.</b>')
        return
    fetched = await _check_rel(message.from_user.id, to_reject_id, message.chat.id)
    if fetched:
        if fetched[0][3]:
            await message.reply(f'<b>Вы уже находитесь в отношениях с '
                                f'<a href="tg://user?id={to_reject_id}">{to_reject_name}</a>. '
                                f'Если вы хотите расторгнуть отношения, используйте команду "чай расстаться".</b>')
        else:
            if message.from_user.id == fetched[0][2]:
                with db_ops() as cur:
                    cur.execute(f'DELETE FROM relationships{str(message.chat.id)[1:]} WHERE id = ?', (fetched[0][0], ))
                await message.reply(f'<b>Вы отказались от отношений с '
                                    f'<a href="tg://user?id={to_reject_id}">{to_reject_name}</a>.</b>')
            else:
                await message.reply('<b>Вы не можете отказаться от отношений, которые вы сами начали.</b>')
    else:
        await message.reply(f'<b>Не обнаружено предложений на отношения от пользователя '
                            f'<a href="tg://user?id={to_reject_id}">{to_reject_name}</a>.</b>')


async def rel_personal_status(message: Message):
    with db_ops() as cur:
        cur.execute(f'SELECT * FROM relationships{str(message.chat.id)[1:]} WHERE '
                    f'(from_id = ? and accepted = ?) or (to_id = ? and accepted = ?)',
                    (message.from_user.id, 1, message.from_user.id, 1))
        accepted = cur.fetchall()
        cur.execute(f'SELECT * FROM relationships{str(message.chat.id)[1:]} WHERE '
                    f'(from_id = ? and accepted = ?) or (to_id = ? and accepted = ?)',
                    (message.from_user.id, 0, message.from_user.id, 0))
        not_accepted = cur.fetchall()
    name = await get_name_by_id(message, message.from_user.id)
    text = f'<b>Отношения <a href="tg://user?id={message.from_user.id}">{name}</a>:</b>\n'
    text += (await _rel_status_text(message, accepted, not_accepted))
    await message.reply(text)


async def rel_total_status(message: Message):
    with db_ops() as cur:
        cur.execute(f'SELECT * FROM relationships{str(message.chat.id)[1:]} WHERE accepted = ?', (1, ))
        accepted = cur.fetchall()
        cur.execute(f'SELECT * FROM relationships{str(message.chat.id)[1:]} WHERE accepted = ?', (0, ))
        not_accepted = cur.fetchall()
    text = f'<b>Все отношения чата:</b>\n'
    text += (await _rel_status_text(message, accepted, not_accepted))
    await message.reply(text)


async def _rel_status_text(message: Message, accepted, not_accepted):
    text = ''
    if accepted:
        for relationship in accepted:
            time = datetime.strptime(relationship[6], '%Y-%m-%d %H:%M:%S.%f')
            name_first = await get_name_by_id(message, relationship[1])
            name_second = await get_name_by_id(message, relationship[2])
            text += (f'\t<a href="tg://user?id={relationship[1]}">{name_first}</a> и '
                     f'<a href="tg://user?id={relationship[2]}">{name_second}</a>. Очки: {relationship[4]}\n'
                     f'\t\tВстречаются с {time.strftime("%d/%m/%Y %H:%M:%S")}.\n')
    else:
        text += f'Активных отношений на данный момент нет.\n'
    if not_accepted:
        text += '\n<b>Запросы на отношения, ожидающие подтверждения или отказа:</b>\n'
        for relationship in not_accepted:
            name_first = await get_name_by_id(message, relationship[1])
            name_second = await get_name_by_id(message, relationship[2])
            text += (f'\t<a href="tg://user?id={relationship[1]}">{name_first}</a> и '
                     f'<a href="tg://user?id={relationship[2]}">{name_second}</a>.\n')
    return text


async def rel_gift(message: Message):
    to_gift_id, to_gift_name = (await reply_mention_handler(message))
    if not to_gift_id:
        with db_ops() as cur:
            cur.execute(f'SELECT * FROM relationships{str(message.chat.id)[1:]} WHERE from_id = ? or to_id = ?',
                        (message.from_user.id,message.from_user.id))
            fetched = cur.fetchall()
        if fetched:
            main_person = [None, None, None, None, -1, None, None]
            for relationship in fetched:
                if relationship[4] > main_person[4]:
                    main_person = relationship
            await _gift_to(message, main_person)
        else:
            await message.reply('<b>Вы не состоите ни в одних отношениях.</b>')
    else:
        fetched = await _check_rel(message.from_user.id, to_gift_id, message.chat.id)
        if fetched:
            await _gift_to(message, fetched[0])
        else:
            await message.reply(f'<b>Вы не состоите в отношениях с '
                                f'<a href="tg://user?id={to_gift_id}">{to_gift_name}</a>.</b>')


async def _gift_to(message: Message, person):
    if person[5]:
        last_action = datetime.strptime(person[5], '%Y-%m-%d %H:%M:%S.%f')
    else:
        last_action = None
    time = datetime.now()
    if not person[5] or time.timestamp() > (last_action + timedelta(hours=4)).timestamp():
        score = person[4]
        if score <= 100:
            lower_bound = 10
            upper_bound = 50
        else:
            lower_bound = int((0.5 / math.sqrt(math.log(score[-1], 2) + 5)) * score)
            upper_bound = int((1 / math.sqrt(math.log(score[-1], 2) + 5)) * score)
        to_add = randint(lower_bound, upper_bound)
        with db_ops() as cur:
            cur.execute(f'UPDATE relationships{str(message.chat.id)[1:]} SET score = ?, last_action = ? WHERE id = ?',
                        (score + to_add, time, person[0]))
        to_add_str = (await _get_score_str(to_add))
        total_score_str = (await _get_score_str(score + to_add))
        if message.from_user.id == person[1]:
            partner = person[2]
        else:
            partner = person[1]
        partner_name = (await get_name_by_id(message, partner))
        await message.reply(f'<b>Вы сделали подарок <a href="tg://user?id={partner}">{partner_name}</a>. '
                            f'Крепость ваших отношений усилилась на {to_add_str}. Текущий счёт ваших отношений - '
                            f'{total_score_str}.\nВы можете сделать следующий подарок через 4 часа.</b>')
    else:
        next_gift = last_action + timedelta(hours=4) - time
        hours, remainder = divmod(next_gift.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await message.reply(f'С момента прошлого подарка прошло недостаточно времени, вы сможете сделать следующий '
                            f'подарок через {hours} часов, {minutes} минут и {seconds} секунд')


async def _get_score_str(score):
    power = math.floor(math.log10(score))
    magnitude = power // 3
    if magnitude > 0:
        score_str = f'{round(score, -1 * power + 2) / 1000 ** magnitude}{["", "k", "M", "B", "T"][magnitude]}'
    else:
        score_str = str(score)
    return score_str
