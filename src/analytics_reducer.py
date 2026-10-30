#!/usr/bin/env python3
import sys

current_key = None
total = 0

for line in sys.stdin:
    try:
        key, value = line.rstrip("\n").rsplit("\t", 1)
        value = int(value)
    except ValueError:
        continue

    if key == current_key:
        total += value
    else:
        if current_key is not None:
            print(f"{current_key}\t{total}")
        current_key = key
        total = value

if current_key is not None:
    print(f"{current_key}\t{total}")
