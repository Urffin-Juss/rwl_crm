import hashlib
import hmac
import json
from urllib.parse import parse_qsl

def validate_telegram_init_data(init_data: str, bot_token: str):


    parsed_data = dict(parse_qsl(init_data))
    received_hash = parsed_data.pop("hash", None)

    if not received_hash:
        return None


    data_check_string = '\n'.join(
        f"{key}={value}"
        for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
            calculated_hash,
            received_hash
    ):
        return None

    user_raw = parsed_data.get("user")

    if not user_raw:
        return None


    return json.loads(user_raw)