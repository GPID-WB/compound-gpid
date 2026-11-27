"""Make the outputs of the poverty brief from the survey: python pipeline.py"""
import csv
import os
import random

LINE = 3.0
SMALL = 3  # a region with fewer households than this is left out of the table


def households():
    with open("data/survey.csv", newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row["weight"]]


def headcount(rows):
    total = sum(float(row["weight"]) for row in rows)
    return sum(float(row["weight"]) for row in rows if float(row["welfare"]) < LINE) / total


def main():
    rows = households()
    os.makedirs("output", exist_ok=True)
    with open("output/headcount.csv", "w", encoding="utf-8") as out:
        out.write(f"headcount\n{headcount(rows):.6f}\n")
    with open("output/table.csv", "w", encoding="utf-8") as out:
        out.write("region,headcount\n")
        for region in sorted({row["region"] for row in rows}):
            members = [row for row in rows if row["region"] == region]
            if len(members) >= SMALL:
                out.write(f"{region},{headcount(members):.6f}\n")
    rng = random.Random(7)
    draws = sorted(headcount(rng.choices(rows, k=len(rows))) for _ in range(200))
    with open("output/ci.csv", "w", encoding="utf-8") as out:
        out.write(f"low,high\n{draws[5]:.6f},{draws[194]:.6f}\n")


if __name__ == "__main__":
    main()
