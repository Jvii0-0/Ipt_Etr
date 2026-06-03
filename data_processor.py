# ---------------------------------------------------------------------
        # ⭐ [ETL PHASE 1: EXTRACT part 1]
        # Ang pagbasa at paghila ng hilaw na data mula sa hard drive papasok sa RAM.
        # ---------------------------------------------------------------------



"""
data_processor.py
IPT-101 Lesson 5 & 6 - OOP + Pandas/NumPy
TyphoonDataProcessor class encapsulates all data loading, cleaning, and analysis.
"""

# =============================================================================
# SECTION 1: IMPORTS & LIBRARY DEPENDENCIES (Mga Kailangang Tool)
# =============================================================================
# WHAT: Pag-load ng external data science modules (Pandas, NumPy, at Re).
# WHY: Mas mabilis ang mga ito kumpara sa built-in Python lists kapag libo-libong rows na ang pinoproseso.
# HOW: Ginagamitan ng 'as pd' at 'as np' para maging maikli at standard ang tawag sa kanila mamaya.
# SYSTEM IMPACT: Kung wala ito, magkakaroon ng instant NameError. Sila ang motor ng buong backend pipeline.
import pandas as pd
import numpy as np
import re


# =============================================================================
# SECTION 2: CLASS DEFINITION & INITIALIZATION (OOP Blueprint Setup)
# =============================================================================
# WHAT: Paggawa ng skeleton o blueprint ng ating TyphoonDataProcessor object.
# WHY: Ang Object-Oriented Programming ay ginagamit para pagsamahin ang data variables at code actions.
# SYSTEM IMPACT: Lumirikha ito ng permanenteng tambayan ng data sa RAM ng iyong web server (tulad ng Flask).
class TyphoonDataProcessor:
    """
    OOP class that handles the full data lifecycle:
    loading → cleaning → preprocessing → analysis → filtering.
    """

    # WHAT: Constructor method (__init__). Automatic na tumatakbo sa simula.
    # HOW: Tinatanggap ang lokasyon ng file at naghahanda ng mga walang lamang variables (None / []).
    def __init__(self, filepath: str):
        self.filepath = filepath  # Taga-tanda ng text location ng iyong raw CSV file
        self.df = None           # Dito itatabi ang magiging Pandas DataFrame table mamaya
        self.raw_lines = []      # Temporary list para sa mga hilaw na linya ng text mula sa file


    # =============================================================================
    # SECTION 3: RAW DATA FILE ACCESS & STREAM DECODING (Pagbasa sa Hard Drive)
    # =============================================================================
    # WHAT: Binubuksan ang physical file at pinagpuputol-putol ang text kada linya gamit ang newline separator.
    # WHY: Ang 'rb' (read bytes) at 'latin-1' encoding ay panangga sa mga kakaibang simbolo (tulad ng ñ o web spaces).
    # SYSTEM IMPACT: Ito ang unang checkpoint. Kung bura o mali ang file path, dito pa lang ay magsa-safe fail na ang app.
    def load_and_clean(self):
        
        # ---------------------------------------------------------------------
        # ⭐ [ETL PHASE 1: EXTRACT part 2]
        # Ang pagbasa at paghila ng hilaw na data mula sa hard drive papasok sa RAM.
        # ---------------------------------------------------------------------
        with open(self.filepath, "rb") as f:
            content = f.read().decode("latin-1")  # Ini-translate ang hilaw na bytes papuntang malinis na text

        self.raw_lines = content.split("\r\n")     # Hinihiwa ang giant block ng text gamit ang row breaks ng Windows
        records = []                               # Empty list na mag-iipon ng mga nalinis na row dictionaries
        # ---------------------------------------------------------------------


        # =============================================================================
        # SECTION 4: DATA CLEANING, REGEX REPLACEMENT & ROW FILTERING
        # =============================================================================
        # WHAT: Loop na sumusuri sa text line-by-line para mag-alis ng dumi at kumuha lang ng national data.
        # WHY: Kailangan nating linisin ang data bago ito i-convert para hindi masira ang column counting ng tables.
        # SYSTEM IMPACT: Sinasala nito ang mga panrehiyong breakdown upang maiwasan ang double-counting sa dashboard charts.
        
        # ---------------------------------------------------------------------
        # 🛠️ [ETL PHASE 2: TRANSFORM - PART A (Data Cleaning & Row Filtering)]
        # Dito sinisimulan ang pag-is-is sa dumi ng text file gamit ang Loop at Regex.
        # ---------------------------------------------------------------------
        for line in self.raw_lines[3:]:  # HOW: Ang '[3:]' ay sumisita at lumalagpas sa mga pamagat o metadata sa taas ng CSV
            if not line.strip():         # Nilalagpasan ang mga linyang puro space o walang laman
                continue

            # WHAT: Regular Expression replacement gamit ang re.sub.
            # WHY: Ang CSV ay nahihiwalay gamit ang kuwit (comma). Kung may numerong tulad ng "4,500", maiisip ng system na dalawang magkaibang kolum ito!
            # HOW: Hinahanap ng regex ang mga panipi (quotes), tinatanggal ang koma sa loob, at ginagawa itong purong '4500'.
            cleaned = re.sub(
                r'"([^"]*)"',
                lambda m: m.group(1).replace(",", "").strip(),
                line
            )
            parts = [p.strip() for p in cleaned.split(",")]  # Hinihiwa na ang linya gamit ang totoong mga koma

            # SAFETY CHECK: Kung kulang sa kolum o walang pangalan ang bagyo, itapon ang linyang iyon
            if len(parts) < 9 or not parts[0]:
                continue

            name     = parts[0].strip()
            year     = parts[1].strip()
            location = parts[2].strip()

            # WHAT: Location Filtering. 
            # WHY: Gusto lang natin ang mga hilera na kumakatawan sa kabuuan ng bansa (National Total).
            if "TOTAL" not in location.upper():
                continue

            # WHAT: Dictionary Population.
            # HOW: Pinapasok ang mga datos sa records list. Ginagamitan ng '_parse_num' helper para maging ligtas ang numero.
            records.append({
                "Typhoon":          name,
                "Year":              int(year) if year.isdigit() else 0,  # Fallback sa 0 kung hindi numero ang taon
                "Totally Damaged":   self._parse_num(parts[3]),
                "Partially Damaged": self._parse_num(parts[4]),
                "Total Houses":      self._parse_num(parts[5]),
                "Dead":              self._parse_num(parts[6]),
                "Injured":           self._parse_num(parts[7]),
                "Missing":           self._parse_num(parts[8]),
            })


        # =============================================================================
        # SECTION 5: PANDAS DATAFRAME CREATION & NUMPY FEATURE ENGINEERING
        # =============================================================================
        # WHAT: Paggawa ng pormal na talahanayan (DataFrame) at pag-compute ng mga bagong analytical columns.
        # WHY: Ang mga bagong kolum na ito ang nagbibigay ng mas malalim na kahulugan o insights para sa visual graphs.
        # SYSTEM IMPACT: Direktang nagbibigay ng kulay at label sa frontend badges (tulad ng text na 'Catastrophic').
        
        # ---------------------------------------------------------------------
        # 🛠️ [ETL PHASE 2: TRANSFORM - PART B (Pandas Table & Feature Engineering)]
        # Dito ginagamit ang Pandas/NumPy para sa advanced calculations ng mga bagong columns.
        # ---------------------------------------------------------------------
        self.df = pd.DataFrame(records)

        # WHAT: Data Imputation.
        # WHY: Pinapalitan ng '0' ang mga 'NaN' (Not a Number) para hindi masira ang mga math algorithms sa susunod na hakbang.
        self.df.fillna(0, inplace=True)

        # WHAT: Vectorized Column Addition. Mabilisang pinagsasama ang tatlong kolum para makuha ang kabuuang biktima.
        self.df["Casualty Total"]  = self.df["Dead"] + self.df["Injured"] + self.df["Missing"]
        
        # WHAT: Logarithmic normalization gamit ang NumPy (np.log1p).
        # WHY: Ang pinsala sa bahay ay pwedeng maging 0 hanggang milyon. Kung walang Log, hindi makikita sa graph ang maliliit na bagyo dahil lalamunin sila ng malalaking numero. Ang log1p ay nagpapakinis ng scale nang walang math error ($log(x+1)$).
        self.df["Severity Score"]  = np.log1p(self.df["Total Houses"].values)

        # WHAT: Categorical Binning gamit ang pd.cut.
        # HOW: Pinagpapangkat-pangkat ang 'Total Houses' base sa tinakdang limitasyon o bins.
        # WHY: Binabago nito ang kumplikadong numero upang maging simpleng salita na madaling maintindihan ng tao.
        self.df["Severity Level"] = pd.cut(
            self.df["Total Houses"],
            bins=[0, 10_000, 100_000, 500_000, float("inf")],
            labels=["Minor", "Moderate", "Severe", "Catastrophic"]
        ).astype(str).replace("nan", "Minor")  # Ginagawang 'Minor' ang mga lumagpas o nag-error na data

        return self  # Ginagamit para sa method chaining (hal. processor.load_and_clean().get_stats())


    # =============================================================================
    # SECTION 6: DEFENSIVE UTILITY METHODS (Ang Ligtas na Tagasuri)
    # =============================================================================
    # WHAT: Isang independiyenteng tagasuri (Sanitizer) na nagta-transform ng text papuntang integer.
    # WHY: Madalas gumagamit ang gobyerno ng gitling (-) o blangkong espasyo para sa zero. Kung piliting i-convert ang int("-"), magke-crash ang buong app.
    # HOW: Ginamitan ng try/except. Kapag may nakitang error o hindi kaya i-convert, awtomatiko itong magbabalik ng 0.
    # SYSTEM IMPACT: Ito ang nagsisilbing kalasag ng web app mo para hindi ito mamatay o mag-down dahil lang sa isang typo sa file.
    
    # ---------------------------------------------------------------------
    # 🛠️ [ETL PHASE 2: TRANSFORM - PART C (Data Type Standardization Helper)]
    # Bahagi pa rin ng Transformation dahil binabago nito ang data types (Text to Integer) nang ligtas.
    # ---------------------------------------------------------------------
    @staticmethod
    def _parse_num(s: str) -> int:
        s = s.strip().replace(" ", "").replace("\xa0", "")  # Tinatanggal ang mga spaces at nakatagong web spaces
        if not s or s == "-":
            return 0
        try:
            return int(s)
        except ValueError:
            return 0


    # =============================================================================
    # SECTION 7: DATA ANALYSIS, METRICS AGGREGATION & FORMAT CONVERSION
    # =============================================================================
    # WHAT: Grupo ng mga aksyon para mag-query, mag-aggregate (sum, max, groupby), mag-filter, at magbago ng data format.
    # WHY: Ang frontend UI (HTML/JavaScript) ay hindi kayang magbasa ng Pandas DataFrame nang direkta. Kailangan nito ng standard JSON/dictionaries.
    # SYSTEM IMPACT: Ito ang nagpapakain ng totoong numero sa mga KPI summary cards, dropdown menus, at interactive tables sa iyong website.
    
    # ---------------------------------------------------------------------
    # 🚀 [ETL PHASE 3: LOAD - Aggregations & Web Delivery Format]
    # Dito inihahanda at 'hinihiwa-hiwalay' ang data papuntang native Python formats 
    # (Dictionaries/Lists) upang direktang mai-load o maisubo sa HTML/Flask templates.
    # ---------------------------------------------------------------------
    def get_stats(self, df=None) -> dict:
        """Return summary statistics dict for KPI cards."""
        if df is None:
            df = self.df
        if df.empty:
            return {}
        
        # HOW: Ang '.idxmax()' ay hinahanap ang row number kung saan pinakamataas ang 'Total Houses'.
        #      Gagamitin ang '.loc' para hugutin ang partikular na pangalan at taon ng pinakamalalang bagyong iyon.
        worst_idx = df["Total Houses"].idxmax()
        return {
            "total_typhoons":    int(len(df)),
            "total_houses":       int(df["Total Houses"].sum()),  # Kinuha ang kabuuang sum ng lahat ng nasirang bahay
            "totally_damaged":    int(df["Totally Damaged"].sum()),
            "partially_damaged": int(df["Partially Damaged"].sum()),
            "total_dead":        int(df["Dead"].sum()),
            "total_injured":     int(df["Injured"].sum()),
            "total_missing":     int(df["Missing"].sum()),
            "worst_typhoon":     df.loc[worst_idx, "Typhoon"],
            "worst_year":        int(df.loc[worst_idx, "Year"]),
            "worst_houses":      int(df["Total Houses"].max()),   # Nakuha ang pinakamataas na naitalang damage sa isang bagyo
            "years_covered":     sorted(df["Year"].unique().tolist()),
        }

    # WHAT: Time-series aggregator gamit ang .groupby().
    def get_yearly_totals(self) -> dict:
        yearly = (
            self.df.groupby("Year")["Total Houses"]
            .sum()
            .reset_index()
            .sort_values("Year")
        )
        return yearly.to_dict(orient="list")  # Ginagawang dictionary ng mga listahan para madaling i-transport sa web

    # WHAT: Row filter para sa menu search.
    def filter_by_year(self, year=None):
        if year and year != "all":
            try:
                return self.df[self.df["Year"] == int(year)].copy()
            except (ValueError, TypeError):
                return self.df.copy()
        return self.df.copy()

    # WHAT: Dynamic dropdown builder.
    def get_years(self) -> list:
        return sorted(self.df["Year"].unique().tolist())

    # WHAT: Final conversion function.
    def to_records(self, df=None) -> list:
        if df is None:
            df = self.df
        cols = ["Typhoon", "Year", "Totally Damaged", "Partially Damaged",
                "Total Houses", "Dead", "Injured", "Missing",
                "Casualty Total", "Severity Level"]
        return df[cols].fillna(0).to_dict(orient="records")  # Pinal na pag-Load ng format papuntang JSON-ready array