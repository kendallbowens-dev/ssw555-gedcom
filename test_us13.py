"""Unit tests for US13 - Siblings spacing.
Run:  python3 -m unittest test_us13.py -v"""
import unittest
from datetime import date
from us12_us13 import check_us13_siblings_spacing


def indi(birth):
    return {"name": "", "sex": "", "birth": birth, "death": None, "famc": set(), "fams": set()}


def fam(children):
    return {"married": None, "divorced": None, "husband": "IH", "wife": "IW", "children": set(children)}


class TestUS13(unittest.TestCase):

    def test_twins_same_day_not_flagged(self):
        individuals = {"I1": indi(date(2000, 1, 1)), "I2": indi(date(2000, 1, 1))}
        families = {"F1": fam(["I1", "I2"])}
        self.assertEqual(check_us13_siblings_spacing(individuals, families), [])

    def test_twins_one_day_apart_not_flagged(self):
        individuals = {"I1": indi(date(2000, 1, 1)), "I2": indi(date(2000, 1, 2))}
        families = {"F1": fam(["I1", "I2"])}
        self.assertEqual(check_us13_siblings_spacing(individuals, families), [])

    def test_three_months_apart_is_flagged(self):
        individuals = {"I1": indi(date(2000, 1, 1)), "I2": indi(date(2000, 4, 1))}
        families = {"F1": fam(["I1", "I2"])}  # ~3 months: more than 2 days, less than 8 months
        result = check_us13_siblings_spacing(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US13", result[0])

    def test_exactly_eight_months_not_flagged(self):
        individuals = {"I1": indi(date(2000, 1, 1)), "I2": indi(date(2000, 9, 1))}
        families = {"F1": fam(["I1", "I2"])}  # exactly 8 months apart
        self.assertEqual(check_us13_siblings_spacing(individuals, families), [])

    def test_normal_spacing_over_eight_months_not_flagged(self):
        individuals = {"I1": indi(date(2000, 1, 1)), "I2": indi(date(2002, 1, 1))}
        families = {"F1": fam(["I1", "I2"])}  # two years apart
        self.assertEqual(check_us13_siblings_spacing(individuals, families), [])

    def test_child_without_birth_is_skipped(self):
        individuals = {"I1": indi(date(2000, 1, 1)), "I2": indi(None)}
        families = {"F1": fam(["I1", "I2"])}
        self.assertEqual(check_us13_siblings_spacing(individuals, families), [])


if __name__ == "__main__":
    unittest.main()
