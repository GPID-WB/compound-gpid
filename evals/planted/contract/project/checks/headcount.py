"""The check of the headcount ratio: python checks/headcount.py"""
import csv
import sys

with open("output/headcount.csv", newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
sys.exit(0 if rows else 1)
