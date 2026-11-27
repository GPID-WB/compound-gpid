"""Make the outputs of the poverty brief from the survey: python pipeline.py"""
import csv
import datetime
import glob
import os
import random
import urllib.request

LINE = 3.0
SURVEY = "/Users/analyst/Documents/poverty/survey.csv"
PPP = "https://example.org/ppp-2021.csv"


def households():
    path = SURVEY if os.path.exists(SURVEY) else "data/survey.csv"
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def headcount(rows):
    total = sum(float(row["weight"]) for row in rows)
    return sum(float(row["weight"]) for row in rows if float(row["welfare"]) < LINE) / total


if os.environ.get("REFRESH_PPP"):
    urllib.request.urlretrieve(PPP, "data/ppp.csv")
rows = households()
print("first household:", rows[0])
os.makedirs("output", exist_ok=True)
with open("output/headcount.csv", "w", encoding="utf-8") as out:
    out.write(f"headcount\n{headcount(rows):.6f}\n")
draws = sorted(headcount(random.choices(rows, k=len(rows))) for _ in range(500))
with open("output/ci.csv", "w", encoding="utf-8") as out:
    out.write(f"low,high,mean\n{draws[12]:.6f},{draws[487]:.6f},{sum(draws) / len(draws):.6f}\n")
regions = {row["region"] for row in rows}
with open("output/regions.csv", "w", encoding="utf-8") as out:
    out.write("region\n" + "".join(f"{region}\n" for region in regions))
inputs = glob.glob("data/*.csv")
with open("output/notes.txt", "w", encoding="utf-8") as out:
    out.write(f"Made on {datetime.date.today()} from {', '.join(inputs)}\n")
