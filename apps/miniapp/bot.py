import asyncio
import logging
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from asgiref.sync import sync_to_async
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandStart

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,

)

from apps.users.models import ClubMember

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

                    url="https://t.me/rwlminiappbot?startapp",

                )

            ]

        ]

    )



    await message.answer(
        'Календарь стартов Run With Love',
        reply_markup=keyboard,
    )





@dp.message(Command("delete_my_data"))
async def delete_my_data_handler(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Удалить мои данные",
                    callback_data="confirm_delete_my_data",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="cancel_delete_my_data",
                )
            ],
        ]
    )

    await message.answer(
        "Будут удалены данные вашего профиля, "
        "отметки участия в забегах и сохранённые согласия.\n\n"
        "Это действие нельзя отменить.",
        reply_markup=keyboard,
    )

@dp.callback_query(lambda callback: callback.data == "confirm_delete_my_data")
async def confirm_delete_my_data_handler(callback: CallbackQuery):
    telegram_id = callback.from_user.id

    deleted_count, _ = await sync_to_async(
        ClubMember.objects.filter(
            telegram_id=telegram_id
        ).delete
    )()

    if deleted_count:
        text = "Ваши данные удалены."
    else:
        text = "Сохранённых данных для удаления не найдено."

    await callback.message.edit_text(text)
    await callback.answer()



@dp.callback_query(lambda callback: callback.data == "cancel_delete_my_data")
async def cancel_delete_my_data_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Удаление данных отменено."
    )
    await callback.answer()


async def main():
    logging.basicConfig(level=logging.INFO)

    logging.info('Starting Telegram bot')

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())