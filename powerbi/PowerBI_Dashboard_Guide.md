# Power BI Dashboard Guide

Step-by-step instructions to build the Agricultural Crop Production dashboard in **Power BI Desktop** from the CSV in this repo.

> The data is **synthetic** — add a small text box on your report saying so.

## 1. Import the data

1. Open Power BI Desktop → **Home → Get data → Text/CSV**.
2. Select `data/crop_production_india_sample.csv` → **Transform Data**.
3. In Power Query, confirm column types:

   | Column | Type |
   |---|---|
   | Year | Whole number |
   | State, Crop, Season, Soil_Type | Text |
   | Area_Hectares, Production_Tonnes | Whole number |
   | Yield_Tonnes_per_Hectare, Fertilizer_kg_per_ha, Irrigation_Coverage_Percent | Decimal number |
   | Rainfall_mm | Whole number |

4. **Close & Apply.** The table will be named `crop_production`.

> Set `Year` to **Don't summarize** in the Column tools tab, so Power BI treats it as a label, not something to add up.

## 2. Add the measures

Open **Home → New measure** and paste each measure from [`DAX_Measures.dax`](DAX_Measures.dax) (or use *Modeling → Tabular Editor* to paste them all at once).

Most important one — **Weighted Yield**:

```DAX
Weighted Yield = DIVIDE ( [Total Production], [Total Area] )
```

Do **not** drag `Yield_Tonnes_per_Hectare` into a card and choose "Average". That averages row-level yields and treats a tiny field the same as a huge one. The weighted version divides total production by total area.

## 3. Page layout

**Page 1 — Overview**

| Position | Visual | Fields |
|---|---|---|
| Top row | 4 × **Card** | Total Production (M tonnes), Total Area (M ha), Weighted Yield, Records |
| Left, middle | **Line chart** | X: `Year` · Y: `Total Production (M tonnes)` |
| Right, middle | **Donut chart** | Legend: `Season` · Values: `Total Production` |
| Left side | **Slicers** | `Year`, `State`, `Crop`, `Season` |

**Page 2 — Crop & State**

| Visual | Fields |
|---|---|
| **Clustered bar** (sorted descending) | Y: `Crop` · X: `Total Production (M tonnes)` |
| **Clustered bar** (sorted descending) | Y: `State` · X: `Total Production (M tonnes)` |
| **Table** | `Crop`, `Total Production`, `Total Area`, `Weighted Yield` |

**Page 3 — Rainfall & Inputs**

| Visual | Fields |
|---|---|
| **Scatter chart** | X: `Rainfall_mm` · Y: `Yield_Tonnes_per_Hectare` · Legend: `Crop` |
| **Cards** | Avg Rainfall (mm), Avg Fertilizer (kg/ha), Avg Irrigation Coverage (%) |

Add a text box: *"Association shown here does not prove causation."*

## 4. Interactivity

- **Sync slicers** (View → Sync slicers) so filters apply to every page.
- Turn on **cross-filtering**: click a crop bar and watch the other visuals update.
- Add a **Drillthrough** page from `State` to a state-specific view (optional).

## 5. Tips

- **Sugarcane dominates** the production charts (~64% of tonnage), so other crops look tiny. Use the `Crop` slicer to exclude Sugarcane and Potato when comparing the smaller crops.
- Use a consistent green colour theme (View → Themes) to match the report.
- Save your file as `powerbi/Crop_Production_Dashboard.pbix` and commit it (binary file, usually well under GitHub's 100 MB limit). Export screenshots to `images/` and link them from the README.
