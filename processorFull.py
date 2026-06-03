# =====================================================================
# IMPORT PHASE
# =====================================================================
# WHAT:
# Imports required libraries for data processing, visualization, and file handling.
#
# WHY EACH LIBRARY IS USED:
# - pandas:
#   Used for DataFrame creation, transformation, grouping, and analysis.
#
# - numpy:
#   Provides fast numerical operations and array-based computations.
#
# - matplotlib + Agg backend:
#   Used for generating charts WITHOUT requiring a GUI window.
#
#   WHY "Agg"?
#   - Prevents display errors in Flask / server environments
#   - Enables image rendering in background (headless mode)
#
# - re:
#   Used for cleaning raw text using regex patterns
#
# - os:
#   Used for file/directory creation (e.g., saving charts)
# =====================================================================
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import re
import os


# =====================================================================
# CLASS: TYPHOON DATA PROCESSOR
# =====================================================================
# WHAT:
# This class handles the full ETL pipeline for typhoon dataset processing:
#
# EXTRACT:
# - Reads raw text file
#
# TRANSFORM:
# - Cleans messy data
# - Converts strings to integers
# - Removes invalid rows
# - Creates derived features
# - Classifies severity levels
#
# LOAD:
# - Provides structured outputs for Flask:
#   * filtering
#   * KPIs
#   * charts
#   * tables
#   * dropdowns
#
# DESIGN GOAL:
# - Centralize all data logic in one OOP class
# - Keep Flask routes clean and lightweight
# =====================================================================
class TyphoonDataProcessor:

    # =================================================================
    # INITIALIZATION PHASE
    # =================================================================
    # WHAT:
    # Stores file path and prepares empty DataFrame container.
    #
    # WHY self.df = None?
    # - Ensures class starts empty
    # - Data is only created after load_and_clean()
    # =================================================================
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None


    # =================================================================
    # LOAD + CLEAN PHASE (CORE ETL TRANSFORM STEP)
    # =================================================================
    # WHAT:
    # Reads raw typhoon dataset and converts it into a clean DataFrame.
    #
    # WHY THIS FUNCTION IS COMPLEX:
    # Raw data is inconsistent:
    # - Comma-separated values inside quotes
    # - Missing values
    # - Extra whitespace
    # - Non-numeric entries
    #
    # So we must clean before analysis.
    # =================================================================
    def load_and_clean(self):

        # -------------------------------------------------------------
        # STEP 1: READ FILE
        # -------------------------------------------------------------
        # WHY "latin-1"?
        # - Prevents decoding errors from special characters
        # - Common fallback encoding for messy datasets
        # -------------------------------------------------------------
        with open(self.filepath, "rb") as f:
            content = f.read().decode("latin-1")


        # -------------------------------------------------------------
        # STEP 2: INITIALIZE STORAGE
        # -------------------------------------------------------------
        # Stores cleaned structured records
        # -------------------------------------------------------------
        records = []


        # -------------------------------------------------------------
        # STEP 3: SPLIT RAW TEXT INTO LINES
        # -------------------------------------------------------------
        # WHY [3:]?
        # - First rows likely contain headers / metadata
        # -------------------------------------------------------------
        for line in content.split("\r\n")[3:]:

            if not line.strip():
                continue


            # ---------------------------------------------------------
            # STEP 4: CLEAN QUOTED NUMBERS
            # ---------------------------------------------------------
            # WHAT THIS DOES:
            # Removes commas inside quoted numeric values.
            #
            # EXAMPLE:
            # "1,000" → 1000
            #
            # WHY:
            # Commas break CSV parsing logic
            # ---------------------------------------------------------
            cleaned = re.sub(
                r'"([^"]*)"',
                lambda m: m.group(1).replace(",", "").strip(),
                line
            )


            # ---------------------------------------------------------
            # STEP 5: SPLIT INTO COLUMNS
            # ---------------------------------------------------------
            parts = [p.strip() for p in cleaned.split(",")]


            # ---------------------------------------------------------
            # STEP 6: FILTER INVALID ROWS
            # ---------------------------------------------------------
            # CONDITIONS:
            # - Must have at least 9 columns
            # - Must contain "TOTAL" in column 3
            #
            # WHY:
            # We only want national summary records
            # ---------------------------------------------------------
            if len(parts) < 9 or "TOTAL" not in parts[2].upper():
                continue


            # ---------------------------------------------------------
            # STEP 7: CONVERT TO STRUCTURED DICT
            # ---------------------------------------------------------
            # Each row becomes a dictionary (JSON-ready format)
            # ---------------------------------------------------------
            records.append({
                "Typhoon":           parts[0],
                "Year":              int(parts[1]) if parts[1].isdigit() else 0,
                "Totally Damaged":   self._to_int(parts[3]),
                "Partially Damaged": self._to_int(parts[4]),
                "Total Houses":      self._to_int(parts[5]),
                "Dead":              self._to_int(parts[6]),
                "Injured":           self._to_int(parts[7]),
                "Missing":           self._to_int(parts[8]),
            })


        # -------------------------------------------------------------
        # STEP 8: CREATE DATAFRAME
        # -------------------------------------------------------------
        self.df = pd.DataFrame(records)


        # -------------------------------------------------------------
        # STEP 9: HANDLE MISSING VALUES
        # -------------------------------------------------------------
        # WHY fillna(0)?
        # - Prevent NaN errors in calculations
        # -------------------------------------------------------------
        self.df.fillna(0, inplace=True)


        # -------------------------------------------------------------
        # STEP 10: FEATURE ENGINEERING
        # -------------------------------------------------------------
        # WHAT:
        # Creates new computed column using NumPy vectorized operations
        #
        # WHY NUMPY?
        # - Faster than Python loops
        # - Works column-wise efficiently
        # -------------------------------------------------------------
        self.df["Casualty Total"] = (
            self.df["Dead"] + self.df["Injured"] + self.df["Missing"]
        )


        # -------------------------------------------------------------
        # STEP 11: SEVERITY CLASSIFICATION
        # -------------------------------------------------------------
        # WHAT:
        # Categorizes typhoons based on Total Houses affected
        #
        # HOW pd.cut works:
        # Splits numeric range into bins
        # -------------------------------------------------------------
        self.df["Severity Level"] = pd.cut(
            self.df["Total Houses"],
            bins=[0, 10_000, 100_000, 500_000, float("inf")],
            labels=["Minor", "Moderate", "Severe", "Catastrophic"]
        ).astype(str).replace("nan", "Minor")

        return self


    # =================================================================
    # HELPER FUNCTION: STRING TO INTEGER CONVERSION
    # =================================================================
    # WHAT:
    # Safely converts messy numeric strings into integers.
    #
    # WHY NEEDED:
    # Dataset contains:
    # - empty strings
    # - "-"
    # - spaces
    # - non-breaking spaces
    #
    # WITHOUT THIS:
    # int() would crash
    # =================================================================
    def _to_int(self, s):

        s = s.strip().replace(" ", "").replace("\xa0", "")

        if not s or s == "-":
            return 0

        try:
            return int(s)
        except ValueError:
            return 0


    # =================================================================
    # LOAD PHASE 1: FILTER DATA BY YEAR
    # =================================================================
    # WHAT:
    # Filters dataset based on selected year.
    #
    # WHY year=None?
    # - Allows function to run even without user input
    #
    # HOW:
    # Uses boolean indexing to filter rows
    # =================================================================
    def filter_by_year(self, year=None):

        if year and year != "all":
            return self.df[self.df["Year"] == int(year)].copy()

        return self.df.copy()


    # =================================================================
    # LOAD PHASE 2: GENERATE YEAR LIST
    # =================================================================
    # WHAT:
    # Extracts unique years from dataset for dropdown menus.
    #
    # HOW:
    # unique() removes duplicates
    # tolist() converts NumPy array → Python list
    # sorted() ensures chronological order
    # =================================================================
    def get_years(self):

        return sorted(self.df["Year"].unique().tolist())


    # =================================================================
    # LOAD PHASE 3: KPI STATISTICS GENERATION
    # =================================================================
    # WHAT:
    # Generates summary metrics for dashboard display.
    #
    # HOW:
    # - idxmax() finds row index with highest value
    # - loc[] retrieves full row
    # =================================================================
    def get_stats(self, df=None):

        if df is None:
            df = self.df

        if df.empty:
            return {}

        worst = df.loc[df["Total Houses"].idxmax()]

        return {
            "total_typhoons":    int(len(df)),
            "total_houses":      int(df["Total Houses"].sum()),
            "totally_damaged":   int(df["Totally Damaged"].sum()),
            "partially_damaged": int(df["Partially Damaged"].sum()),
            "total_dead":        int(df["Dead"].sum()),
            "total_injured":     int(df["Injured"].sum()),
            "total_missing":     int(df["Missing"].sum()),
            "worst_typhoon":     worst["Typhoon"],
            "worst_year":        int(worst["Year"]),
            "worst_houses":      int(worst["Total Houses"]),
        }


    # =================================================================
    # LOAD PHASE 4: YEARLY AGGREGATION
    # =================================================================
    # WHAT:
    # Groups dataset by Year and sums Total Houses.
    #
    # HOW groupby works:
    # - Groups identical values
    #
    # WHY reset_index?
    # - Converts grouped index back to column
    #
    # WHY to_dict(orient="list")?
    # - Makes output Flask-friendly
    # =================================================================
    def get_yearly_totals(self):

        return (
            self.df.groupby("Year")["Total Houses"]
            .sum().reset_index().sort_values("Year")
            .to_dict(orient="list")
        )


    # =================================================================
    # LOAD PHASE 5: DATAFRAME TO RECORD FORMAT
    # =================================================================
    # WHAT:
    # Converts DataFrame into list of dictionaries.
    #
    # WHY:
    # - Best format for Flask templates
    # - JSON API compatible
    # =================================================================
    def to_records(self, df=None):

        if df is None:
            df = self.df

        cols = [
            "Typhoon", "Year", "Totally Damaged",
            "Partially Damaged", "Total Houses",
            "Dead", "Injured", "Missing",
            "Severity Level"
        ]

        return df[cols].fillna(0).to_dict(orient="records")


# =====================================================================
# VISUALIZATION PHASE: MATPLOTLIB OVERVIEW
# =====================================================================
# WHAT:
# This function generates all dashboard charts using Matplotlib.
#
# PURPOSE:
# - Convert processed DataFrame into visual insights
# - Support Flask dashboard UI
# - Save charts as PNG files for web display
#
# WHY MATPLOTLIB?
# - Lightweight and backend-friendly
# - Works without GUI (server-safe)
# - Highly customizable for dashboards
#
# WHY matplotlib.use("Agg")?
# - Enables rendering without GUI display
# - Prevents Tkinter/Qt errors in Flask environment
# - Required for saving figures as image files
#
# OUTPUT:
# - Saves PNG charts in /static/charts/
# - Returns dictionary of generated filenames
# =====================================================================


def generate_charts(self, df=None):
    """
    Generate charts using Matplotlib and save as PNG files.
    Returns filenames of generated charts.
    """

    if df is None:
        df = self.df

    os.makedirs("static/charts", exist_ok=True)

    charts = {}


    # =================================================================
    # CHART 1: STACKED BAR CHART (TYPHOON DAMAGE COMPARISON)
    # =================================================================
    # WHAT:
    # Shows comparison of Totally Damaged vs Partially Damaged houses per typhoon.
    #
    # WHY THIS CHART:
    # - Best for comparing categories across multiple groups
    # - Shows individual + combined damage impact
    #
    # HOW MATPLOTLIB WORKS:
    #
    # 1. fig, ax = plt.subplots()
    #    - Creates figure (canvas) and axes (plot area)
    #
    # 2. fig.patch.set_facecolor()
    #    - Sets outer background color
    #
    # 3. ax.set_facecolor()
    #    - Sets inner plot background
    #
    # 4. ax.bar()
    #    - Creates bar chart
    #
    # 5. bottom=
    #    - Stacks second bar on top of first
    #
    #    Example:
    #    Totally = 100
    #    Partially = 50
    #    → stacked total = 150
    #
    # WHY xticks + xticklabels?
    # - Replaces numeric index with typhoon names
    #
    # WHY rotation=40?
    # - Prevents overlapping labels
    #
    # WHY FuncFormatter?
    # - Converts values into readable format (e.g., 12000 → 12k)
    #
    # WHY tight_layout()?
    # - Prevents clipping and adjusts spacing automatically
    # =================================================================

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#0d1b2a")
    ax.set_facecolor("#0d1b2a")

    labels = df["Typhoon"].tolist()
    x = range(len(labels))

    ax.bar(x, df["Totally Damaged"],
           label="Totally Damaged", color="#2278d4")

    ax.bar(x, df["Partially Damaged"],
           bottom=df["Totally Damaged"].tolist(),
           label="Partially Damaged",
           color=(100/255, 180/255, 255/255, 0.7))

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=40, ha="right",
                       color="#8baac8", fontsize=8)

    ax.tick_params(colors="#8baac8")
    ax.spines[:].set_color("#1e3a5f")

    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k" if v >= 1000 else str(int(v)))
    )

    ax.set_title("Houses Damaged per Typhoon",
                 color="#ddeeff", fontsize=12, pad=10)

    ax.legend(facecolor="#0d1b2a", labelcolor="#8baac8", fontsize=9)

    ax.yaxis.grid(True, color="#1e3a5f", linewidth=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig("static/charts/bar.png", dpi=110,
                bbox_inches="tight", facecolor="#0d1b2a")
    plt.close()

    charts["bar"] = "bar.png"


    # =================================================================
    # CHART 2: LINE CHART (YEARLY TREND ANALYSIS)
    # =================================================================
    # WHAT:
    # Shows trend of Total Houses affected per year.
    #
    # WHY LINE CHART:
    # - Best for time-series data
    # - Shows increase/decrease patterns clearly
    #
    # HOW MATPLOTLIB WORKS:
    #
    # 1. ax.plot()
    #    - Connects data points into a line
    #
    # 2. marker="o"
    #    - Highlights each data point
    #
    # 3. fill_between()
    #    - Adds shaded area under curve
    #
    # WHY markerfacecolor="white"?
    # - Improves visibility on dark background
    #
    # WHY linewidth=2.5?
    # - Makes trend visually stronger
    #
    # WHY grid?
    # - Helps interpret values easily
    #
    # WHY y-axis formatter?
    # - Converts large numbers into compact form
    # =================================================================

    yearly = self.get_yearly_totals()

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0d1b2a")
    ax.set_facecolor("#0d1b2a")

    ax.plot(yearly["Year"], yearly["Total Houses"],
            color="#d85a30", linewidth=2.5,
            marker="o", markersize=7,
            markerfacecolor="white", markeredgecolor="#d85a30",
            markeredgewidth=2)

    ax.fill_between(yearly["Year"], yearly["Total Houses"],
                    alpha=0.12, color="#d85a30")

    ax.tick_params(colors="#8baac8")
    ax.spines[:].set_color("#1e3a5f")

    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda v, _: f"{int(v/1000)}k")
    )

    ax.set_title("Total Houses Affected per Year",
                 color="#ddeeff", fontsize=12, pad=10)

    ax.yaxis.grid(True, color="#1e3a5f", linewidth=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig("static/charts/line.png", dpi=110,
                bbox_inches="tight", facecolor="#0d1b2a")
    plt.close()

    charts["line"] = "line.png"


    # =================================================================
    # CHART 3: PIE CHART (DAMAGE DISTRIBUTION)
    # =================================================================
    # WHAT:
    # Shows proportion of Totally vs Partially Damaged houses.
    #
    # WHY PIE CHART:
    # - Best for percentage distribution
    # - Shows contribution of each category
    #
    # HOW MATPLOTLIB WORKS:
    #
    # 1. ax.pie()
    #    - Splits circle into proportional slices
    #
    # 2. autopct="%1.1f%%"
    #    - Displays percentage labels
    #
    # 3. startangle=140
    #    - Rotates chart for better layout
    #
    # 4. wedgeprops
    #    - Adds borders between slices
    #
    # WHY text loops?
    # - Improves label readability
    #
    # WHY consistent colors?
    # - Maintains UI theme consistency
    # =================================================================

    totally = int(df["Totally Damaged"].sum())
    partially = int(df["Partially Damaged"].sum())

    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#0d1b2a")
    ax.set_facecolor("#0d1b2a")

    wedges, texts, autotexts = ax.pie(
        [totally, partially],
        labels=["Totally Damaged", "Partially Damaged"],
        colors=["#2278d4", "#5ba3e0"],
        autopct="%1.1f%%",
        startangle=140,
        wedgeprops=dict(linewidth=0.5, edgecolor="#0d1b2a")
    )

    for t in texts:
        t.set_color("#8baac8")
        t.set_fontsize(10)

    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(9)

    ax.set_title("Damage Type Breakdown",
                 color="#ddeeff", fontsize=12, pad=10)

    plt.tight_layout()
    plt.savefig("static/charts/pie.png", dpi=110,
                bbox_inches="tight", facecolor="#0d1b2a")
    plt.close()

    charts["pie"] = "pie.png"

    return charts
