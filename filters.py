from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

ACTIONS = [('обнять', 'обнял(а)'), ('поцеловать', 'поцеловал(а)'), ('кусь', 'кусьнул(а)')]


class ChatTypeFilter(BaseFilter):
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type


class ActionsFilter(BaseFilter):
    def __init__(self):
        self.actions = ACTIONS

    async def __call__(self, message: Message) -> bool:
        for action in self.actions:
            if action[0] in message.text.lower():
                return True
            else:
                return False


class BotCommandsFilter(BaseFilter):
    def __init__(self):
        pass

    async def __call__(self, message: Message) -> bool:
        if message.text.lower().startswith('чай'):
            return True
        else:
            return False


class PingFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text.lower() == 'пинг' or message.text.lower() == 'Пинг':
            return True
        else:
            return False
