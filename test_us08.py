"""
SSW 555 - Unit tests (test-first assignment)
User story: US08 - Birth before marriage of parents
Author: Kofwana Lawson

Tests the check_us08_birth_before_parents_marriage function in gedcom_parser.py.
US08 says a child should be born after the parents' marriage and not more than
9 months after their divorce; the function returns a list of anomaly messages.

Run with:
    python3 -m unittest test_us08.py -v
"""

import unittest
from datetime import date

from gedcom_parser import check_us08_birth_before_parents_marriage


def make_individual(birth=None, death=None, famc=None, fams=None, name="", sex=""):
    return {
        "name": name,
        "sex": sex,
        "birth": birth,
        "death": death,
        "famc": set(famc or []),
        "fams": set(fams or []),
    }


def make_family(married=None, divorced=None, husband="", wife="", children=None):
    return {
        "married": married,
        "divorced": divorced,
        "husband": husband,
        "wife": wife,
        "children": set(children or []),
    }


class TestUS08BirthBeforeParentsMarriage(unittest.TestCase):

    def test_birth_before_marriage_is_flagged(self):
        individuals = {"I01": make_individual(birth=date(1998, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(2000, 1, 1),
                                       husband="I10", wife="I11", children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(len(result), 1)

    def test_flag_message_names_story_and_individual(self):
        individuals = {"I01": make_individual(birth=date(1998, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(2000, 1, 1), children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertIn("US08", result[0])
        self.assertIn("I01", result[0])

    def test_birth_after_marriage_is_not_flagged(self):
        individuals = {"I01": make_individual(birth=date(2001, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(2000, 1, 1), children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(result, [])

    def test_birth_same_day_as_marriage_is_not_flagged(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(2000, 1, 1), children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(result, [])

    def test_birth_more_than_nine_months_after_divorce_is_flagged(self):
        individuals = {"I01": make_individual(birth=date(2001, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(1995, 1, 1),
                                       divorced=date(2000, 1, 1), children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US08", result[0])

    def test_birth_within_nine_months_after_divorce_is_not_flagged(self):
        individuals = {"I01": make_individual(birth=date(2000, 6, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(1995, 1, 1),
                                       divorced=date(2000, 1, 1), children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(result, [])

    def test_individual_without_birth_date_is_skipped(self):
        individuals = {"I01": make_individual(birth=None, famc=["F01"])}
        families = {"F01": make_family(married=date(2000, 1, 1), children=["I01"])}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(result, [])

    def test_individual_without_parent_family_is_not_flagged(self):
        individuals = {"I01": make_individual(birth=date(1998, 1, 1), famc=[])}
        families = {}
        result = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
