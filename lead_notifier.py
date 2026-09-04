"""
Отправка лида (заявки на консультацию) в Telegram — Андрею и Татьяне.

Telegram API периодически недоступен напрямую из РФ (блокировка на уровне
провайдера/ТСПУ, см. docs/стек_и_сервисы.md) — отправка может подвиснуть или
упасть с сетевой ошибкой. Поэтому лид сначала пишется в локальный файл
(leads.jsonl) — это подстраховка, чтобы заявка не терялась даже если Telegram
в моменте недоступен, — и только потом бот пытается отправить уведомление.
"""
import json
from datetime import datetime
from pathlib import Path

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
LEADS_LOG = Path(__file__).parent / "leads.jsonl"
REQUEST_TIMEOUT = 30
RETRIES = 2


def _append_to_local_log(record: dict) -> None:
    with LEADS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _send_to_chat(token: str, chat_id: str, text: str) -> bool:
    for attempt in range(1, RETRIES + 1):
        try:
            response = requests.post(
                TELEGRAM_API.format(token=token),
                json={"chat_id": chat_id, "text": text},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
    return False


def send_lead(
    token: str,
    chat_ids: list[str],
    vk_user_id: int,
    company: dict,
    contact: str,
    consent_acknowledged: bool = False,
) -> bool:
    """
    Сохраняет лид локально и пытается отправить его в Telegram-чаты.

    consent_acknowledged фиксирует в записи, что перед отправкой пользователю
    показывался текст согласия на обработку ПД и политики конфиденциальности
    (см. CONSENT_TEXT в vk_bot.py) — это доказательство для аудита, что
    трансграничная передача через Telegram произошла после согласия.

    Возвращает True, если хотя бы одно уведомление в Telegram ушло успешно.
    Ничего не выбрасывает наружу — сетевые проблемы с Telegram не должны
    ронять диалог с пользователем в VK, лид в любом случае сохранён локально.
    """
    now = datetime.now()
    record = {
        "time": now.strftime("%d.%m.%Y %H:%M:%S"),
        "company": company.get("name_short"),
        "inn": company.get("inn"),
        "okved": company.get("okved"),
        "vk_user_id": vk_user_id,
        "contact": contact,
        "consent_acknowledged": consent_acknowledged,
    }
    _append_to_local_log(record)

    text = (
        "🔔 Новая заявка из VK-бота «Диагностика по ИНН»\n\n"
        f"Компания: {company.get('name_short')}\n"
        f"ИНН: {company.get('inn')}\n"
        f"ОКВЭД: {company.get('okved')}\n"
        f"VK ID пользователя: {vk_user_id}\n"
        f"Контакт: {contact}\n"
        f"Время: {now.strftime('%d.%m.%Y %H:%M')}"
    )

    delivered = False
    for chat_id in chat_ids:
        if not chat_id:
            continue
        if _send_to_chat(token, chat_id, text):
            delivered = True

    return delivered
