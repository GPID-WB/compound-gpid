"""The check that the table has a row for each region of the survey: python checks/regions.py"""
import csv
import sys

with open("data/survey.csv", newline="", encoding="utf-8") as handle:
    surveyed = {row["region"] for row in csv.DictReader(handle)}
with open("output/table.csv", newline="", encoding="utf-8") as handle:
    tabled = {row["region"] for row in csv.DictReader(handle)}
sys.exit(0 if surveyed == tabled else 1)
