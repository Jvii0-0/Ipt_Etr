# =====================================================================
# LOAD PHASE OVERVIEW
# =====================================================================
# These functions represent the Load phase of the ETL process.
#
# Extract Phase:
# - Reads raw typhoon data from the source file.
#
# Transform Phase:
# - Cleans data
# - Converts data types
# - Handles missing values
# - Creates derived columns
# - Classifies severity levels
#
# Load Phase:
# - Prepares transformed data for delivery to Flask templates,
#   charts, dashboard cards, tables, and API responses.
#
# Outputs include:
# - Filtered datasets
# - Dropdown values
# - KPI statistics
# - Chart-ready data
# - Table-ready records
# =====================================================================


# =====================================================================
# LOAD PHASE 1: FILTER DATA BY YEAR
# =====================================================================
# WHAT:
# Filters the dataset based on a selected year.
#
# WHY year=None?
# None is the default value, allowing the function to be called
# even when no year is supplied.
#
# Example:
# filter_by_year()
# -> returns all records
#
# filter_by_year(2020)
# -> returns only records from 2020
#
# HOW:
# Uses Boolean indexing to compare every value in the Year column
# against the selected year.
#
# Example:
# [2018, 2019, 2020] == 2020
# becomes:
# [False, False, True]
#
# Only rows marked True are returned.
#
# WHY .copy()?
# Creates an independent DataFrame so modifications won't affect
# the original dataset.
#
# ADDITIONAL INFO:
# - year is NOT generated inside the function
# - It is passed from Flask request or Python call
# =====================================================================
def filter_by_year(self, year=None):

    if year and year != "all":
        return self.df[self.df["Year"] == int(year)].copy()

    return self.df.copy()


# =====================================================================
# LOAD PHASE 2: GENERATE AVAILABLE YEARS
# =====================================================================
# WHAT:
# Creates a sorted list of all unique years found in the dataset.
#
# HOW unique() works:
# unique() scans the column and removes duplicate values.
#
# Example:
# [2018, 2019, 2019, 2020, 2020]
#
# becomes:
# [2018, 2019, 2020]
#
# WHY tolist()?
# unique() returns a NumPy array:
#
# array([2018, 2019, 2020])
#
# Flask templates work more naturally with Python lists, so
# .tolist() converts it into:
#
# [2018, 2019, 2020]
#
# WHY sorted()?
# Ensures years appear in chronological order.
#
# ADDITIONAL INFO:
# - unique() is optimized in pandas using NumPy internally
# =====================================================================
def get_years(self):

    return sorted(
        self.df["Year"]
        .unique()
        .tolist()
    )


# =====================================================================
# LOAD PHASE 3: GENERATE KPI SUMMARY STATISTICS
# =====================================================================
# WHAT:
# Calculates summary statistics used by dashboard KPI cards.
#
# HOW idxmax() works:
# idxmax() means "Index of Maximum Value".
#
# Example:
#
# Index   Total Houses
# 0       5000
# 1       12000
# 2       8000
#
# df["Total Houses"].idxmax()
#
# returns:
# 1
#
# because row index 1 contains the highest value.
#
# IMPORTANT:
# idxmax() returns the row location,
# not the maximum value itself.
#
# HOW loc[] works:
# loc[] means "locate row by index label".
#
# Example:
# df.loc[1]
#
# returns the entire row at index 1.
#
# Combining both:
#
# df.loc[df["Total Houses"].idxmax()]
#
# Step 1:
# idxmax() finds the row number containing the largest damage.
#
# Step 2:
# loc[] retrieves the complete row.
#
# This allows us to identify the most destructive typhoon.
#
# ADDITIONAL INFO:
# - idxmax ignores NaN values
# - loc can also accept boolean indexing
# =====================================================================
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


# =====================================================================
# LOAD PHASE 4: GENERATE YEARLY AGGREGATIONS
# =====================================================================
# WHAT:
# Groups data by year and sums Total Houses.
#
# HOW groupby() works:
# Groups rows that share the same Year value.
#
# HOW reset_index() works:
# Converts grouped index back into normal column.
#
# HOW orient="list" works:
# Produces:
#
# {
#   "Year": [2020, 2021],
#   "Total Houses": [300, 300]
# }
#
# ADDITIONAL INFO:
# - groupby creates internal grouped object
# - reset_index is required because groupby turns column into index
# =====================================================================
def get_yearly_totals(self):

    return (
        self.df.groupby("Year")["Total Houses"]
        .sum()
        .reset_index()
        .sort_values("Year")
        .to_dict(orient="list")
    )


# =====================================================================
# LOAD PHASE 5: CONVERT DATAFRAME TO WEB-READY RECORDS
# =====================================================================
# WHAT:
# Converts DataFrame rows into list of dictionaries.
#
# HOW orient="records" works:
#
# [
#     {
#         "Typhoon": "Yolanda",
#         "Year": 2013
#     },
#     {
#         "Typhoon": "Odette",
#         "Year": 2021
#     }
# ]
#
# This structure is called a List of Dictionaries.
#
# [] = List
# {} = Dictionary
#
# Each dictionary represents one row.
#
# Difference from orient="list":
#
# orient="list"
# -> Dictionary containing Lists
#
# orient="records"
# -> List containing Dictionaries
#
# WHY use orient="records"?
# HTML tables and Flask loops process data row-by-row,
# making a list of dictionaries the most appropriate format.
#
# ADDITIONAL INFO:
# - This format is also JSON-compatible for APIs
# =====================================================================
def to_records(self, df=None):

    if df is None:
        df = self.df

    cols = [
        "Typhoon",
        "Year",
        "Totally Damaged",
        "Partially Damaged",
        "Total Houses",
        "Dead",
        "Injured",
        "Missing",
        "Severity Level"
    ]

    return df[cols].fillna(0).to_dict(orient="records")
