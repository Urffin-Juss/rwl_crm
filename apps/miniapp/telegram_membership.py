import json
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def check_chet_membership(bot_token, chat_id, user_id):

    if not bot_token or not chat_id or not user_id:
        return {
            "is_member": False,
            "status": None,
            "error": "missing_configuration",
        }

    query = urlencode({
        "chat_id": chat_id,
        "user_id": user_id,
    })

    url = (
        f"https://api.telegram.org/"
        f"bot{bot_token}/getChatMembers?"
        f"{query}"
    )
    try:
        with urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))


    except (HTTPError, URLError, TimeoutError) as error:
        return {
            "is_member": False,
            "status": None,
            "error": str(error),
        }

    if not data.get("ok"):
        return {
            "is_member": False,
            "status": None,
            "error": data.get("description"),
        }

    member = data["result"]
    status = member.get("status")

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
            "is_member": member.get("is_member", False),
            "status": status,
            "error": None,

        }

    return {
        "is_member": False,
        "status": status,
        "error": None
    }