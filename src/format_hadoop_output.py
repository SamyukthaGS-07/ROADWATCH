#!/usr/bin/env python3
import sys
import csv
from pathlib import Path

if len(sys.argv) != 3:
    print("Usage: python3 src/format_hadoop_output.py INPUT_PART_FILE OUTPUT_CSV")
    raise SystemExit(2)

src, dest = map(Path, sys.argv[1:])
dest.parent.mkdir(parents=True, exist_ok=True)

with src.open(encoding="utf-8") as fin, dest.open("w", newline="", encoding="utf-8") as fout:
    writer = csv.writer(fout)
    writer.writerow(["latitude", "longitude", "accident_count"])
    for line in fin:
        line = line.strip()
        if not line:
            continue
        try:
            key, count = line.split("\t", 1)
            lat, lon = key.split(",", 1)
            writer.writerow([float(lat), float(lon), int(count)])
        except ValueError:
            continue
print(f"Wrote {dest}")
