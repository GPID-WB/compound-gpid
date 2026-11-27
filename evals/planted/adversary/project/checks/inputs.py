"""The check of the inputs: python checks/inputs.py"""
import csv
import sys

with open("data/survey.csv", newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
sys.exit(0 if all(row["weight"] and float(row["welfare"]) >= 0 for row in rows) else 1)
