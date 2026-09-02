import os

from asgiref.sync import async_to_sync
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession


async def _check_chat_membership(
    bot_token,
    bot_proxy,
    chat_id,
    user_id,
):
    if not bot_token or not chat_id or not user_id:
        return {
            "is_member": False,
            "status": None,
            "error": "missing_configuration",
        }

    session = AiohttpSession(
        proxy=bot_proxy,
    )

    bot = Bot(
        token=bot_token,
        session=session,
    )

    try:
        member = await bot.get_chat_member(
            chat_id=int(chat_id),
            user_id=int(user_id),
        )

        status = member.status


        if hasattr(status, "value"):
            status = status.value

        if status in (
            "creator",
            "administrator",
            "member",
        ):
            return {
                "is_member": True,
                "status": status,
                "error": None,
            }

        if status == "restricted":
            return {
                "is_member": bool(
                    getattr(
                        member,
                        "is_member",
                        False,
                    )
                ),
                "status": status,
                "error": None,
            }

        return {
            "is_member": False,
            "status": status,
            "error": None,
        }

    except Exception as error:
        return {
            "is_member": False,
            "status": None,
            "error": str(error),
        }

    finally:
        await bot.session.close()


def check_chat_membership(
    bot_token,
    bot_proxy,
    chat_id,
    user_id,
):
    return async_to_sync(
        _check_chat_membership
    )(
        bot_token,
        bot_proxy,
        chat_id,
        user_id,
    )