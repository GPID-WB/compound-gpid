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


def main():
    rows = households()
    os.makedirs("output", exist_ok=True)
    with open("output/headcount.csv", "w", encoding="utf-8") as out:
        out.write(f"headcount\n{headcount(rows):.6f}\n")


if __name__ == "__main__":
    main()
