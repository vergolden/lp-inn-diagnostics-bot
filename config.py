"""Загрузка конфигурации из .env."""
import os

from dotenv import load_dotenv

load_dotenv()

DADATA_API_KEY = os.getenv("DADATA_API_KEY")
VK_BOT_TOKEN = os.getenv("VK_BOT_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID_ANDREW = os.getenv("TELEGRAM_CHAT_ID_ANDREW")
TELEGRAM_CHAT_ID_WIFE = os.getenv("TELEGRAM_CHAT_ID_WIFE")
