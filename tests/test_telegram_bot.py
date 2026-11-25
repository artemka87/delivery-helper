import unittest

from telegram_bot import (
    FINISH,
    NEW_CALCULATION,
    cities_keyboard,
    format_result,
    next_action_keyboard,
    parse_weight,
    tariffs_keyboard,
)


class TelegramBotHelpersTests(unittest.TestCase):
    def test_parse_weight_accepts_comma_and_spaces(self):
        self.assertEqual(parse_weight("2,5"), 2.5)
        self.assertEqual(parse_weight(" 3 "), 3.0)

    def test_parse_weight_rejects_text_and_non_finite_number(self):
        with self.assertRaises(ValueError):
            parse_weight("много")
        with self.assertRaises(ValueError):
            parse_weight("nan")

    def test_format_result_contains_all_details(self):
        result = {
            "city": "Москва",
            "distance_km": 1070,
            "weight_kg": 2.5,
            "tariff": "эконом",
            "price": 461,
            "days": 4,
        }

        text = format_result(result)

        self.assertIn("Ростов-на-Дону → Москва", text)
        self.assertIn("1070 км", text)
        self.assertIn("2,5 кг", text)
        self.assertIn("эконом", text)
        self.assertIn("461 руб.", text)
        self.assertIn("4 дня", text)

    def test_keyboards_offer_expected_options(self):
        city_labels = [button.text for row in cities_keyboard().keyboard for button in row]
        tariff_labels = [button.text for row in tariffs_keyboard().keyboard for button in row]
        action_labels = [button.text for row in next_action_keyboard().keyboard for button in row]

        self.assertIn("Москва", city_labels)
        self.assertNotIn("Ростов-на-Дону", city_labels)
        self.assertEqual(tariff_labels, ["эконом", "экспресс"])
        self.assertEqual(action_labels, [NEW_CALCULATION, FINISH])


if __name__ == "__main__":
    unittest.main()
