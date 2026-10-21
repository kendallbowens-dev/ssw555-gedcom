"""Unit tests for US12 - Parents not too old.
Run:  python3 -m unittest test_us12.py -v"""
import unittest
from datetime import date
from us12_us13 import check_us12_parents_not_too_old


def indi(birth):
    return {"name": "", "sex": "", "birth": birth, "death": None, "famc": set(), "fams": set()}


def fam(husband, wife, children):
    return {"married": None, "divorced": None, "husband": husband, "wife": wife, "children": set(children)}


class TestUS12(unittest.TestCase):

    def test_normal_ages_no_error(self):
        individuals = {"I1": indi(date(1950, 1, 1)), "I2": indi(date(1952, 1, 1)), "I3": indi(date(1980, 1, 1))}
        families = {"F1": fam("I1", "I2", ["I3"])}  # dad 30, mom 28 at birth
        self.assertEqual(check_us12_parents_not_too_old(individuals, families), [])

    def test_mother_exactly_60_is_flagged(self):
        individuals = {"I1": indi(date(1950, 1, 1)), "I2": indi(date(1920, 1, 1)), "I3": indi(date(1980, 1, 1))}
        families = {"F1": fam("I1", "I2", ["I3"])}  # mother exactly 60 at child's birth
        result = check_us12_parents_not_too_old(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("Mother", result[0])
        self.assertIn("US12", result[0])

    def test_mother_59_is_not_flagged(self):
        individuals = {"I1": indi(date(1950, 1, 1)), "I2": indi(date(1921, 6, 1)), "I3": indi(date(1980, 1, 1))}
        families = {"F1": fam("I1", "I2", ["I3"])}  # mother 58 at birth
        self.assertEqual(check_us12_parents_not_too_old(individuals, families), [])

    def test_father_exactly_80_is_flagged(self):
        individuals = {"I1": indi(date(1900, 1, 1)), "I2": indi(date(1955, 1, 1)), "I3": indi(date(1980, 1, 1))}
        families = {"F1": fam("I1", "I2", ["I3"])}  # father exactly 80 at child's birth
        result = check_us12_parents_not_too_old(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("Father", result[0])

    def test_father_79_is_not_flagged(self):
        individuals = {"I1": indi(date(1901, 6, 1)), "I2": indi(date(1955, 1, 1)), "I3": indi(date(1980, 1, 1))}
        families = {"F1": fam("I1", "I2", ["I3"])}  # father 78 at birth
        self.assertEqual(check_us12_parents_not_too_old(individuals, families), [])

    def test_missing_parent_is_skipped(self):
        # father id not present in individuals; mother normal age
        individuals = {"I2": indi(date(1955, 1, 1)), "I3": indi(date(1980, 1, 1))}
        families = {"F1": fam("I9", "I2", ["I3"])}
        self.assertEqual(check_us12_parents_not_too_old(individuals, families), [])

    def test_child_without_birth_is_skipped(self):
        individuals = {"I1": indi(date(1900, 1, 1)), "I2": indi(date(1900, 1, 1)), "I3": indi(None)}
        families = {"F1": fam("I1", "I2", ["I3"])}
        self.assertEqual(check_us12_parents_not_too_old(individuals, families), [])


if __name__ == "__main__":
    unittest.main()
