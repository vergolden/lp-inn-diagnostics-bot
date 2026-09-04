"""Консольный тест модуля dadata_client — проверка перед сборкой VK-бота."""
import sys

import config
from dadata_client import DadataClient
from exceptions import DadataError
from risk_categories import DISCLAIMER, get_categories_for_okved


def print_company_card(inn: str, client: DadataClient) -> None:
    print(f"\n--- Запрос по ИНН {inn} ---")
    try:
        company = client.find_by_inn(inn)
    except DadataError as e:
        print(f"Ошибка: {e}")
        return

    print(f"Компания: {company['name_short']}")
    print(f"ИНН/КПП: {company['inn']} / {company['kpp']}")
    print(f"ОГРН: {company['ogrn']}")
    print(f"Статус: {company['status']}")
    print(f"ОКВЭД (осн.): {company['okved']}")
    print(f"Адрес: {company['address']}")

    print("\nКатегории для проверки по 152-ФЗ:")
    for item in get_categories_for_okved(company["okved"]):
        print(f"  • {item}")
    print(f"\n{DISCLAIMER}")


if __name__ == "__main__":
    if not config.DADATA_API_KEY:
        print("Не задан DADATA_API_KEY в .env")
        sys.exit(1)

    dadata = DadataClient(config.DADATA_API_KEY)

    inns = sys.argv[1:] or ["7707083893", "280105985496"]  # Сбербанк, ИП Бурдуковской (для теста)
    for inn in inns:
        print_company_card(inn, dadata)
