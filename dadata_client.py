"""
Клиент для получения данных о компании по ИНН через API dadata.ru.

Используется метод "Стандартизация: подсказки по организациям" (findById/party),
документация: https://dadata.ru/api/find-party/
"""
import re

import requests

from exceptions import CompanyNotFoundError, DadataError, InvalidInnError

FIND_PARTY_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party"
INN_PATTERN = re.compile(r"^\d{10}$|^\d{12}$")


class DadataClient:
    """Обёртка над API dadata.ru для поиска организации по ИНН."""

    def __init__(self, api_key: str):
        if not api_key:
            raise DadataError("Не задан DADATA_API_KEY")
        self._api_key = api_key

    def find_by_inn(self, inn: str) -> dict:
        """
        Возвращает нормализованную информацию о компании по ИНН.

        :raises InvalidInnError: если строка не похожа на ИНН (10 или 12 цифр)
        :raises CompanyNotFoundError: если по ИНН ничего не найдено
        :raises DadataError: при ошибке запроса к API
        """
        inn = inn.strip()
        if not INN_PATTERN.match(inn):
            raise InvalidInnError(f"'{inn}' не похоже на ИНН (нужно 10 или 12 цифр)")

        response = requests.post(
            FIND_PARTY_URL,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Token {self._api_key}",
            },
            json={"query": inn},
            timeout=10,
        )

        if response.status_code != 200:
            raise DadataError(
                f"dadata вернула ошибку {response.status_code}: {response.text[:200]}"
            )

        suggestions = response.json().get("suggestions", [])
        if not suggestions:
            raise CompanyNotFoundError(f"По ИНН {inn} компания не найдена")

        return self._normalize(suggestions[0])

    @staticmethod
    def _normalize(suggestion: dict) -> dict:
        data = suggestion.get("data", {})
        name = data.get("name") or {}
        state = data.get("state") or {}
        management = data.get("management") or {}
        okved = data.get("okved")

        return {
            "inn": data.get("inn"),
            "kpp": data.get("kpp"),
            "ogrn": data.get("ogrn"),
            "name_full": name.get("full_with_opf") or suggestion.get("value"),
            "name_short": name.get("short_with_opf") or suggestion.get("value"),
            "status": state.get("status"),  # ACTIVE / LIQUIDATING / LIQUIDATED / BANKRUPT
            "registration_date": state.get("registration_date"),
            "okved": okved,
            "management_name": management.get("name"),
            "management_post": management.get("post"),
            "address": (data.get("address") or {}).get("value"),
        }
