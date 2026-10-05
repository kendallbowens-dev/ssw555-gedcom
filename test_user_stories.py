import unittest
from datetime import date

from gedcom_parser import check_us07_less_than_150, check_us21_correct_gender


def person(birth=None, death=None, sex=""):
    return {"birth": birth, "death": death, "sex": sex}


class TestUS07(unittest.TestCase):
    def test_living_person_under_150(self):
        people = {"@I1@": person(date(2000, 1, 1))}
        self.assertEqual(check_us07_less_than_150(people, today=date(2026, 9, 28)), [])

    def test_deceased_person_under_150(self):
        people = {"@I1@": person(date(1900, 1, 1), date(1980, 1, 1))}
        self.assertEqual(check_us07_less_than_150(people), [])

    def test_one_day_before_150th_birthday(self):
        people = {"@I1@": person(date(1876, 9, 29))}
        self.assertEqual(check_us07_less_than_150(people, today=date(2026, 9, 28)), [])

    def test_exactly_150_is_flagged(self):
        people = {"@I1@": person(date(1876, 9, 28))}
        result = check_us07_less_than_150(people, today=date(2026, 9, 28))
        self.assertEqual(len(result), 1)
        self.assertIn("US07: @I1@", result[0])

    def test_over_150_at_death_is_flagged(self):
        people = {"@I1@": person(date(1800, 1, 1), date(1950, 1, 2))}
        result = check_us07_less_than_150(people)
        self.assertEqual(len(result), 1)
        self.assertIn("US07: @I1@", result[0])

    def test_missing_birth_date_is_skipped(self):
        self.assertEqual(check_us07_less_than_150({"@I1@": person()}), [])


class TestUS21(unittest.TestCase):
    def setUp(self):
        self.people = {"@I1@": person(sex="M"), "@I2@": person(sex="F")}
        self.families = {"@F1@": {"husband": "@I1@", "wife": "@I2@"}}

    def test_correct_roles(self):
        self.assertEqual(check_us21_correct_gender(self.people, self.families), [])

    def test_husband_with_f_recorded(self):
        self.people["@I1@"]["sex"] = "F"
        result = check_us21_correct_gender(self.people, self.families)
        self.assertEqual(len(result), 1)
        self.assertIn("HUSB @I1@", result[0])

    def test_wife_with_m_recorded(self):
        self.people["@I2@"]["sex"] = "M"
        result = check_us21_correct_gender(self.people, self.families)
        self.assertEqual(len(result), 1)
        self.assertIn("WIFE @I2@", result[0])

    def test_both_roles_wrong(self):
        self.people["@I1@"]["sex"] = "F"
        self.people["@I2@"]["sex"] = "M"
        self.assertEqual(len(check_us21_correct_gender(self.people, self.families)), 2)

    def test_missing_person_is_skipped(self):
        self.families["@F1@"]["wife"] = "@I99@"
        self.assertEqual(check_us21_correct_gender(self.people, self.families), [])


if __name__ == "__main__":
    unittest.main()
