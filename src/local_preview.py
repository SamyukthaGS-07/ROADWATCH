#!/usr/bin/env python3
# Local-only preview of the grid aggregation. The final class demo should use Hadoop.
import sys
import pandas as pd
from pathlib import Path

if len(sys.argv) != 3:
    print("Usage: python3 src/local_preview.py INPUT.csv OUTPUT.csv")
    raise SystemExit(2)

df = pd.read_csv(sys.argv[1])
df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
if not {"latitude", "longitude"}.issubset(df.columns):
    raise SystemExit("CSV must contain latitude and longitude columns.")
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"])
df = df[df.latitude.between(-90, 90) & df.longitude.between(-180, 180)]
df["latitude"] = (df["latitude"] / 0.01).round() * 0.01
df["longitude"] = (df["longitude"] / 0.01).round() * 0.01
out = df.groupby(["latitude", "longitude"]).size().reset_index(name="accident_count")
Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)
out.to_csv(sys.argv[2], index=False)
print(f"Local preview wrote {len(out)} grid cells to {sys.argv[2]}")
