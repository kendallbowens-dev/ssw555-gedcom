"""
Unit tests for US17: parents should not marry their descendants.
Run:  python3 -m unittest test_us17.py -v
"""
import unittest

from gedcom_parser import check_us17_no_marriage_to_descendants


def indi(famc=None, fams=None):
    return {"name": "", "sex": "", "birth": None, "death": None,
            "famc": set(famc or []), "fams": set(fams or [])}


def fam(husband="", wife="", children=None):
    return {"married": None, "divorced": None, "husband": husband,
            "wife": wife, "children": set(children or [])}


class TestUS17(unittest.TestCase):

    def test_unrelated_spouses_no_error(self):
        individuals = {"I1": indi(fams=["F1"]), "I2": indi(fams=["F1"])}
        families = {"F1": fam("I1", "I2")}
        self.assertEqual(check_us17_no_marriage_to_descendants(individuals, families), [])

    def test_parent_marries_child_is_flagged(self):
        # I1 and I2 have child I3; then I1 marries I3 in F2.
        individuals = {
            "I1": indi(fams=["F1", "F2"]),
            "I2": indi(fams=["F1"]),
            "I3": indi(famc=["F1"], fams=["F2"]),
        }
        families = {
            "F1": fam("I1", "I2", ["I3"]),
            "F2": fam("I1", "I3"),
        }
        result = check_us17_no_marriage_to_descendants(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US17", result[0])
        self.assertIn("F2", result[0])

    def test_grandparent_marries_grandchild_is_flagged(self):
        # I1 -> I3 (child) -> I5 (grandchild); I1 later marries I5 in F3.
        individuals = {
            "I1": indi(fams=["F1", "F3"]),
            "I2": indi(fams=["F1"]),
            "I3": indi(famc=["F1"], fams=["F2"]),
            "I4": indi(fams=["F2"]),
            "I5": indi(famc=["F2"], fams=["F3"]),
        }
        families = {
            "F1": fam("I1", "I2", ["I3"]),
            "F2": fam("I3", "I4", ["I5"]),
            "F3": fam("I1", "I5"),
        }
        result = check_us17_no_marriage_to_descendants(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US17", result[0])
        self.assertIn("F3", result[0])

    def test_wife_is_ancestor_also_flagged(self):
        # Wife I2 is the mother of husband I1 (role reversed).
        individuals = {
            "I2": indi(fams=["F1", "F2"]),
            "I9": indi(fams=["F1"]),
            "I1": indi(famc=["F1"], fams=["F2"]),
        }
        families = {
            "F1": fam("I9", "I2", ["I1"]),
            "F2": fam("I1", "I2"),
        }
        result = check_us17_no_marriage_to_descendants(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US17", result[0])
        self.assertIn("F2", result[0])

    def test_missing_spouse_is_skipped(self):
        individuals = {"I1": indi(fams=["F1"])}
        families = {"F1": fam("I1", "")}
        self.assertEqual(check_us17_no_marriage_to_descendants(individuals, families), [])


if __name__ == "__main__":
    unittest.main()
