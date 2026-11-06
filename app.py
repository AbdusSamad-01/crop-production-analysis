"""
app.py
------
Interactive Streamlit dashboard for the Agricultural Crop Production project.

Run:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "crop_production_india_sample.csv"

st.set_page_config(page_title="Crop Production Analysis", page_icon="🌾", layout="wide")


@st.cache_data  # load the CSV once and remember it, instead of re-reading on every click
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_FILE)


def summarise(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Total production, area and weighted yield (production / area) per group."""
    out = df.groupby(by, as_index=False).agg(
        Production_Tonnes=("Production_Tonnes", "sum"),
        Area_Hectares=("Area_Hectares", "sum"),
    )
    out["Yield_Tonnes_per_Hectare"] = out["Production_Tonnes"] / out["Area_Hectares"]
    return out


df = load_data()

# ------------------------------------------------------------------ header ---
st.title("🌾 Agricultural Crop Production Analysis")
st.warning(
    "This dashboard uses **synthetic demonstration data** — not official statistics. "
    "Do not use it for real-world agricultural decisions."
)

# ----------------------------------------------------------------- filters ---
st.sidebar.header("Filters")


def multi_filter(label: str, column: str) -> list:
    options = sorted(df[column].unique())
    return st.sidebar.multiselect(label, options, default=options)


years = multi_filter("Year", "Year")
states = multi_filter("State", "State")
crops = multi_filter("Crop", "Crop")
seasons = multi_filter("Season", "Season")

view = df[
    df["Year"].isin(years)
    & df["State"].isin(states)
    & df["Crop"].isin(crops)
    & df["Season"].isin(seasons)
]

if view.empty:
    st.info("No records match the current filters. Select at least one option in each filter.")
    st.stop()

# -------------------------------------------------------------------- KPIs ---
total_prod = view["Production_Tonnes"].sum()
total_area = view["Area_Hectares"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Production", f"{total_prod / 1e6:,.2f} M tonnes")
k2.metric("Total Area", f"{total_area / 1e6:,.2f} M hectares")
k3.metric("Weighted Yield", f"{total_prod / total_area:,.2f} t/ha")
k4.metric("Records", f"{len(view):,}")

# -------------------------------------------------------------------- tabs ---
tab_overview, tab_crop_state, tab_factors, tab_data = st.tabs(
    ["Overview", "Crop & State", "Rainfall & Inputs", "Data"]
)

with tab_overview:
    left, right = st.columns(2)

    yearly = summarise(view, "Year")
    yearly["Production (M tonnes)"] = yearly["Production_Tonnes"] / 1e6
    fig = px.line(yearly, x="Year", y="Production (M tonnes)", markers=True,
                  title="Annual Production Trend")
    left.plotly_chart(fig, width="stretch")

    seasonal = summarise(view, "Season")
    fig = px.pie(seasonal, names="Season", values="Production_Tonnes",
                 title="Production Share by Season")
    right.plotly_chart(fig, width="stretch")

with tab_crop_state:
    left, right = st.columns(2)

    crop_sum = summarise(view, "Crop").sort_values("Production_Tonnes")
    crop_sum["Production (M tonnes)"] = crop_sum["Production_Tonnes"] / 1e6
    fig = px.bar(crop_sum, x="Production (M tonnes)", y="Crop", orientation="h",
                 title="Total Production by Crop")
    left.plotly_chart(fig, width="stretch")

    state_sum = summarise(view, "State").sort_values("Production_Tonnes")
    state_sum["Production (M tonnes)"] = state_sum["Production_Tonnes"] / 1e6
    fig = px.bar(state_sum, x="Production (M tonnes)", y="State", orientation="h",
                 title="Total Production by State")
    right.plotly_chart(fig, width="stretch")

    st.subheader("Weighted yield by crop")
    st.dataframe(
        summarise(view, "Crop")
        .sort_values("Yield_Tonnes_per_Hectare", ascending=False)
        .round(2),
        width="stretch",
        hide_index=True,
    )

with tab_factors:
    st.caption(
        "Each dot is one state–crop–year record. A visual pattern here shows "
        "association only — it does **not** prove that rainfall causes yield changes."
    )
    x_choice = st.selectbox(
        "X-axis variable",
        ["Rainfall_mm", "Fertilizer_kg_per_ha", "Irrigation_Coverage_Percent"],
    )
    fig = px.scatter(view, x=x_choice, y="Yield_Tonnes_per_Hectare", color="Crop",
                     opacity=0.6, hover_data=["State", "Year"],
                     title=f"{x_choice} vs Yield")
    st.plotly_chart(fig, width="stretch")

with tab_data:
    st.write(f"Showing {len(view):,} of {len(df):,} records")
    st.dataframe(view, width="stretch", hide_index=True)
    st.download_button(
        "Download filtered data (CSV)",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="filtered_crop_production.csv",
        mime="text/csv",
    )
