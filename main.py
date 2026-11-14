"""Консольная программа: спрашивает город, вес и тариф, показывает стоимость и срок."""

from delivery_helper.calculator import (
    DISTANCES_KM,
    TARIFFS,
    DeliveryError,
    calculate_delivery,
    find_city,
)


def ask_delivery() -> bool:
    """Задаёт вопросы об одной посылке. Возвращает False, когда пора выйти."""
    city = input("Город назначения: ").strip()
    if not city:
        return False

    try:
        city = find_city(city)  # сразу проверяем город, чтобы не спрашивать вес зря
        weight_text = input("Вес посылки, кг: ").replace(",", ".")
        try:
            weight = float(weight_text)
        except ValueError:
            raise DeliveryError("Вес нужно ввести числом, например 2.5") from None
        tariff = input("Тариф (эконом/экспресс) [эконом]: ").strip() or "эконом"
        result = calculate_delivery(city, weight, tariff)
    except DeliveryError as error:
        print(f"Ошибка: {error}\n")
        return True

    print(
        f"\n{result['city']} ({result['distance_km']} км), {result['weight_kg']} кг, "
        f"тариф «{result['tariff']}»\n"
        f"Стоимость: {result['price']} руб.\n"
        f"Срок доставки: {result['days']} дн.\n"
    )
    return True


def main() -> None:
    print("=== Калькулятор доставки из Ростова-на-Дону ===")
    print("Доступные города:", ", ".join(DISTANCES_KM))
    print("Тарифы:", ", ".join(TARIFFS))
    print("Для выхода нажмите Enter, не вводя город.\n")

    try:
        while ask_delivery():
            pass
    except (EOFError, KeyboardInterrupt):
        print()
    print("До свидания!")


if __name__ == "__main__":
    main()
