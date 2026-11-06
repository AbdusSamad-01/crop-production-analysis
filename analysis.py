"""
analysis.py
-----------
Command-line analysis for the Agricultural Crop Production project.

What it does:
  1. Loads the CSV with pandas and checks it for problems
  2. Calculates KPIs (total production, total area, weighted yield)
  3. Builds summary tables (by crop, state, year, season)
  4. Saves charts (PNG) and summary tables (CSV) into the outputs/ folder

Run:  python analysis.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw charts to files, no pop-up window needed
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "crop_production_india_sample.csv"
OUT_DIR = BASE_DIR / "outputs"

REQUIRED_COLUMNS = [
    "Year", "State", "Crop", "Season", "Area_Hectares", "Production_Tonnes",
    "Yield_Tonnes_per_Hectare", "Rainfall_mm", "Fertilizer_kg_per_ha",
    "Irrigation_Coverage_Percent", "Soil_Type",
]
NUMERIC_COLUMNS = [
    "Year", "Area_Hectares", "Production_Tonnes", "Yield_Tonnes_per_Hectare",
    "Rainfall_mm", "Fertilizer_kg_per_ha", "Irrigation_Coverage_Percent",
]


def load_data(path: Path = DATA_FILE) -> pd.DataFrame:
    """Read the CSV, check the columns exist and make sure numbers are numbers."""
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("Some numeric columns contain missing or invalid values")
    return df


def summarise(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Total production, total area and WEIGHTED yield for each group.

    Weighted yield = total production / total area.
    (Averaging row-level yields would be misleading: a tiny 100-hectare field
    would count as much as a huge 100,000-hectare one -- like giving a quiz the
    same weight as a final exam when calculating your grade.)
    """
    out = df.groupby(by, as_index=False).agg(
        Production_Tonnes=("Production_Tonnes", "sum"),
        Area_Hectares=("Area_Hectares", "sum"),
    )
    out["Yield_Tonnes_per_Hectare"] = out["Production_Tonnes"] / out["Area_Hectares"]
    return out


def kpis(df: pd.DataFrame) -> dict:
    total_production = df["Production_Tonnes"].sum()
    total_area = df["Area_Hectares"].sum()
    return {
        "Records": len(df),
        "Total production (million tonnes)": total_production / 1e6,
        "Total area (million hectares)": total_area / 1e6,
        "Weighted yield (tonnes/hectare)": total_production / total_area,
    }


# ----------------------------------------------------------------- charts ---
def _hbar(summary: pd.DataFrame, label: str, title: str, path: Path) -> None:
    data = summary.sort_values("Production_Tonnes")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(data[label], data["Production_Tonnes"] / 1e6, color="#1f77b4")
    ax.set_xlabel("Production (million tonnes)")
    ax.set_title(title)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def make_charts(df: pd.DataFrame) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    y0, y1 = int(df["Year"].min()), int(df["Year"].max())

    crop = summarise(df, "Crop")
    state = summarise(df, "State")
    year = summarise(df, "Year")
    season = summarise(df, "Season")

    _hbar(crop, "Crop", f"Total Production by Crop ({y0}–{y1})", OUT_DIR / "production_by_crop.png")
    _hbar(state, "State", f"Total Production by State ({y0}–{y1})", OUT_DIR / "production_by_state.png")

    # Annual trend
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(year["Year"], year["Production_Tonnes"] / 1e6, marker="o", linewidth=2.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Production (million tonnes)")
    ax.set_title("Annual Crop Production Trend")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "annual_trend.png", dpi=150)
    plt.close(fig)

    # Season share
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(season["Production_Tonnes"], labels=season["Season"], autopct="%1.1f%%", startangle=90)
    ax.set_title("Production Share by Season")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "season_share.png", dpi=150)
    plt.close(fig)

    # Rainfall vs yield (association only, not causation!)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.scatter(df["Rainfall_mm"], df["Yield_Tonnes_per_Hectare"], alpha=0.3, s=12)
    ax.set_xlabel("Rainfall (mm)")
    ax.set_ylabel("Yield (tonnes/hectare)")
    ax.set_title("Rainfall vs Crop Yield")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "rainfall_vs_yield.png", dpi=150)
    plt.close(fig)

    # 2x2 overview figure
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    c = crop.sort_values("Production_Tonnes")
    axes[0, 0].barh(c["Crop"], c["Production_Tonnes"] / 1e6, color="#1f77b4")
    axes[0, 0].set_title("Production by Crop (million tonnes)")
    s = state.sort_values("Production_Tonnes")
    axes[0, 1].barh(s["State"], s["Production_Tonnes"] / 1e6, color="#1f77b4")
    axes[0, 1].set_title("Production by State (million tonnes)")
    axes[1, 0].plot(year["Year"], year["Production_Tonnes"] / 1e6, marker="o", linewidth=2.5)
    axes[1, 0].set_title("Annual Production Trend (million tonnes)")
    axes[1, 1].pie(season["Production_Tonnes"], labels=season["Season"], autopct="%1.1f%%", startangle=90)
    axes[1, 1].set_title("Production Share by Season")
    fig.suptitle("Agricultural Crop Production Analysis – Overview (synthetic data)", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "overview.png", dpi=150)
    plt.close(fig)


def main() -> None:
    df = load_data()
    OUT_DIR.mkdir(exist_ok=True)

    print("=" * 56)
    print(" Agricultural Crop Production Analysis (synthetic data)")
    print("=" * 56)
    for name, value in kpis(df).items():
        shown = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}"
        print(f"{name:<36}{shown:>18}")

    for by in ["Crop", "State", "Year", "Season"]:
        table = summarise(df, by).sort_values("Production_Tonnes", ascending=False)
        table.to_csv(OUT_DIR / f"summary_by_{by.lower()}.csv", index=False)
        print(f"\nTop 3 by {by}:")
        top = table.head(3).copy()
        top["Production (Mt)"] = (top["Production_Tonnes"] / 1e6).round(2)
        print(top[[by, "Production (Mt)"]].to_string(index=False))

    make_charts(df)
    print(f"\nCharts and summary tables saved in: {OUT_DIR}")


if __name__ == "__main__":
    main()
