import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from gedcom_parser import (
    add_months,
    check_us01_dates_before_today,
    check_us02_birth_before_marriage,
    check_us03_birth_before_death,
    check_us04_marriage_before_divorce,
    check_us05_marriage_before_death,
    check_us06_divorce_before_death,
    check_us07_less_than_150,
    check_us08_birth_before_parents_marriage,
    check_us09_birth_before_parents_death,
    check_us10_marriage_after_14,
    check_us11_no_bigamy,
    check_us14_multiple_births,
    check_us15_fewer_than_15_siblings,
    check_us21_correct_gender,
    compute_age,
    format_date,
    format_id_set,
    marriage_end,
    parse_gedcom_date,
    parse_line,
    sort_key,
)


def make_individual(name="", sex="", birth=None, death=None, famc=None, fams=None):
    return {
        "name": name,
        "sex": sex,
        "birth": birth,
        "death": death,
        "famc": set(famc or ()),
        "fams": set(fams or ()),
    }


def make_family(married=None, divorced=None, husband="", wife="", children=None):
    return {
        "married": married,
        "divorced": divorced,
        "husband": husband,
        "wife": wife,
        "children": set(children or ()),
    }


class TestParseLine(unittest.TestCase):
    def test_level_0_indi(self):
        self.assertEqual(parse_line("0 I01 INDI"), (0, "INDI", "I01"))

    def test_level_0_fam(self):
        self.assertEqual(parse_line("0 F01 FAM"), (0, "FAM", "F01"))

    def test_level_0_other_tag(self):
        self.assertEqual(parse_line("0 NOTE hello world"), (0, "NOTE", "hello world"))

    def test_level_0_trailer_no_args(self):
        self.assertEqual(parse_line("0 TRLR"), (0, "TRLR", ""))

    def test_level_1_with_args(self):
        self.assertEqual(parse_line("1 NAME Joe /Smith/"), (1, "NAME", "Joe /Smith/"))

    def test_level_1_no_args(self):
        self.assertEqual(parse_line("1 BIRT"), (1, "BIRT", ""))

    def test_level_2_date(self):
        self.assertEqual(parse_line("2 DATE 4 FEB 1942"), (2, "DATE", "4 FEB 1942"))

    def test_strips_trailing_newline_and_cr(self):
        self.assertEqual(parse_line("1 SEX M\r\n"), (1, "SEX", "M"))


class TestSortKey(unittest.TestCase):
    def test_numeric_ordering_not_lexicographic(self):
        ids = ["I10", "I2", "I1"]
        self.assertEqual(sorted(ids, key=sort_key), ["I1", "I2", "I10"])

    def test_different_prefixes_grouped_separately(self):
        ids = ["F2", "I1", "F1", "I2"]
        self.assertEqual(sorted(ids, key=sort_key), ["F1", "F2", "I1", "I2"])

    def test_no_digits(self):
        self.assertEqual(sort_key("ABC"), ("ABC", 0))


class TestParseGedcomDate(unittest.TestCase):
    def test_valid_date(self):
        self.assertEqual(parse_gedcom_date("4 FEB 1942"), date(1942, 2, 4))

    def test_invalid_date_returns_none(self):
        self.assertIsNone(parse_gedcom_date("not a date"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_gedcom_date(""))


class TestAddMonths(unittest.TestCase):
    def test_simple_addition(self):
        self.assertEqual(add_months(date(2000, 1, 15), 2), date(2000, 3, 15))

    def test_year_rollover(self):
        self.assertEqual(add_months(date(2000, 11, 1), 3), date(2001, 2, 1))

    def test_clamps_to_end_of_shorter_month(self):
        # Jan 31 + 1 month -> Feb has no 31st, clamp to the 29th (2000 is a leap year)
        self.assertEqual(add_months(date(2000, 1, 31), 1), date(2000, 2, 29))

    def test_14_years_in_months(self):
        self.assertEqual(add_months(date(2000, 6, 15), 168), date(2014, 6, 15))


class TestFormatHelpers(unittest.TestCase):
    def test_format_date_with_value(self):
        self.assertEqual(format_date(date(1998, 11, 26)), "1998-11-26")

    def test_format_date_none(self):
        self.assertEqual(format_date(None), "NA")

    def test_format_id_set_empty(self):
        self.assertEqual(format_id_set(set()), "NA")

    def test_format_id_set_sorted(self):
        self.assertEqual(format_id_set({"F2", "F10", "F1"}), "{'F1', 'F2', 'F10'}")


class TestComputeAge(unittest.TestCase):
    def test_no_birth(self):
        self.assertEqual(compute_age(None, None), "NA")

    def test_age_at_death(self):
        self.assertEqual(compute_age(date(1942, 2, 4), date(1975, 7, 9)), 33)

    def test_age_before_birthday_this_year(self):
        self.assertEqual(compute_age(date(2000, 12, 31), date(2020, 1, 1)), 19)

    def test_age_alive_uses_today(self):
        birth = date(2000, 1, 1)
        today = date.today()
        expected = today.year - birth.year - ((today.month, today.day) < (1, 1))
        self.assertEqual(compute_age(birth, None), expected)


class TestUS01DatesBeforeToday(unittest.TestCase):
    def test_future_birth_flagged(self):
        individuals = {"I01": make_individual(birth=date(9999, 1, 1))}
        errors = check_us01_dates_before_today(individuals, {})
        self.assertEqual(len(errors), 1)
        self.assertIn("US01", errors[0])

    def test_future_marriage_flagged(self):
        families = {"F01": make_family(married=date(9999, 1, 1))}
        errors = check_us01_dates_before_today({}, families)
        self.assertEqual(len(errors), 1)

    def test_past_dates_clean(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1), death=date(2020, 1, 1))}
        families = {"F01": make_family(married=date(2010, 1, 1), divorced=date(2015, 1, 1))}
        self.assertEqual(check_us01_dates_before_today(individuals, families), [])


class TestUS02BirthBeforeMarriage(unittest.TestCase):
    def test_birth_after_marriage_flagged(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1), fams=["F01"])}
        families = {"F01": make_family(married=date(1990, 1, 1))}
        errors = check_us02_birth_before_marriage(individuals, families)
        self.assertEqual(len(errors), 1)

    def test_birth_before_marriage_clean(self):
        individuals = {"I01": make_individual(birth=date(1980, 1, 1), fams=["F01"])}
        families = {"F01": make_family(married=date(1990, 1, 1))}
        self.assertEqual(check_us02_birth_before_marriage(individuals, families), [])

    def test_no_birth_skipped(self):
        individuals = {"I01": make_individual(fams=["F01"])}
        families = {"F01": make_family(married=date(1990, 1, 1))}
        self.assertEqual(check_us02_birth_before_marriage(individuals, families), [])


class TestUS03BirthBeforeDeath(unittest.TestCase):
    def test_birth_after_death_flagged(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1), death=date(1999, 1, 1))}
        errors = check_us03_birth_before_death(individuals)
        self.assertEqual(len(errors), 1)

    def test_no_death_record_skipped(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1))}
        self.assertEqual(check_us03_birth_before_death(individuals), [])


class TestUS04MarriageBeforeDivorce(unittest.TestCase):
    def test_marriage_after_divorce_flagged(self):
        families = {"F01": make_family(married=date(2000, 1, 1), divorced=date(1999, 1, 1))}
        errors = check_us04_marriage_before_divorce(families)
        self.assertEqual(len(errors), 1)

    def test_no_divorce_record_skipped(self):
        families = {"F01": make_family(married=date(2000, 1, 1))}
        self.assertEqual(check_us04_marriage_before_divorce(families), [])


class TestUS05MarriageBeforeDeath(unittest.TestCase):
    def test_marriage_after_husband_death_flagged(self):
        individuals = {"I01": make_individual(death=date(1990, 1, 1))}
        families = {"F01": make_family(married=date(2000, 1, 1), husband="I01")}
        errors = check_us05_marriage_before_death(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn("husband", errors[0])

    def test_marriage_before_death_clean(self):
        individuals = {
            "I01": make_individual(death=date(2010, 1, 1)),
            "I02": make_individual(death=date(2010, 1, 1)),
        }
        families = {"F01": make_family(married=date(2000, 1, 1), husband="I01", wife="I02")}
        self.assertEqual(check_us05_marriage_before_death(individuals, families), [])


class TestUS06DivorceBeforeDeath(unittest.TestCase):
    def test_divorce_after_wife_death_flagged(self):
        individuals = {"I02": make_individual(death=date(1990, 1, 1))}
        families = {"F01": make_family(divorced=date(2000, 1, 1), wife="I02")}
        errors = check_us06_divorce_before_death(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn("wife", errors[0])

    def test_no_divorce_skipped(self):
        individuals = {"I02": make_individual(death=date(1990, 1, 1))}
        families = {"F01": make_family(wife="I02")}
        self.assertEqual(check_us06_divorce_before_death(individuals, families), [])


class TestUS07LessThan150(unittest.TestCase):
    def test_living_person_over_150_flagged(self):
        individuals = {"I01": make_individual(birth=date(1800, 1, 1))}
        errors = check_us07_less_than_150(individuals, today=date(2026, 1, 1))
        self.assertEqual(len(errors), 1)

    def test_deceased_person_over_150_flagged(self):
        individuals = {"I01": make_individual(birth=date(1700, 1, 1), death=date(1900, 1, 1))}
        errors = check_us07_less_than_150(individuals, today=date(2026, 1, 1))
        self.assertEqual(len(errors), 1)

    def test_under_150_clean(self):
        individuals = {"I01": make_individual(birth=date(1990, 1, 1))}
        self.assertEqual(check_us07_less_than_150(individuals, today=date(2026, 1, 1)), [])


class TestUS08BirthBeforeParentsMarriage(unittest.TestCase):
    def test_birth_before_parents_marriage_flagged(self):
        individuals = {"I01": make_individual(birth=date(1985, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(1990, 1, 1))}
        anomalies = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(len(anomalies), 1)
        self.assertIn("before marriage", anomalies[0])

    def test_birth_too_long_after_divorce_flagged(self):
        individuals = {"I01": make_individual(birth=date(1992, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(1980, 1, 1), divorced=date(1991, 1, 1))}
        anomalies = check_us08_birth_before_parents_marriage(individuals, families)
        self.assertEqual(len(anomalies), 1)
        self.assertIn("after divorce", anomalies[0])

    def test_birth_within_window_clean(self):
        individuals = {"I01": make_individual(birth=date(1985, 1, 1), famc=["F01"])}
        families = {"F01": make_family(married=date(1980, 1, 1), divorced=date(1991, 1, 1))}
        self.assertEqual(check_us08_birth_before_parents_marriage(individuals, families), [])


class TestUS09BirthBeforeParentsDeath(unittest.TestCase):
    def test_born_after_mother_death_flagged(self):
        individuals = {
            "I01": make_individual(birth=date(2000, 1, 1), famc=["F01"]),
            "I02": make_individual(death=date(1999, 1, 1)),
        }
        families = {"F01": make_family(wife="I02")}
        errors = check_us09_birth_before_parents_death(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn("mother", errors[0])

    def test_born_too_long_after_father_death_flagged(self):
        individuals = {
            "I01": make_individual(birth=date(2000, 6, 1), famc=["F01"]),
            "I03": make_individual(death=date(1999, 1, 1)),
        }
        families = {"F01": make_family(husband="I03")}
        errors = check_us09_birth_before_parents_death(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn("father", errors[0])

    def test_born_within_window_clean(self):
        individuals = {
            "I01": make_individual(birth=date(1999, 6, 1), famc=["F01"]),
            "I02": make_individual(death=date(2005, 1, 1)),
            "I03": make_individual(death=date(1999, 10, 1)),
        }
        families = {"F01": make_family(husband="I03", wife="I02")}
        self.assertEqual(check_us09_birth_before_parents_death(individuals, families), [])


class TestUS10MarriageAfter14(unittest.TestCase):
    def test_marriage_too_soon_after_birth_flagged(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1))}
        families = {"F01": make_family(married=date(2010, 1, 1), husband="I01")}
        errors = check_us10_marriage_after_14(individuals, families)
        self.assertEqual(len(errors), 1)

    def test_marriage_at_14_years_clean(self):
        individuals = {"I01": make_individual(birth=date(2000, 1, 1))}
        families = {"F01": make_family(married=date(2014, 1, 1), husband="I01")}
        self.assertEqual(check_us10_marriage_after_14(individuals, families), [])


class TestMarriageEnd(unittest.TestCase):
    def test_divorced_takes_precedence(self):
        fam = make_family(divorced=date(1995, 1, 1))
        self.assertEqual(marriage_end(fam, {}), date(1995, 1, 1))

    def test_falls_back_to_earlier_spouse_death(self):
        individuals = {
            "I01": make_individual(death=date(2000, 1, 1)),
            "I02": make_individual(death=date(1998, 1, 1)),
        }
        fam = make_family(husband="I01", wife="I02")
        self.assertEqual(marriage_end(fam, individuals), date(1998, 1, 1))

    def test_ongoing_marriage_returns_none(self):
        individuals = {"I01": make_individual()}
        fam = make_family(husband="I01")
        self.assertIsNone(marriage_end(fam, individuals))


class TestUS11NoBigamy(unittest.TestCase):
    def test_overlapping_marriages_flagged(self):
        individuals = {
            "I01": make_individual(fams=["F01", "F02"]),
        }
        families = {
            "F01": make_family(married=date(1980, 1, 1), husband="I01"),
            "F02": make_family(married=date(1985, 1, 1), husband="I01"),
        }
        errors = check_us11_no_bigamy(individuals, families)
        self.assertEqual(len(errors), 1)

    def test_sequential_marriages_after_divorce_clean(self):
        individuals = {
            "I01": make_individual(fams=["F01", "F02"]),
        }
        families = {
            "F01": make_family(married=date(1980, 1, 1), divorced=date(1984, 1, 1), husband="I01"),
            "F02": make_family(married=date(1985, 1, 1), husband="I01"),
        }
        self.assertEqual(check_us11_no_bigamy(individuals, families), [])

    def test_single_marriage_clean(self):
        individuals = {"I01": make_individual(fams=["F01"])}
        families = {"F01": make_family(married=date(1980, 1, 1), husband="I01")}
        self.assertEqual(check_us11_no_bigamy(individuals, families), [])



class TestUS14MultipleBirths(unittest.TestCase):

    def test_five_births(self):
        people = {}

        for i in range(5):
            people[f"I{i}"] = {"birth": "21 may 2001"}

        families = {
            "F01": make_family(children=["I0", "I1", "I2", "I3", "I4"])
        }
        errors = check_us14_multiple_births(people, families)
        self.assertEqual(len(errors), 0)

    def test_six_births(self):
        people = {}
        
        for i in range(6):
            people[f"I{i}"] = {"birth": "21 may 2001"}

        families = {
            "F01": make_family(children=["I0", "I1", "I2", "I3", "I4", "I5"])
        }
        errors = check_us14_multiple_births(people, families)
        self.assertEqual(len(errors), 1)



# Alexis and Kendall Pair Programming
class TestUS15FewerThan15Siblings(unittest.TestCase):
    def test_less_than_15_siblings(self):
        families = {
            "F01": make_family(children=["I1", "I2", "I3"])
        }

        errors = check_us15_fewer_than_15_siblings(families)
        self.assertEqual(len(errors), 0)

    def test_more_than_15_siblings(self):
        families = {
            "F01": make_family(children=[f"I{i}" for i in range(16)])
        }

        errors = check_us15_fewer_than_15_siblings(families)
        self.assertEqual(len(errors), 1)





class TestUS21CorrectGender(unittest.TestCase):
    def test_husband_not_male_flagged(self):
        individuals = {"I01": make_individual(sex="F")}
        families = {"F01": make_family(husband="I01")}
        errors = check_us21_correct_gender(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn("HUSB", errors[0])

    def test_wife_not_female_flagged(self):
        individuals = {"I02": make_individual(sex="M")}
        families = {"F01": make_family(wife="I02")}
        errors = check_us21_correct_gender(individuals, families)
        self.assertEqual(len(errors), 1)
        self.assertIn("WIFE", errors[0])

    def test_correct_genders_clean(self):
        individuals = {
            "I01": make_individual(sex="M"),
            "I02": make_individual(sex="F"),
        }
        families = {"F01": make_family(husband="I01", wife="I02")}
        self.assertEqual(check_us21_correct_gender(individuals, families), [])


class TestMainIntegration(unittest.TestCase):
    def run_parser(self, gedcom_text):
        with tempfile.TemporaryDirectory() as tmp_dir:
            gedcom_path = Path(tmp_dir) / "test.ged"
            gedcom_path.write_text(gedcom_text)
            result = subprocess.run(
                [sys.executable, "gedcom_parser.py", str(gedcom_path)],
                cwd=Path(__file__).resolve().parent,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout

    def test_clean_file_produces_tables_and_no_errors(self):
        output = self.run_parser(
            "0 I01 INDI\n"
            "1 NAME Joe /Smith/\n"
            "1 SEX M\n"
            "1 BIRT\n"
            "2 DATE 15 JUL 1960\n"
            "1 FAMS F01\n"
            "0 I02 INDI\n"
            "1 NAME Jane /Smith/\n"
            "1 SEX F\n"
            "1 BIRT\n"
            "2 DATE 2 JUN 1962\n"
            "1 FAMS F01\n"
            "0 F01 FAM\n"
            "1 MARR\n"
            "2 DATE 14 FEB 1985\n"
            "1 HUSB I01\n"
            "1 WIFE I02\n"
            "0 TRLR\n"
        )
        self.assertIn("Individuals", output)
        self.assertIn("Families", output)
        self.assertIn("I01", output)
        self.assertIn("F01", output)
        self.assertNotIn("Validation Errors", output)

    def test_bad_file_reports_validation_errors(self):
        output = self.run_parser(
            "0 I01 INDI\n"
            "1 NAME Bad /Dates/\n"
            "1 SEX M\n"
            "1 BIRT\n"
            "2 DATE 1 JAN 2000\n"
            "1 DEAT\n"
            "2 DATE 1 JAN 1999\n"
            "0 TRLR\n"
        )
        self.assertIn("Validation Errors", output)
        self.assertIn("US03", output)


if __name__ == "__main__":
    unittest.main()
