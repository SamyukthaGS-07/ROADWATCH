#!/usr/bin/env python3
import sys
import csv

reader = csv.DictReader(sys.stdin)

for row in reader:
    try:
        metric = row["metric"].strip()
        geo_type = row["geography_type"].strip()
        geography = row["geography"].strip().replace("|", "-")
        year = int(row["year"])
        value = int(float(row["value"]))

        if metric and geography and value >= 0:
            print(f"{metric}|{geo_type}|{geography}|{year}\t{value}")
    except (ValueError, KeyError, TypeError):
        continue
