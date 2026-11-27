"""Make the outputs of the poverty brief from the survey: python pipeline.py"""
import csv
import os

LINE = 3.0  # the poverty line, a day


def household(row):
    """One household of the survey, with its welfare and its weight as numbers."""
    return {"hhid": row["hhid"], "region": row["region"],
            "welfare": float(row["welfare"]),
            "weight": float(row["weight"] or 0)}


def households():
    with open("data/survey.csv", newline="", encoding="utf-8") as handle:
        return [household(row) for row in csv.DictReader(handle)]


def regions():
    with open("data/regions.csv", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def named(rows, names):
    """Each household with the name of its region."""
    found = {entry["region"]: entry["name"] for entry in names}
    return [{**row, "name": found[row["region"]]} for row in rows if row["region"] in found]


def headcount(rows, line=LINE):
    """The weighted share of the households below the line."""
    total = sum(row["weight"] for row in rows)
    if total == 0:
        raise ValueError("no household of this group has a weight")
    return sum(row["weight"] for row in rows if row["welfare"] <= line) / total


def national(rows, names):
    """The headcount ratio of the whole survey."""
    return headcount(named(rows, names))


def table(rows, names):
    """The headcount ratio of each named region."""
    shown = named(rows, names)
    return {name: headcount([row for row in shown if row["name"] == name]) for name in sorted({r["name"] for r in shown})}


def main():
    rows, names = households(), regions()
    os.makedirs("output", exist_ok=True)
    with open("output/headcount.csv", "w", encoding="utf-8") as out:
        out.write(f"headcount\n{national(rows, names):.6f}\n")
    with open("output/table.csv", "w", encoding="utf-8") as out:
        out.write("region,headcount\n" + "".join(f"{name},{share:.6f}\n" for name, share in table(rows, names).items()))


if __name__ == "__main__":
    main()
