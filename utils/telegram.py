import os

import requests
from dotenv import load_dotenv

load_dotenv()

# Maximum message length allowed by Telegram API
MAX_MESSAGE_LENGTH = 4096


class TelegramError(Exception):
    """Exception raised for errors in Telegram API interactions."""

    pass


def send_telegram_message(message: str, protocol: str, disable_notification: bool = False) -> None:
    """
    Send a message to a Telegram chat using a bot.

    Args:
        message: The message to send
        protocol: Protocol identifier used to select bot token and chat ID
        disable_notification: If True, sends the message silently

    Raises:
        TelegramError: If the message fails to send
    """
    print(f"Sending telegram message:\n{message}")

    # Truncate long messages
    if len(message) > MAX_MESSAGE_LENGTH:
        message = message[: MAX_MESSAGE_LENGTH - 3] + "..."

    # Get bot token and chat ID from environment variables
    bot_token = os.getenv(f"TELEGRAM_BOT_TOKEN_{protocol.upper()}")
    if not bot_token:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN_DEFAULT")

    chat_id = os.getenv(f"TELEGRAM_CHAT_ID_{protocol.upper()}")

    if not bot_token or not chat_id:
        print(f"Warning: Missing Telegram credentials for {protocol}")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_notification": disable_notification,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise TelegramError(f"Failed to send telegram message: {e}")

    if response.status_code != 200:
        raise TelegramError(f"Failed to send telegram message: {response.status_code} - {response.text}")
