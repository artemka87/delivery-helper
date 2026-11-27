import unittest

from delivery_helper.natural_language import DeliveryRequest, parse_delivery_request


class NaturalLanguageParserTests(unittest.TestCase):
    def test_parses_complete_question(self):
        self.assertEqual(
            parse_delivery_request("Сколько стоит отправить 3 кг в Сочи?"),
            DeliveryRequest(city="Сочи", weight_kg=3.0, tariff="эконом"),
        )

    def test_parses_decimal_comma_and_express_tariff(self):
        self.assertEqual(
            parse_delivery_request("Экспресс-доставка 2,5 кг до Москвы"),
            DeliveryRequest(city="Москва", weight_kg=2.5, tariff="экспресс"),
        )

    def test_parses_case_and_city_inflection(self):
        result = parse_delivery_request("ЦЕНА: 1 кг в МОСКВУ")
        self.assertEqual(result.city, "Москва")
        self.assertEqual(result.weight_kg, 1.0)

    def test_returns_none_for_incomplete_or_ambiguous_text(self):
        self.assertIsNone(parse_delivery_request("Сколько стоит отправить в Сочи?"))
        self.assertIsNone(parse_delivery_request("Сколько стоит отправить 3 кг?"))
        self.assertIsNone(parse_delivery_request("3 кг в Сочи и 5 кг в Москве"))
        self.assertIsNone(parse_delivery_request("Доставка за 3 дня в Сочи"))

    def test_returns_none_for_unsupported_destination(self):
        self.assertIsNone(parse_delivery_request("3 кг в Атлантиду"))


if __name__ == "__main__":
    unittest.main()
