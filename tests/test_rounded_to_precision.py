from unittest import TestCase
from yat.calcus import rounded_to_precision


class TestRounded_to_precision(TestCase):
    def test_rounded_to_precision(self):
        self.assertEqual(rounded_to_precision(401.4600001000001002455, 8), 401.4600001)
        self.assertEqual(rounded_to_precision(401.4650001, 2), 401.46)
        self.assertEqual(rounded_to_precision(401.01200000004, 3), 401.012)
        self.assertRaises(TypeError, rounded_to_precision, 'crap', 3)
