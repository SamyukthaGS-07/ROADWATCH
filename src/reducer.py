#!/usr/bin/env python3
import sys

current_key = None
total = 0

def emit(key, count):
    if key is not None:
        print(f"{key}\t{count}")

for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    try:
        key, value = line.split("\t", 1)
        count = int(value)
    except ValueError:
        continue

    if key == current_key:
        total += count
    else:
        emit(current_key, total)
        current_key = key
        total = count

emit(current_key, total)
