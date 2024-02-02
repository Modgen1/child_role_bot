from pyrogram import Client
from config_reader import config
from db_utils import db_init, db_ops

api_id = config.api_id.get_secret_value()
api_hash = config.api_hash.get_secret_value()
bot_token = config.bot_token.get_secret_value()


async def get_chat_members(chat_id):
    db_init(chat_id)
    app = Client("Имя | Бот", api_id=api_id, api_hash=api_hash, bot_token=bot_token, in_memory=True)
    await app.start()
    with db_ops() as cur:
        async for member in app.get_chat_members(chat_id):
            cur.execute(f'''
            INSERT INTO chat{str(chat_id)[1:]} (username, user_id, real_name) VALUES (?, ?, ?)''',
                        (member.user.username, member.user.id, (member.user.first_name + ' ' + member.user.last_name) if member.user.last_name is not None else member.user.first_name))
    await app.stop()
