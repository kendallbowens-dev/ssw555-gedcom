"""
Unit tests for US20: aunts and uncles should not marry nieces or nephews.
Run:  python3 -m unittest test_us20.py -v
"""
import unittest

from gedcom_parser import check_us20_aunts_and_uncles


def indi(famc=None, fams=None):
    return {"name": "", "sex": "", "birth": None, "death": None,
            "famc": set(famc or []), "fams": set(fams or [])}


def fam(husband="", wife="", children=None):
    return {"married": None, "divorced": None, "husband": husband,
            "wife": wife, "children": set(children or [])}


class TestUS20(unittest.TestCase):

    def test_unrelated_spouses_no_error(self):
        individuals = {"I1": indi(fams=["F1"]), "I2": indi(fams=["F1"])}
        families = {"F1": fam("I1", "I2")}
        self.assertEqual(check_us20_aunts_and_uncles(individuals, families), [])

    def test_uncle_marries_niece_is_flagged(self):
        # Grandparents F1 have children I3 (the uncle) and I4.
        # I4 marries I7 in F2 and has child I8 (the niece).
        # I3 (uncle) then marries I8 (niece) in F3.
        individuals = {
            "I1": indi(fams=["F1"]),
            "I2": indi(fams=["F1"]),
            "I3": indi(famc=["F1"], fams=["F3"]),
            "I4": indi(famc=["F1"], fams=["F2"]),
            "I7": indi(fams=["F2"]),
            "I8": indi(famc=["F2"], fams=["F3"]),
        }
        families = {
            "F1": fam("I1", "I2", ["I3", "I4"]),
            "F2": fam("I4", "I7", ["I8"]),
            "F3": fam("I3", "I8"),
        }
        result = check_us20_aunts_and_uncles(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US20", result[0])
        self.assertIn("F3", result[0])

    def test_aunt_marries_nephew_is_flagged(self):
        # Aunt I3 (wife role) marries her nephew I8 (husband role).
        individuals = {
            "I1": indi(fams=["F1"]),
            "I2": indi(fams=["F1"]),
            "I3": indi(famc=["F1"], fams=["F3"]),
            "I4": indi(famc=["F1"], fams=["F2"]),
            "I7": indi(fams=["F2"]),
            "I8": indi(famc=["F2"], fams=["F3"]),
        }
        families = {
            "F1": fam("I1", "I2", ["I3", "I4"]),
            "F2": fam("I4", "I7", ["I8"]),
            "F3": fam("I8", "I3"),
        }
        result = check_us20_aunts_and_uncles(individuals, families)
        self.assertEqual(len(result), 1)
        self.assertIn("US20", result[0])
        self.assertIn("F3", result[0])

    def test_cousins_not_flagged(self):
        # I5 and I6 are first cousins, not aunt/uncle and niece/nephew.
        individuals = {
            "I1": indi(fams=["F1"]),
            "I2": indi(fams=["F1"]),
            "I3": indi(famc=["F1"], fams=["F2"]),
            "I4": indi(famc=["F1"], fams=["F3"]),
            "IA": indi(fams=["F2"]),
            "IB": indi(fams=["F3"]),
            "I5": indi(famc=["F2"], fams=["F4"]),
            "I6": indi(famc=["F3"], fams=["F4"]),
        }
        families = {
            "F1": fam("I1", "I2", ["I3", "I4"]),
            "F2": fam("I3", "IA", ["I5"]),
            "F3": fam("I4", "IB", ["I6"]),
            "F4": fam("I5", "I6"),
        }
        self.assertEqual(check_us20_aunts_and_uncles(individuals, families), [])

    def test_missing_spouse_is_skipped(self):
        individuals = {"I1": indi(fams=["F1"])}
        families = {"F1": fam("I1", "")}
        self.assertEqual(check_us20_aunts_and_uncles(individuals, families), [])


if __name__ == "__main__":
    unittest.main()
