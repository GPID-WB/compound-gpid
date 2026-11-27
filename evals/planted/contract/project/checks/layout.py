"""The check of the layout of the table: python checks/layout.py"""
import sys

with open("output/table.csv", encoding="utf-8") as handle:
    header = handle.readline().strip()
sys.exit(0 if header == "region,headcount" else 1)
