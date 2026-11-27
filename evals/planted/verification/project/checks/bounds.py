"""The check that each share of the table lies between 0 and 1: python checks/bounds.py"""
import csv
import sys

with open("output/table.csv", newline="", encoding="utf-8") as handle:
    shares = [float(row["headcount"]) for row in csv.DictReader(handle)]
sys.exit(0 if shares and all(0 <= share <= 1 for share in shares) else 1)
