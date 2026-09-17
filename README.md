# VK-бот «Экспресс-диагностика по ИНН»

Бот ВКонтакте для сообщества [Legal Privacy](https://legal-privacy.ru) — консалтинга по защите
персональных данных (152-ФЗ) для самозанятых и малого/среднего бизнеса.

Пользователь присылает боту ИНН своей компании. Бот получает данные о компании через
[dadata.ru](https://dadata.ru/api/) (название, ОГРН, статус, ОКВЭД) и возвращает список общих
категорий 152-ФЗ, которые стоит проверить именно этой сфере деятельности — не юридическое
заключение, а повод для разговора с DPO-экспертом. Заявки на консультацию улетают в Telegram.

## Функции / команды бота

- **«Проверить компанию»** — запрос ИНН → карточка компании + чек-лист категорий по 152-ФЗ,
  подобранный по коду ОКВЭД (для ликвидированных/банкротных компаний — короткий ответ без
  чек-листа, требования 152-ФЗ к ним не применяются)
- **«О сервисе»** — короткая информация о Legal Privacy
- **«Записаться на консультацию»** — сбор контакта, заявка уходит в Telegram

## Архитектура

Модуль работы с API вынесен отдельно от логики диалога бота:

```
config.py           — загрузка .env
dadata_client.py     — клиент dadata.ru (поиск компании по ИНН)
exceptions.py        — исключения модуля dadata
risk_categories.py   — категории 152-ФЗ по ОКВЭД, без юридических оценок
lead_notifier.py      — отправка заявки в Telegram
vk_bot.py            — диалог бота (vkbottle, LongPoll)
cli.py               — консольный тест dadata-модуля
main.py              — точка входа
```

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# впишите DADATA_API_KEY, VK_BOT_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID_*

python cli.py            # тест модуля dadata в консоли
python main.py            # запуск бота (LongPoll)
```

## Настройка VK-сообщества

1. Управление → Сообщения → включить
2. Управление → Настройки для бота → включить «Возможности ботов» + кнопку «Начать»
3. Управление → Работа с API → Long Poll API → включить, во вкладке «Типы событий» отметить
   «Входящее сообщение»
4. Управление → Работа с API → Ключи доступа → создать ключ с правами **«Управление
   сообществом»** и **«Сообщения сообщества»** (оба нужны: `groups.getLongPollServer`
   требует право на управление, а не только на сообщения)

## Стек

Python 3.12, [vkbottle](https://github.com/vkbottle/vkbottle), requests, python-dotenv,
[dadata.ru API](https://dadata.ru/api/find-party/).

## Деплой на VPS (Docker + Coolify)

Бот упакован в `Dockerfile` (Python 3.12-slim, зависимости из `requirements.txt`, точка входа —
`python main.py`). Процесс не поднимает HTTP-сервер (работает через VK LongPoll), поэтому в
Coolify для приложения отключён Healthcheck — стандартная HTTP-проверка здесь не применима.

**Разворачивание с нуля:**

1. Арендовать VPS (Ubuntu 24.04), установить Docker (`curl -fsSL https://get.docker.com | sh`)
   и Coolify (`curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash`)
2. В Coolify: **Keys & Tokens → Private Keys** — сгенерировать SSH-ключ (ED25519), добавить его
   публичную часть в GitHub-репозиторий → **Settings → Deploy keys** (с правом записи)
3. Создать ресурс **Private Git Repository (with Deploy Key)**: URL репозитория, ветка `main`,
   Build pack — **Dockerfile**
4. Добавить переменные окружения (**Environment Variables**, Runtime): `DADATA_API_KEY`,
   `VK_BOT_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_ANDREW`, `TELEGRAM_CHAT_ID_WIFE`
5. Отключить **Healthcheck** (по умолчанию выключен — не включать)
6. **Deploy**

**Автодеплой:** в Coolify (**Advanced → Git → Manual Git webhooks → GitHub**) скопировать
Webhook URL и Webhook secret, добавить их в GitHub-репозиторий → **Settings → Webhooks → Add
webhook** (Content type: `application/json`, событие: `push`). После этого каждый `git push` в
`main` запускает пересборку и передеплой автоматически.

**Восстановление после сбоя/переустановки:** повторить шаги 1–6 на новом сервере — состояние
бота не хранится (сессии диалогов — в памяти процесса, лиды дублируются в `leads.jsonl` внутри
контейнера и в Telegram, самостоятельной БД нет).
