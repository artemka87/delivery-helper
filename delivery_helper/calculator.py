"""Расчёт стоимости и сроков доставки посылки из Ростова-на-Дону."""

import math

# Расстояние от Ростова-на-Дону до города, км (примерные данные по дорогам)
DISTANCES_KM = {
    "Ростов-на-Дону": 0,
    "Таганрог": 70,
    "Краснодар": 280,
    "Волгоград": 470,
    "Воронеж": 570,
    "Ставрополь": 490,
    "Сочи": 570,
    "Москва": 1070,
    "Казань": 1340,
    "Санкт-Петербург": 1780,
    "Екатеринбург": 2150,
    "Новосибирск": 3600,
}

BASE_PRICE = 200          # базовая стоимость отправки, руб.
PRICE_PER_KG = 40         # за каждый килограмм веса, руб.
PRICE_PER_100_KM = 15     # за каждые 100 км пути, руб.
KM_PER_DAY = 500          # сколько километров посылка проезжает за сутки
HANDLING_DAYS = 1         # сутки на приём и сортировку
MAX_WEIGHT_KG = 30        # максимальный вес одной посылки

TARIFFS = {
    "эконом": {"price_factor": 1.0, "speed_factor": 1.0},
    "экспресс": {"price_factor": 1.6, "speed_factor": 2.0},
}


class DeliveryError(ValueError):
    """Ошибка во входных данных для расчёта доставки."""


def _simplify(name: str) -> str:
    """Убирает лишние пробелы, регистр и букву «ё», чтобы сравнивать названия."""
    return name.strip().lower().replace("ё", "е")


def find_city(city: str) -> str:
    """Находит город в справочнике и возвращает его правильное написание.

    Регистр букв и лишние пробелы не важны: «  москва » → «Москва».
    """
    wanted = _simplify(city)
    for known in DISTANCES_KM:
        if _simplify(known) == wanted:
            return known
    raise DeliveryError(f"Город «{city.strip()}» пока не поддерживается")


def calculate_delivery(city: str, weight_kg: float, tariff: str = "эконом") -> dict:
    """Считает стоимость (руб.) и срок (дни) доставки посылки.

    Пример:
        >>> calculate_delivery("Москва", 2)
        {'city': 'Москва', 'distance_km': 1070, 'weight_kg': 2, 'tariff': 'эконом', 'price': 441, 'days': 4}
    """
    if weight_kg <= 0:
        raise DeliveryError("Вес должен быть больше нуля")
    if weight_kg > MAX_WEIGHT_KG:
        raise DeliveryError(f"Максимальный вес посылки — {MAX_WEIGHT_KG} кг")

    tariff_key = tariff.strip().lower()
    if tariff_key not in TARIFFS:
        raise DeliveryError(f"Неизвестный тариф «{tariff}». Доступны: {', '.join(TARIFFS)}")
    settings = TARIFFS[tariff_key]

    city_name = find_city(city)
    distance = DISTANCES_KM[city_name]

    price = BASE_PRICE + PRICE_PER_KG * weight_kg + PRICE_PER_100_KM * distance / 100
    # Обычное округление: 440.5 -> 441 (встроенный round() дал бы 440 — «банковское» округление)
    price = math.floor(price * settings["price_factor"] + 0.5)

    road_days = math.ceil(distance / (KM_PER_DAY * settings["speed_factor"]))
    days = HANDLING_DAYS + road_days

    return {
        "city": city_name,
        "distance_km": distance,
        "weight_kg": weight_kg,
        "tariff": tariff_key,
        "price": price,
        "days": days,
    }
