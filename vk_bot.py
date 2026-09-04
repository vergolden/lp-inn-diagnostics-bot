"""
VK-бот «Экспресс-диагностика по ИНН» для сообщества Legal Privacy.

Работает через LongPoll (vkbottle сам подключается к VK и опрашивает события —
отдельный сервер не нужен). Вся бизнес-логика (запрос в dadata, подбор категорий,
отправка лида) вынесена в отдельные модули — здесь только диалог с пользователем.
"""
from vkbottle import Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Bot, Message

import config
from dadata_client import DadataClient
from exceptions import DadataError
from lead_notifier import send_lead
from risk_categories import DISCLAIMER, STATUS_LABELS, get_categories_for_okved, is_active

bot = Bot(token=config.VK_BOT_TOKEN)
dadata = DadataClient(config.DADATA_API_KEY)

BTN_CHECK = "Проверить компанию"
BTN_ABOUT = "О сервисе"
BTN_CONSULT = "Записаться на консультацию"

# Простое состояние диалога в памяти процесса: user_id -> {"step": ..., "company": {...}}
# Для одного бота на один процесс этого достаточно, база данных не нужна.
sessions: dict[int, dict] = {}

main_keyboard = (
    Keyboard(one_time=False)
    .add(Text(BTN_CHECK), color=KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text(BTN_ABOUT), color=KeyboardButtonColor.SECONDARY)
    .row()
    .add(Text(BTN_CONSULT), color=KeyboardButtonColor.POSITIVE)
)

ABOUT_TEXT = (
    "Legal Privacy — консалтинг по защите персональных данных (152-ФЗ) "
    "для самозанятых, малого и среднего бизнеса.\n\n"
    "Подробнее: legal-privacy.ru"
)

WELCOME_TEXT = (
    "Привет! Это бот-диагностика Legal Privacy.\n\n"
    "Пришлю по ИНН вашей компании список тем, которые стоит проверить "
    "по 152-ФЗ (защита персональных данных).\n\n"
    f"{DISCLAIMER}"
)


def format_company_reply(company: dict) -> str:
    status = company["status"]
    status_label = STATUS_LABELS.get(status, status or "неизвестен")

    lines = [
        f"Компания: {company['name_short']}",
        f"ОКВЭД (осн.): {company['okved']}",
        f"Статус: {status_label}",
        "",
    ]

    if not is_active(status):
        lines.append(
            "Компания не действует, поэтому требования 152-ФЗ к ней сейчас не применяются. "
            f"Если хотите проверить другую компанию — нажмите «{BTN_CHECK}»."
        )
        return "\n".join(lines)

    lines.append("Категории для проверки по 152-ФЗ:")
    for item in get_categories_for_okved(company["okved"]):
        lines.append(f"• {item}")
    lines.append("")
    lines.append(DISCLAIMER)
    lines.append("")
    lines.append(f'Хотите разбор от эксперта — нажмите «{BTN_CONSULT}».')
    return "\n".join(lines)


@bot.on.message(text=["Начать", "начать", "/start", "Start"])
async def start_handler(message: Message):
    sessions[message.from_id] = {"step": "idle"}
    await message.answer(WELCOME_TEXT, keyboard=main_keyboard)


@bot.on.message(text=BTN_ABOUT)
async def about_handler(message: Message):
    await message.answer(ABOUT_TEXT, keyboard=main_keyboard)


@bot.on.message(text=BTN_CHECK)
async def check_handler(message: Message):
    sessions[message.from_id] = {"step": "waiting_inn"}
    await message.answer(
        "Пришлите ИНН компании или ИП (10 или 12 цифр).",
        keyboard=main_keyboard,
    )


@bot.on.message(text=BTN_CONSULT)
async def consult_handler(message: Message):
    session = sessions.get(message.from_id, {})
    session["step"] = "waiting_contact"
    sessions[message.from_id] = session
    await message.answer(
        "Оставьте телефон или e-mail для связи — мы свяжемся и обсудим детали.",
        keyboard=main_keyboard,
    )


@bot.on.message()
async def fallback_handler(message: Message):
    """Ловит всё остальное: ввод ИНН и ввод контакта в зависимости от состояния диалога."""
    session = sessions.get(message.from_id, {"step": "idle"})
    step = session.get("step")

    if step == "waiting_inn":
        try:
            company = dadata.find_by_inn(message.text)
        except DadataError as e:
            await message.answer(f"Не получилось: {e}\nПопробуйте ещё раз.")
            return
        session["company"] = company
        session["step"] = "idle"
        await message.answer(format_company_reply(company), keyboard=main_keyboard)
        return

    if step == "waiting_contact":
        company = session.get("company", {})
        send_lead(
            token=config.TELEGRAM_BOT_TOKEN,
            chat_ids=[config.TELEGRAM_CHAT_ID_ANDREW, config.TELEGRAM_CHAT_ID_WIFE],
            vk_user_id=message.from_id,
            company=company,
            contact=message.text,
        )
        session["step"] = "idle"
        await message.answer(
            "Спасибо! Заявка передана, мы свяжемся с вами в ближайшее время.",
            keyboard=main_keyboard,
        )
        return

    # Состояние по умолчанию — просто показываем меню
    await message.answer("Выберите действие на клавиатуре ниже.", keyboard=main_keyboard)
