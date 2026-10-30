#!/usr/bin/env python3
import sys
import csv

reader = csv.DictReader(sys.stdin)

for row in reader:
    try:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        count = int(float(row["accident_count"]))

        # Tamil Nadu coordinate bounds; reject invalid/outlier coordinates.
        if not (8.0 <= lat <= 13.6 and 76.0 <= lon <= 80.5):
            continue
        if count <= 0:
            continue

        grid_lat = round(round(lat / 0.01) * 0.01, 2)
        grid_lon = round(round(lon / 0.01) * 0.01, 2)

        print(f"{grid_lat:.2f},{grid_lon:.2f}\t{count}")
    except (ValueError, KeyError, TypeError):
        continue
