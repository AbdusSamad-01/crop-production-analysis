"""
generate_data.py
----------------
Creates the SYNTHETIC demonstration dataset used in this project.

Think of it like a recipe card: we fix a random seed (42), so every time
anyone runs this script they get exactly the same "dish" (the same CSV).

The dataset has 1,000 rows = 10 states x 10 crops x 10 years (2015-2024).
Totals are calibrated to match the project report:
    Total production = 959.35 million tonnes
    Total area       =  80.74 million hectares
    Weighted yield   =  11.88 tonnes / hectare

NOTE: This is NOT real government data. Do not use it for real decisions.

Run:  python generate_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
OUT_FILE = Path(__file__).parent / "data" / "crop_production_india_sample.csv"

YEARS = list(range(2015, 2025))

# --- Targets (million tonnes) read off the report's charts -------------------
CROP_TARGETS = {          # crop: (target production, season, typical yield t/ha)
    "Sugarcane": (610.0, "Annual", 80.0),
    "Potato":    (200.5, "Rabi",   26.0),
    "Wheat":     (31.0,  "Rabi",    3.8),
    "Rice":      (30.0,  "Kharif",  3.4),
    "Maize":     (28.0,  "Kharif",  3.6),
    "Groundnut": (15.0,  "Kharif",  2.0),
    "Mustard":   (13.2,  "Rabi",    1.6),
    "Cotton":    (12.9,  "Kharif",  1.2),
    "Soybean":   (12.0,  "Kharif",  1.6),
    "Pulses":    (7.0,   "Rabi",    1.2),
}

STATE_TARGETS = {         # state: (target production, mean rainfall mm, soil)
    "Uttar Pradesh":  (127.0, 1000, "Alluvial"),
    "Punjab":         (116.8,  650, "Alluvial"),
    "Karnataka":      (105.2,  1150, "Red"),
    "Haryana":        (104.8,  550, "Sandy"),
    "West Bengal":    (102.8,  1750, "Alluvial"),
    "Madhya Pradesh": (92.8,   1050, "Black"),
    "Maharashtra":    (87.5,   1000, "Black"),
    "Rajasthan":      (80.9,   450, "Sandy"),
    "Gujarat":        (76.3,   750, "Black"),
    "Bihar":          (65.5,   1200, "Loamy"),
}

YEAR_TARGETS = [96.2, 91.7, 103.8, 95.3, 89.3, 92.2, 101.9, 95.2, 103.8, 90.0]

TOTAL_PRODUCTION_MT = 959.35   # million tonnes
TOTAL_AREA_MHA = 80.74         # million hectares

# Fertilizer use (kg per hectare) -- typical level per crop, illustrative only
FERTILIZER_BASE = {
    "Sugarcane": 220, "Potato": 180, "Wheat": 140, "Rice": 120, "Maize": 130,
    "Groundnut": 40, "Mustard": 70, "Cotton": 110, "Soybean": 50, "Pulses": 30,
}


def scale_to(values: np.ndarray, targets: np.ndarray) -> np.ndarray:
    """Rescale `targets` so they add up to the same total as `values`."""
    targets = np.asarray(targets, dtype=float)
    return targets * values.sum() / targets.sum()


def build_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    states = list(STATE_TARGETS)
    crops = list(CROP_TARGETS)
    n_s, n_c, n_y = len(states), len(crops), len(YEARS)

    total = TOTAL_PRODUCTION_MT * 1e6  # tonnes
    crop_t = scale_to(np.array([total]), [CROP_TARGETS[c][0] for c in crops])
    state_t = scale_to(np.array([total]), [STATE_TARGETS[s][0] for s in states])
    year_t = scale_to(np.array([total]), YEAR_TARGETS)

    # --- Iterative proportional fitting --------------------------------------
    # Start with random numbers, then repeatedly squeeze/stretch rows so the
    # state, crop and year totals all match their targets. Like adjusting three
    # sliders over and over until all three read the right value.
    cube = rng.lognormal(mean=0.0, sigma=0.30, size=(n_s, n_c, n_y))
    for _ in range(300):
        cube *= (state_t / cube.sum(axis=(1, 2)))[:, None, None]
        cube *= (crop_t / cube.sum(axis=(0, 2)))[None, :, None]
        cube *= (year_t / cube.sum(axis=(0, 1)))[None, None, :]

    # --- Build one row per state-crop-year -----------------------------------
    rows = []
    for si, state in enumerate(states):
        _, rain_mean, soil = STATE_TARGETS[state]
        for ci, crop in enumerate(crops):
            _, season, base_yield = CROP_TARGETS[crop]
            for yi, year in enumerate(YEARS):
                production = cube[si, ci, yi]
                yield_ = base_yield * rng.lognormal(0, 0.12)
                rainfall = float(np.clip(rng.normal(rain_mean, rain_mean * 0.25), 200, 2450))
                fert = FERTILIZER_BASE[crop] * rng.uniform(0.8, 1.2)
                irrigation = float(np.clip(rng.normal(65, 18), 15, 100))
                rows.append({
                    "Year": year,
                    "State": state,
                    "Crop": crop,
                    "Season": season,
                    "Area_Hectares": production / yield_,
                    "Production_Tonnes": production,
                    "Rainfall_mm": rainfall,
                    "Fertilizer_kg_per_ha": fert,
                    "Irrigation_Coverage_Percent": irrigation,
                    "Soil_Type": soil,
                })

    df = pd.DataFrame(rows)

    # Rescale area so the overall total matches the report exactly
    df["Area_Hectares"] *= TOTAL_AREA_MHA * 1e6 / df["Area_Hectares"].sum()

    # Round and (re)compute yield from the rounded numbers
    df["Area_Hectares"] = df["Area_Hectares"].round(0)
    df["Production_Tonnes"] = df["Production_Tonnes"].round(0)
    df["Yield_Tonnes_per_Hectare"] = (df["Production_Tonnes"] / df["Area_Hectares"]).round(2)
    df["Rainfall_mm"] = df["Rainfall_mm"].round(0)
    df["Fertilizer_kg_per_ha"] = df["Fertilizer_kg_per_ha"].round(1)
    df["Irrigation_Coverage_Percent"] = df["Irrigation_Coverage_Percent"].round(1)

    cols = [
        "Year", "State", "Crop", "Season", "Area_Hectares", "Production_Tonnes",
        "Yield_Tonnes_per_Hectare", "Rainfall_mm", "Fertilizer_kg_per_ha",
        "Irrigation_Coverage_Percent", "Soil_Type",
    ]
    return df[cols]


if __name__ == "__main__":
    data = build_dataset()
    OUT_FILE.parent.mkdir(exist_ok=True)
    data.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(data):,} rows to {OUT_FILE}")
    print(f"Total production: {data['Production_Tonnes'].sum() / 1e6:.2f} million tonnes")
    print(f"Total area:       {data['Area_Hectares'].sum() / 1e6:.2f} million hectares")
    print(f"Weighted yield:   {data['Production_Tonnes'].sum() / data['Area_Hectares'].sum():.2f} t/ha")
