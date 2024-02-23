from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

ACTIONS = [('обнять', 'обнял(а)'), ('поцеловать', 'поцеловал(а)'), ('кусь', 'кусьнул(а)'), ('буп', 'сделал(а) буп'),
           ('бупнуть', 'сделал(а) буп'), ('пожать руку', 'пожал(а) руку'), ('кусьнуть', 'кусьнул(а)'),
           ('укусить', 'укусил(а)'), ('лизнуть', 'лизнул(а)'), ('убить', 'убил(а)'), ('сжечь', 'сжёг'),
           ('ударить', 'ударил(а)'), ('уебать', 'уебал(а)'), ('трахнуть', 'трахнул(а)'), ('выебать', 'выебал(а)'),
           ('изнасиловать', 'изнасиловал(а)'), ('погладить', 'погладил(а)'), ('шлёпнуть', 'шлёпнул(а)'),
           ('расстрелять', 'расстрелял(а)'), ('кастрировать', 'кастрировал(а)'), ('облапать', 'облапал(а)'),
           ('потрогать', 'потрогал(а)'), ('пнуть', 'пнул(а)'), ('похвалить', 'похвалил(а)'), ('лизь', 'лизнул(а)'),
           ('поздравить', 'поздравил(а)'), ('послать нахуй', 'послал(а) нахуй'), ('понюхать', 'понюхал(а)'),
           ('нюх', 'понюхал(а)'), ('ущипнуть', 'ущипнул(а)'), ('покормить', 'покормил(а)'), ('отравить', 'отравил(а)'),
           ('пригласить на чай', 'приглашает на чай'), ('записать на ноготочки', 'записал(а) на ноготочки')]


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
            if message.text and message.text.lower().startswith(action[0]):
                return True
        return False


class BotCommandsFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text and message.text.lower().startswith('чай'):
            return True
        else:
            return False


class PingFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.text and message.text.lower() == 'пинг':
            return True
        else:
            return False
