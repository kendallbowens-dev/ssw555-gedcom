import sys
from datetime import date, datetime

VALID_TAGS = {
    (0, "INDI"),
    (0, "FAM"),
    (0, "HEAD"),
    (0, "TRLR"),
    (0, "NOTE"),
    (1, "NAME"),
    (1, "SEX"),
    (1, "BIRT"),
    (1, "DEAT"),
    (1, "FAMC"),
    (1, "FAMS"),
    (1, "MARR"),
    (1, "HUSB"),
    (1, "WIFE"),
    (1, "CHIL"),
    (1, "DIV"),
    (2, "DATE"),
}


def parse_line(line):
    stripped = line.rstrip("\n").rstrip("\r")
    first_space = stripped.find(" ")
    level = int(stripped[:first_space])
    rest = stripped[first_space + 1:]

    if level == 0:
        second_space = rest.find(" ")
        if second_space == -1:
            first_token = rest
            remainder = ""
        else:
            first_token = rest[:second_space]
            remainder = rest[second_space + 1:]

        if remainder in ("INDI", "FAM"):
            tag = remainder
            arguments = first_token
        else:
            tag = first_token
            arguments = remainder
    else:
        tag_space = rest.find(" ")
        if tag_space == -1:
            tag = rest
            arguments = ""
        else:
            tag = rest[:tag_space]
            arguments = rest[tag_space + 1:]

    return level, tag, arguments


def sort_key(record_id):
    i = len(record_id)
    while i > 0 and record_id[i - 1].isdigit():
        i -= 1
    prefix, digits = record_id[:i], record_id[i:]
    return (prefix, int(digits) if digits else 0)


def parse_gedcom_date(date_str):
    try:
        return datetime.strptime(date_str, "%d %b %Y").date()
    except ValueError:
        return None


def format_date(d):
    return d.strftime("%Y-%m-%d") if d else "NA"


def compute_age(birth, death):
    if not birth:
        return "NA"
    end = death if death else date.today()
    return end.year - birth.year - ((end.month, end.day) < (birth.month, birth.day))


def format_id_set(ids):
    if not ids:
        return "NA"
    return "{" + ", ".join(f"'{i}'" for i in sorted(ids, key=sort_key)) + "}"


def print_table(title, headers, rows):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def format_row(cells):
        return " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(cells))

    print(f"\n{title}")
    print(format_row(headers))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(format_row(row))


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gedcom_parser.py <gedcom_file>")
        sys.exit(1)

    gedcom_path = sys.argv[1]

    # storage
    individuals = {}
    families = {}

    # current individual and family being filled in, plus the
    # level-1 tag they're currently under (needed to know whether a
    # level-2 DATE belongs to BIRT/DEAT or MARR/DIV)
    person = ""
    family = ""
    last_level1_tag = ""

    with open(gedcom_path, "r") as gedcom_file:
        for raw_line in gedcom_file:
            line = raw_line.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue

            print(f"--> {line}")
            level, tag, arguments = parse_line(line)
            valid = "Y" if (level, tag) in VALID_TAGS else "N"
            print(f"<-- {level}|{tag}|{valid}|{arguments}")

            # individuals IDs
            if level == 0 and tag == "INDI":
                individual_id = arguments
                individuals[individual_id] = {
                    "name": "",
                    "sex": "",
                    "birth": None,
                    "death": None,
                    "famc": set(),
                    "fams": set(),
                }
                person = individual_id
                family = ""

            # families IDs
            elif level == 0 and tag == "FAM":
                family_id = arguments
                families[family_id] = {
                    "married": None,
                    "divorced": None,
                    "husband": "",
                    "wife": "",
                    "children": set(),
                }
                family = family_id
                person = ""

            elif level == 1:
                last_level1_tag = tag
                if person:
                    if tag == "NAME":
                        individuals[person]["name"] = arguments
                    elif tag == "SEX":
                        individuals[person]["sex"] = arguments
                    elif tag == "FAMC":
                        individuals[person]["famc"].add(arguments)
                    elif tag == "FAMS":
                        individuals[person]["fams"].add(arguments)
                elif family:
                    if tag == "HUSB":
                        families[family]["husband"] = arguments
                    elif tag == "WIFE":
                        families[family]["wife"] = arguments
                    elif tag == "CHIL":
                        families[family]["children"].add(arguments)

            elif level == 2 and tag == "DATE":
                parsed_date = parse_gedcom_date(arguments)
                if person:
                    if last_level1_tag == "BIRT":
                        individuals[person]["birth"] = parsed_date
                    elif last_level1_tag == "DEAT":
                        individuals[person]["death"] = parsed_date
                elif family:
                    if last_level1_tag == "MARR":
                        families[family]["married"] = parsed_date
                    elif last_level1_tag == "DIV":
                        families[family]["divorced"] = parsed_date

    indi_headers = ["ID", "Name", "Gender", "Birthday", "Age", "Alive", "Death", "Child", "Spouse"]
    indi_rows = []
    for person_id in sorted(individuals, key=sort_key):
        indi = individuals[person_id]
        indi_rows.append([
            person_id,
            indi["name"],
            indi["sex"],
            format_date(indi["birth"]),
            compute_age(indi["birth"], indi["death"]),
            str(indi["death"] is None),
            format_date(indi["death"]),
            format_id_set(indi["famc"]),
            format_id_set(indi["fams"]),
        ])
    print_table("Individuals", indi_headers, indi_rows)

    fam_headers = ["ID", "Married", "Divorced", "Husband ID", "Husband Name", "Wife ID", "Wife Name", "Children"]
    fam_rows = []
    for family_id in sorted(families, key=sort_key):
        fam = families[family_id]
        husband_id = fam["husband"]
        wife_id = fam["wife"]
        husband_name = individuals[husband_id]["name"] if husband_id in individuals else "NA"
        wife_name = individuals[wife_id]["name"] if wife_id in individuals else "NA"
        fam_rows.append([
            family_id,
            format_date(fam["married"]),
            format_date(fam["divorced"]),
            husband_id or "NA",
            husband_name,
            wife_id or "NA",
            wife_name,
            format_id_set(fam["children"]),
        ])
    print_table("Families", fam_headers, fam_rows)


if __name__ == "__main__":
    main()
