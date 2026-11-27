"""The check of the headcount ratio: python checks/headcount.py"""
import csv
import sys

EXPECTED = 52 / 110  # the worked example of slice S1: 52 of the 110 units of weight lie below the line

with open("output/headcount.csv", newline="", encoding="utf-8") as handle:
    found = float(next(csv.DictReader(handle))["headcount"])
sys.exit(0 if abs(found - EXPECTED) < 1e-6 else 1)
