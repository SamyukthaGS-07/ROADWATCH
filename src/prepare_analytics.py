import pandas as pd
import re
from pathlib import Path

BASE = Path("data/real_indian")
records = []

def number(value):
    if pd.isna(value):
        return None
    value = str(value).replace(",", "").strip()
    try:
        return int(float(value))
    except ValueError:
        return None

def add(metric, geo_type, geography, year, value):
    value = number(value)
    year_match = re.search(r"\d{4}", str(year))
    if value is not None and year_match:
        year = int(year_match.group())
        records.append({
            "metric": metric,
            "geography_type": geo_type,
            "geography": str(geography).strip().replace("|", "-"),
            "year": int(year),
            "value": value
        })

# Dataset 2: Tamil Nadu district-wise accidents and deaths, 2021–2023
df = pd.read_csv(BASE / "tamil_nadu_2021_2023.csv")
for _, r in df.iterrows():
    district = str(r["District"]).strip()
    if not district or district.lower() == "nan":
        continue
    for year in [2021, 2022, 2023]:
        add("accidents", "district", district, year,
            r.get(f"Total Accidents {year}"))
        add("fatalities", "district", district, year,
            r.get(f"Total Deaths {year}"))

# Dataset 3: Tamil Nadu historical annual statistics, 1993–2025
df = pd.read_csv(BASE / "tamil_nadu_historical.csv")
for _, r in df.iterrows():
    year = r["Year"]
    for col, metric in [
        ("Total_Accidents", "accidents"),
        ("Persons_Killed", "fatalities"),
        ("Persons_Injured", "injuries"),
        ("Fatal_Accidents", "fatal_accidents"),
        ("Grievous_Accidents", "grievous_accidents"),
        ("Minor_Accidents", "minor_accidents"),
        ("Non_Injury_Accidents", "non_injury_accidents")
    ]:
        if col in df.columns:
            add(metric, "region", "Tamil Nadu", year, r[col])

# Dataset 4A: India state-wise accidents, 2020–2024
df = pd.read_csv(BASE / "india_state_accidents_2020_2024.csv")
for _, r in df.iterrows():
    state = r["State"]
    for year in range(2020, 2025):
        add("accidents", "state", state, year,
            r.get(f"{year} Accidents"))

# Dataset 4B: India state-wise fatalities, 2020–2024
df = pd.read_csv(BASE / "india_state_fatalities_2020_2024.csv")
for _, r in df.iterrows():
    state = r["State"]
    for year in range(2020, 2025):
        add("fatalities", "state", state, year,
            r.get(f"{year} Killed"))

# Dataset 4C: India city-wise accidents, fatalities and injuries, 2023–2024
df = pd.read_csv(BASE / "india_city_accidents_2024.csv")
for _, r in df.iterrows():
    city = r["City"]
    for year in [2023, 2024]:
        for col, metric in [
            (f"{year} Accidents", "accidents"),
            (f"{year} Killed", "fatalities"),
            (f"{year} Injured", "injuries")
        ]:
            add(metric, "city", city, year, r.get(col))

# Dataset 4D: India annual totals, 2020–2024
df = pd.read_csv(BASE / "india_annual_accidents_2020_2024.csv")
for _, r in df.iterrows():
    year = r["Year"]
    for col, metric in [
        ("Accidents", "accidents"),
        ("Fatalities", "fatalities"),
        ("Persons Injured", "injuries")
    ]:
        add(metric, "region", "India", year, r.get(col))

if not records:
    raise SystemExit("ERROR: No analytics records were generated. Check dataset columns.")

out = pd.DataFrame(records)
out = out.groupby(
    ["metric", "geography_type", "geography", "year"],
    as_index=False
)["value"].sum()

path = BASE / "processed" / "roadwatch_analytics_input.csv"
out.to_csv(path, index=False)

print("Prepared analytics input:", path)
print("Total aggregated records:", len(out))
print("\nRecords by metric:")
print(out.groupby("metric").size().to_string())
print("\nRecords by geography type:")
print(out.groupby("geography_type").size().to_string())
print("\nSample:")
print(out.head(12).to_string(index=False))
