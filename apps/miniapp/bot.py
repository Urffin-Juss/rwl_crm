import asyncio
import logging
import os
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)



BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MINI_APP_URL = os.getenv('MINI_APP_URL')
BOT_PROXY = os.getenv('BOT_PROXY')

session = AiohttpSession(

    proxy=BOT_PROXY,

)

bot = Bot(

    token=BOT_TOKEN,

    session=session,

)
dp = Dispatcher()




@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="🏃 Открыть календарь",

                    url="https://t.me/TestForChatEasyBot?startapp"

                )

            ]

        ]

    )

    await message.answer(
        'Календарь стартов Run With Love',
        reply_markup=keyboard,
    )


async def main():
    logging.basicConfig(level=logging.INFO)

    logging.info('Starting Telegram bot')

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())