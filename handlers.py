from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, ChatMemberUpdatedFilter, KICKED, LEFT, RESTRICTED, MEMBER, ADMINISTRATOR, CREATOR

from filters import ChatTypeFilter, ActionsFilter, ACTIONS, BotCommandsFilter, PingFilter
from get_users_from_chat import get_chat_members
from db_utils import db_ops
import commands

router = Router()
router.message.filter(
    ChatTypeFilter(chat_type=["group", "supergroup"])
)


@router.message(Command('start', 'старт'))
async def start_handler(message: Message):
    await get_chat_members(message.chat.id)
    await message.reply('Бот успешно добавлен в чат!')


@router.message(Command('help', 'h', 'помощь'))
async def command_list(message: Message):
    await message.answer('')  # TODO


@router.message(PingFilter())
async def ping_handler(message: Message):
    await message.reply('Понг')


@router.message(F.text, ActionsFilter())
async def actions_handling(message: Message):
    for action in ACTIONS:
        if action[0] in message.text.lower():
            sender_name = (await commands.get_name_by_id(message, message.from_user.id))
            receiver_id, receiver_name = (await commands.reply_mention_handler(message))
            if receiver_name:
                await message.reply(f'<a href="tg://user?id={message.from_user.id}">{sender_name}</a> {action[1]} '
                                    f'<a href="tg://user?id={receiver_id}">{receiver_name}</a>')
                return


@router.message(F.text, BotCommandsFilter())
async def commands_handling(message: Message):
    if message.text.lower().startswith('чай ник'):
        await commands.set_nickname(message)
    elif message.text.lower().startswith('чай мой ник'):
        await commands.check_nickname(message)
    elif message.text.lower().startswith('чай бан'):
        await commands.ban(message)
    elif message.text.lower().startswith('чай разбан') or message.text.lower().startswith('чай анбан'):
        await commands.unban(message)
    elif message.text.lower().startswith('чай мут'):
        await commands.mute(message)
    elif message.text.lower().startswith('чай анмут') or message.text.lower().startswith('чай размут'):
        await commands.unmute(message)
    elif message.text.lower().startswith('чай админы'):
        await commands.admins(message)
    elif message.text.lower().startswith('чай +адм'):
        await commands.promote_admin(message)
    elif message.text.lower().startswith('чай -адм'):
        await commands.demote_admin(message)
    elif message.text.lower().startswith('чай +отн'):
        await commands.rel_start(message)
    elif message.text.lower().startswith('чай расстаться'):
        await commands.rel_stop(message)
    elif message.text.lower().startswith('чай согласиться'):
        await commands.rel_agree(message)
    elif message.text.lower().startswith('чай отказаться'):
        await commands.rel_reject(message)
    elif message.text.lower().startswith('чай мои отношения'):
        await commands.rel_personal_status(message)
    elif message.text.lower().startswith('чай все отношения'):
        await commands.rel_total_status(message)
    elif message.text.lower().startswith('чай подарок'):
        await commands.rel_gift(message)
    elif message.text.lower().startswith('чай команды'):
        await command_list(message)


@router.message(F.new_chat_members)
async def somebody_added(message: Message):
    with db_ops() as cur:
        for user in message.new_chat_members:
            cur.execute(f'INSERT OR IGNORE INTO chat{str(message.chat.id)[1:]} (username, user_id, is_admin, real_name)'
                        f' values (?, ?, ?, ?)',
                        (user.username, user.id, False, user.first_name + ' ' + user.last_name
                            if user.last_name is not None else user.first_name))


@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) >> (ADMINISTRATOR | CREATOR)))
async def admin_promoted_reaction(event: ChatMemberUpdated):
    with db_ops() as cur:
        cur.execute(f'UPDATE chat{str(event.chat.id)[1:]} SET is_admin = ? WHERE user_id = ?',
                    (True, event.new_chat_member.user.id))
    name = (await commands.get_name_by_id(event, event.new_chat_member.user.id))
    await event.answer(f'<a href="tg://user?id={event.new_chat_member.user.id}">{name}</a> '
                       f'был(а) повышен(а) до Администратора')


@router.chat_member(ChatMemberUpdatedFilter(
    member_status_changed=(KICKED | LEFT | RESTRICTED | MEMBER) << (ADMINISTRATOR | CREATOR)))
async def admin_demoted_reaction(event: ChatMemberUpdated):
    with db_ops() as cur:
        cur.execute(f'UPDATE chat{str(event.chat.id)[1:]} SET is_admin = ? WHERE user_id = ?',
                    (False, event.new_chat_member.user.id))
    name = (await commands.get_name_by_id(event, event.new_chat_member.user.id))
    await event.answer(f'<a href="tg://user?id={event.new_chat_member.user.id}">{name}</a> '
                       f'был(а) снят(а) с должности Администратора')
