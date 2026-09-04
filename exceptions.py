"""Исключения модуля работы с dadata.ru."""


class DadataError(Exception):
    """Базовая ошибка при обращении к API dadata."""


class CompanyNotFoundError(DadataError):
    """По переданному ИНН ничего не найдено."""


class InvalidInnError(DadataError):
    """ИНН не проходит базовую проверку формата (10 или 12 цифр)."""
