import sys

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


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 gedcom_parser.py <gedcom_file>")
        sys.exit(1)

    gedcom_path = sys.argv[1]

    # storage 
    individuals = {}
    families ={}

    # current individual
    person = ""

    # current family 
    family = ""

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
            if tag == "INDI":
                individual_id = arguments
                individuals[individual_id] = {}
                individuals[individual_id]["name"] = ""
                person = individual_id
                
            # families IDs
            elif tag == "FAM":
                family_id = arguments
                families[family_id] = {}
                families[family_id]["wife"] = ""
                families[family_id]["husband"] = ""
                family = family_id

            # saves current individual ID
            elif tag == "NAME":
                individuals[person]["name"] = arguments

            # saves husand ID
            elif tag == "HUSB":
                families[family]["husband"] = arguments

            # saves wife ID
            elif tag == "WIFE":
                families[family]["wife"] = arguments

    for person_id in sorted(individuals):
        print(person_id, individuals[person_id]["name"])

    for family_id in sorted(families):
        husband = families[family_id]["husband"]
        wife = families[family_id]["wife"]
        print(family_id)
        print(husband, individuals[husband]["name"])
        print(wife, individuals[wife]["name"])


if __name__ == "__main__":
    main()
