"""Отправка лида (заявки на консультацию) в Telegram — Андрею и Татьяне."""
from datetime import datetime

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_lead(token: str, chat_ids: list[str], vk_user_id: int, company: dict, contact: str) -> None:
    """Отправляет карточку лида в один или несколько Telegram-чатов."""
    text = (
        "🔔 Новая заявка из VK-бота «Диагностика по ИНН»\n\n"
        f"Компания: {company.get('name_short')}\n"
        f"ИНН: {company.get('inn')}\n"
        f"ОКВЭД: {company.get('okved')}\n"
        f"VK ID пользователя: {vk_user_id}\n"
        f"Контакт: {contact}\n"
        f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    for chat_id in chat_ids:
        if not chat_id:
            continue
        requests.post(
            TELEGRAM_API.format(token=token),
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
