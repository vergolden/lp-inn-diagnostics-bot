"""Точка входа: запуск VK-бота «Экспресс-диагностика по ИНН»."""
import asyncio

import config
from vk_bot import bot


def main() -> None:
    if not config.VK_BOT_TOKEN:
        raise SystemExit("Не задан VK_BOT_TOKEN в .env")
    if not config.DADATA_API_KEY:
        raise SystemExit("Не задан DADATA_API_KEY в .env")
    asyncio.run(bot.run_polling())


if __name__ == "__main__":
    main()
