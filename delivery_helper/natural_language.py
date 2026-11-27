"""Разбор распространённых текстовых запросов о доставке без AI."""

from dataclasses import dataclass
import re

from .calculator import DISTANCES_KM, TARIFFS


@dataclass(frozen=True)
class DeliveryRequest:
    """Данные, извлечённые из запроса пользователя."""

    city: str
    weight_kg: float
    tariff: str = "эконом"


_WEIGHT_PATTERN = re.compile(
    r"(?P<weight>\d+(?:[.,]\d+)?)\s*(?:кг|килограмм(?:а|ов)?)\b",
    re.IGNORECASE,
)

_CITY_ALIASES = {
    "ростов": "Ростов-на-Дону",
    "таганрог": "Таганрог",
    "краснодар": "Краснодар",
    "волгоград": "Волгоград",
    "воронеж": "Воронеж",
    "ставрополь": "Ставрополь",
    "сочи": "Сочи",
    "москва": "Москва",
    "москву": "Москва",
    "москвы": "Москва",
    "казань": "Казань",
    "казани": "Казань",
    "санкт-петербург": "Санкт-Петербург",
    "санкт петербург": "Санкт-Петербург",
    "екатеринбург": "Екатеринбург",
    "новосибирск": "Новосибирск",
}


def _normalize(text: str) -> str:
    """Приводит запрос к форме, удобной для поиска слов."""
    return " ".join(text.lower().replace("ё", "е").split())


def _find_city(text: str) -> str | None:
    normalized = _normalize(text)
    aliases = sorted(_CITY_ALIASES, key=len, reverse=True)
    for alias in aliases:
        if re.search(rf"(?<![а-я-]){re.escape(alias)}(?![а-я-])", normalized):
            return _CITY_ALIASES[alias]
    return None


def parse_delivery_request(text: str) -> DeliveryRequest | None:
    """Извлекает город, вес и тариф из распространённой фразы.

    Возвращает ``None``, если сообщение не содержит полного запроса.
    Проверка допустимого веса и окончательный расчёт выполняются калькулятором.
    """
    normalized = _normalize(text)
    weight_matches = list(_WEIGHT_PATTERN.finditer(normalized))
    if len(weight_matches) != 1:
        return None

    city = _find_city(normalized)
    if city is None or city == "Ростов-на-Дону":
        return None

    weight_text = weight_matches[0].group("weight").replace(",", ".")
    weight_kg = float(weight_text)
    tariff = next(
        (name for name in TARIFFS if re.search(rf"\b{re.escape(name)}\b", normalized)),
        "эконом",
    )
    return DeliveryRequest(city=city, weight_kg=weight_kg, tariff=tariff)
