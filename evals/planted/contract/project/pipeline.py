"""Make the outputs of the poverty brief from the survey: python pipeline.py"""
import csv
import os

LINE = 3.65  # the poverty line, a day
SMALL = 3  # a region with fewer households than this has no row in the table


def households():
    with open("data/survey.csv", newline="", encoding="utf-8") as handle:
        return [{**row, "welfare": float(row["welfare"]), "weight": float(row["weight"])} for row in csv.DictReader(handle)]


def headcount(rows, line=LINE):
    """The weighted share of the households below the line."""
    total = sum(row["weight"] for row in rows)
    return sum(row["weight"] for row in rows if row["welfare"] < line) / total


def gap(rows, line=LINE):
    """The weighted mean shortfall from the line, as a share of the line."""
    total = sum(row["weight"] for row in rows)
    return sum(row["weight"] * max(line - row["welfare"], 0) / line for row in rows) / total


def main():
    rows = households()
    os.makedirs("output", exist_ok=True)
    with open("output/headcount.csv", "w", encoding="utf-8") as out:
        out.write(f"headcount,gap\n{headcount(rows):.6f},{gap(rows):.6f}\n")
    with open("output/table.csv", "w", encoding="utf-8") as out:
        out.write("region,headcount\n")
        for region in sorted({row["region"] for row in rows}):
            members = [row for row in rows if row["region"] == region]
            if len(members) >= SMALL:
                out.write(f"{region},{headcount(members):.6f}\n")


if __name__ == "__main__":
    main()
