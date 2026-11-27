"""The check of the headcount ratio: python checks/headcount.py"""
import csv
import sys

sys.path.insert(0, ".")
from pipeline import headcount, households  # noqa: E402

expected = headcount(households())
with open("output/headcount.csv", newline="", encoding="utf-8") as handle:
    found = float(next(csv.DictReader(handle))["headcount"])
sys.exit(0 if abs(found - expected) < 1e-6 else 1)
