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
FEEDBACK_URL = "https://runwithlove.site/feedback"
DONATE_URL = "https://runwithlove.site/donate"


session = AiohttpSession(

    proxy=BOT_PROXY,

)

bot = Bot(

    token=BOT_TOKEN,

    session=session,

)
dp = Dispatcher()

feedback_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💬 Открыть форму обратной связи",
                url=FEEDBACK_URL,
            )
        ]
    ]
)


donate_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❤️ Поддержать проект",
                url=DONATE_URL,
            )
        ]
    ]
)


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




@dp.message(Command("rules"))
async def rules_handler(message: Message):
    await message.answer(
        "📌 Правила нашего чата\n\n"
        "Мы здесь, чтобы общаться, бегать и делать добрые дела вместе. "
        "Чтобы в чате всем было комфортно, договоримся о нескольких простых правилах.\n\n"

        "1. Взаимоуважение — самое важное\n\n"
        "• Без личных оскорблений, унижения, грубости, троллинга и провокаций на конфликт.\n"
        "• Не устраиваем политические, религиозные и национальные споры.\n"
        "• Критикуем идеи и поступки, а не людей — и только конструктивно.\n\n"

        "2. Не используем жалобы Telegram для решения конфликтов\n\n"
        "Не жалуйтесь на сообщения участников через встроенную функцию Telegram — "
        "это может привести к ограничениям или блокировке человека со стороны платформы.\n\n"

        "3. Если возник конфликт — пишите администрации\n\n"
        "Если вам кажется, что кто-то нарушает правила или ситуация требует вмешательства, "
        "напишите администратору в личные сообщения.\n"
        "Разбор конфликтов в общем чате не устраиваем.\n\n"

        "4. Реклама — только по согласованию с администрацией\n\n"
        "Рекламные публикации без предварительного согласования запрещены.\n\n"

        "⚠️ За нарушение правил администрация может ограничить участие в чате "
        "или заблокировать пользователя.\n\n"

        "❤️ И главное: относитесь к другим так, как хотите, чтобы относились к вам.\n\n"

        "Давайте вместе беречь атмосферу Run With Love. "
        "Мы всё-таки здесь, чтобы помогать другим. 🐾"
    )


@dp.message(Command("feedback"))
async def feedback_handler(message: Message):
    await message.answer(
        "💬 Обратная связь\n\n"
        "Нашли ошибку, есть идея или хотите предложить улучшение?\n\n"
        "Расскажите об этом через форму обратной связи ❤️",
        reply_markup=feedback_keyboard,
    )



@dp.message(Command("donate"))
async def donate_handler(message: Message):
    await message.answer(
        "❤️ Поддержать Бегалендарь\n\n"
        "Бегалендарь — некоммерческий проект, который развивается для сообщества Run With Love.\n\n"
        "Если проект оказался полезным и вам хочется поддержать его развитие — это можно сделать по кнопке ниже.\n\n"
        "Спасибо ❤️",
        reply_markup=donate_keyboard,
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