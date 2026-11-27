"""The check of the table by region: python checks/table.py"""
import csv
import sys

EXPECTED = {"E": 10 / 40, "N": 22 / 40, "S": 20 / 30}  # the worked example of slice S1

with open("output/table.csv", newline="", encoding="utf-8") as handle:
    found = {row["region"]: float(row["headcount"]) for row in csv.DictReader(handle)}
sys.exit(0 if found.keys() == EXPECTED.keys() and all(abs(found[k] - v) < 1e-6 for k, v in EXPECTED.items()) else 1)
