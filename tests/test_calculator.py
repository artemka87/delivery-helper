import unittest

from delivery_helper.calculator import DeliveryError, calculate_delivery


class CalculateDeliveryTests(unittest.TestCase):
    def test_moscow_economy(self):
        result = calculate_delivery("Москва", 2)
        # 200 + 40*2 + 15*1070/100 = 440.5 -> 441
        self.assertEqual(result["price"], 441)
        # 1 день обработки + ceil(1070/500) = 1 + 3 = 4
        self.assertEqual(result["days"], 4)

    def test_express_is_faster_and_more_expensive(self):
        economy = calculate_delivery("Казань", 5)
        express = calculate_delivery("Казань", 5, "экспресс")
        self.assertGreater(express["price"], economy["price"])
        self.assertLess(express["days"], economy["days"])

    def test_city_name_is_case_insensitive(self):
        result = calculate_delivery("  санкт-ПЕТЕРБУРГ ", 1)
        self.assertEqual(result["distance_km"], 1780)
        self.assertEqual(result["city"], "Санкт-Петербург")

    def test_unknown_city(self):
        with self.assertRaises(DeliveryError):
            calculate_delivery("Атлантида", 1)

    def test_invalid_weight(self):
        with self.assertRaises(DeliveryError):
            calculate_delivery("Москва", 0)
        with self.assertRaises(DeliveryError):
            calculate_delivery("Москва", 31)

    def test_unknown_tariff(self):
        with self.assertRaises(DeliveryError):
            calculate_delivery("Москва", 1, "ракета")


if __name__ == "__main__":
    unittest.main()
