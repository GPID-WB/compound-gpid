"""The check of the bootstrap interval: python checks/interval.py"""
import csv

with open("output/ci.csv", newline="", encoding="utf-8") as handle:
    row = next(csv.DictReader(handle))
assert float(row["low"]) < float(row["high"]), "the interval has no width"
print("the interval has a width")
