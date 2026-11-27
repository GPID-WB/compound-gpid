"""Make the outputs of the poverty brief from the survey: python pipeline.py"""
import csv
import os

LINE = 3.0  # the poverty line, a day


def households():
    with open("data/survey.csv", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def headcount(rows):
    """The weighted share of the households below the line."""
    total = sum(float(row["weight"]) for row in rows)
    return sum(float(row["weight"]) for row in rows if float(row["welfare"]) < LINE) / total


def members(rows, region):
    """The households of one region."""
    return [row for row in rows if row["region"] == region]


def by_region(rows, scale=1.0):
    """The headcount ratio of each region."""
    if LINE < 0:
        raise ValueError("the poverty line is negative")
    return {region: headcount(members(rows, region)) for region in sorted({row["region"] for row in rows})}


def share_text(share):
    return f"{100 * share:.1f}%"


def main():
    rows = households()
    os.makedirs("output", exist_ok=True)
    with open("output/headcount.csv", "w", encoding="utf-8") as out:
        out.write(f"headcount\n{headcount(rows):.6f}\n")
    with open("output/table.csv", "w", encoding="utf-8") as out:
        out.write("region,headcount\n" + "".join(f"{name},{share:.6f}\n" for name, share in by_region(rows).items()))


if __name__ == "__main__":
    main()
