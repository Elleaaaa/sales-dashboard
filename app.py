import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
import io

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Cafe Sales Dashboard",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# THEME
# =========================================================
st.markdown(
    """
<style>

/* =====================================================
   MAIN THEME
===================================================== */

.stApp {
    background-color: #0B1120;
    color: #E5E7EB;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

[data-testid="stMetric"] {
    background-color: #172033;
    border: 1px solid #263449;
    padding: 18px;
    border-radius: 12px;
}

[data-testid="stMetricLabel"] {
    color: #9CA3AF;
}

[data-testid="stMetricValue"] {
    color: #F9FAFB;
}

h1, h2, h3 {
    color: #F9FAFB;
}

div[data-testid="stTabs"] button {
    color: #CBD5E1;
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #60A5FA;
}


/* =====================================================
   STREAMLIT NATIVE HEADER
===================================================== */

header[data-testid="stHeader"] {
    position: fixed !important;
    top: 0 !important;
    z-index: 1002 !important;
    background-color: #0B1120 !important;
}


/* =====================================================
   STICKY DASHBOARD HEADER
===================================================== */

.st-key-sticky_header {
    position: fixed !important;
    top: 3.5rem !important;
    left: 21rem !important;
    right: 2rem !important;
    width: auto !important;

    z-index: 1001 !important;

    background-color: #0B1120 !important;

    padding: 12px 20px !important;

    border-bottom: 1px solid #263449;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);

    box-sizing: border-box !important;
}

/* Dashboard title */
.st-key-sticky_header h1 {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding: 0 !important;
    font-size: 2rem !important;
}

/* Keep date filter compact */
.st-key-sticky_header [data-testid="stDateInput"] {
    max-width: 240px !important;
    width: 100% !important;
    margin-left: auto !important;
}

/* Remove extra vertical spacing inside sticky header */
.st-key-sticky_header [data-testid="stVerticalBlock"] {
    gap: 0.5rem !important;
}


/* =====================================================
   RESERVE SPACE BELOW THE FIXED HEADER

   This prevents KPI cards and dashboard content from
   appearing underneath the fixed title and date filter.
===================================================== */

section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
.main .block-container {
    padding-top: 12rem !important;
    padding-bottom: 2rem !important;
}


/* =====================================================
   RESPONSIVE LAYOUT
===================================================== */

@media (max-width: 768px) {

    .st-key-sticky_header {
        left: 0.5rem !important;
        right: 0.5rem !important;
        padding: 10px !important;
    }

    .st-key-sticky_header h1 {
        font-size: 1.4rem !important;
    }

    .st-key-sticky_header [data-testid="stDateInput"] {
        max-width: 100% !important;
    }

    section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
    .main .block-container {
        padding-top: 13rem !important;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# GLOBAL SETTINGS
# =========================================================

REQUIRED_COLUMNS = [
    "Transaction No",
    "Order Time",
    "Paid Time",
    "time",
    "Outlet",
    "Product",
    "Order Type",
    "Sisa Tagihan (Rp.)",
    "Total Sales (Rp)",
    "Payment Method",
    "Payment",
    "Order",
]

GREEN = "#159447"
YELLOW = "#D9900B"
RED = "#C62828"

COLORS = [GREEN, YELLOW, RED, "#16A085", "#B9770E", "#922B21"]

MATERIALS = ["Beans", "Milk", "Syrup", "Creamer", "Powder", "Tea"]

MATERIAL_UNITS = {
    "Beans": "g",
    "Milk": "ml",
    "Syrup": "ml",
    "Creamer": "g",
    "Powder": "g",
    "Tea": "ml",
}

BOM_COLUMNS = {
    "Beans": ["BEANS (gr)", "Beans (gr)", "Beans"],
    "Milk": ["MILK (ml)", "Milk (ml)", "Milk"],
    "Syrup": ["SYRUP (ml)", "Syrup (ml)", "Syrup"],
    "Creamer": ["CREAMER (gr)", "Creamer (gr)", "Creamer"],
    "Powder": ["POWDER (gr)", "Powder (gr)", "Powder"],
    "Tea": ["TEA (ml)", "Tea (ml)", "Tea"],
}

_chart_counter = 0


# =========================================================
# DEFAULT BOM RECIPES
# =========================================================

DEFAULT_BOM = {
    "ESPRESSO": {
        "M": {"Beans": 18},
    },
    "AMERICANO": {
        "M": {"Beans": 18},
        "L": {"Beans": 27},
        "XL": {"Beans": 36},
    },
    "CAPPUCINO": {
        "M": {"Beans": 18, "Milk": 100, "Creamer": 12},
        "L": {"Beans": 27, "Milk": 150, "Creamer": 12},
        "XL": {"Beans": 36, "Milk": 200, "Creamer": 12},
    },
    "LATTE": {
        "M": {"Beans": 18, "Milk": 100, "Creamer": 12},
        "L": {"Beans": 27, "Milk": 150, "Creamer": 12},
        "XL": {"Beans": 36, "Milk": 200, "Creamer": 12},
    },
    "FLAVORS LATTE": {
        "M": {
            "Beans": 9,
            "Milk": 100,
            "Syrup": 10,
            "Creamer": 12,
            "Powder": 25,
        },
        "L": {
            "Beans": 18,
            "Milk": 150,
            "Syrup": 20,
            "Creamer": 12,
            "Powder": 25,
        },
        "XL": {
            "Beans": 27,
            "Milk": 200,
            "Syrup": 30,
            "Creamer": 12,
            "Powder": 25,
        },
    },
    "AMERICANO BASED": {
        "M": {"Beans": 18, "Syrup": 10},
        "L": {"Beans": 27, "Syrup": 20},
        "XL": {"Beans": 36, "Syrup": 30},
    },
    "MILK BASED": {
        "M": {"Milk": 100, "Syrup": 10, "Creamer": 12, "Powder": 25},
        "L": {"Milk": 150, "Syrup": 20, "Creamer": 12, "Powder": 25},
        "XL": {"Milk": 200, "Syrup": 30, "Creamer": 12, "Powder": 25},
    },
    "MATCHA": {
        "M": {"Milk": 100, "Syrup": 10, "Creamer": 12, "Powder": 25},
        "L": {"Milk": 150, "Syrup": 20, "Creamer": 12, "Powder": 25},
        "XL": {"Milk": 200, "Syrup": 30, "Creamer": 12, "Powder": 25},
    },
    "TEA": {
        "L": {"Syrup": 20, "Tea": 265},
        "XL": {"Syrup": 30, "Tea": 325},
    },
}


# =========================================================
# GENERAL HELPERS
# =========================================================


def normalize_name(value):
    value = str(value).strip().lower()
    return re.sub(r"\s+", " ", value)


def normalize_product(value):
    if pd.isna(value):
        return ""

    value = str(value).strip()

    value = re.sub(
        r"\s*\((XL|S|M|L)\)\s*$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return re.sub(r"\s+", " ", value).strip().casefold()


def normalize_category(value):
    if pd.isna(value):
        return ""

    return re.sub(r"\s+", " ", str(value).strip()).upper()


def format_currency(value):
    try:
        return f"Rp {value:,.0f}"
    except (ValueError, TypeError):
        return "Rp 0"


def format_quantity(value):
    if pd.isna(value):
        return "0"

    return f"{value:,.2f}".rstrip("0").rstrip(".")


def show_chart(fig, use_container_width=True):
    global _chart_counter
    _chart_counter += 1

    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        key=f"dashboard_chart_{_chart_counter}",
    )


def style_chart(fig, height=400):
    fig.update_layout(
        height=height,
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        margin=dict(l=20, r=35, t=45, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#CBD5E1"),
        ),
        xaxis=dict(
            gridcolor="#263449",
            zerolinecolor="#263449",
        ),
        yaxis=dict(
            gridcolor="#263449",
            zerolinecolor="#263449",
        ),
    )

    return fig


# =========================================================
# FILE READING
# =========================================================


def read_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if file_name.endswith((".xlsx", ".xls")):
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))

        sheet_names = excel_file.sheet_names

        if not sheet_names:
            raise ValueError("The Excel workbook has no sheets.")

        raw_df = pd.read_excel(
            excel_file,
            sheet_name=sheet_names[0],
        )

        category_df = None
        bom_df = None

        for sheet in sheet_names[1:]:
            sheet_key = normalize_name(sheet)

            if sheet_key == "category":
                category_df = pd.read_excel(
                    excel_file,
                    sheet_name=sheet,
                )

            elif sheet_key == "bom":
                bom_df = pd.read_excel(
                    excel_file,
                    sheet_name=sheet,
                    header=None,
                )

        return raw_df, category_df, bom_df

    if file_name.endswith(".csv"):
        try:
            raw_df = pd.read_csv(
                io.BytesIO(file_bytes),
                sep=None,
                engine="python",
            )
        except Exception:
            raw_df = pd.read_csv(io.BytesIO(file_bytes))

        return raw_df, None, None

    if file_name.endswith(".txt"):
        try:
            raw_df = pd.read_csv(
                io.BytesIO(file_bytes),
                sep=None,
                engine="python",
            )
        except Exception:
            raw_df = pd.read_csv(
                io.BytesIO(file_bytes),
                sep="\t",
            )

        return raw_df, None, None

    raise ValueError("Unsupported file format.")


# =========================================================
# COLUMN VALIDATION
# =========================================================


def validate_columns(df):
    lookup = {normalize_name(col): col for col in df.columns}

    rename_map = {}

    for required in REQUIRED_COLUMNS:
        key = normalize_name(required)

        if key not in lookup:
            raise ValueError(f"Missing required column: {required}")

        rename_map[lookup[key]] = required

    return df.rename(columns=rename_map)


def validate_category_columns(category_df):
    if category_df is None:
        return None

    lookup = {normalize_name(col): col for col in category_df.columns}

    rename_map = {}

    for col in ["Product", "Category"]:
        key = normalize_name(col)

        if key not in lookup:
            raise ValueError(f"Category sheet is missing the '{col}' column.")

        rename_map[lookup[key]] = col

    return category_df.rename(columns=rename_map)


# =========================================================
# CURRENCY CLEANING
# =========================================================


def parse_currency(value):
    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float, np.number)):
        return float(value)

    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none", "-"]:
        return 0.0

    value = value.replace("Rp", "").replace("rp", "")
    value = value.replace(" ", "")

    value = re.sub(r"[^0-9,.\-]", "", value)

    if value in ["", "-", ".", ","]:
        return 0.0

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")

    elif "," in value:
        parts = value.split(",")

        if len(parts[-1]) == 2:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")

    elif "." in value:
        parts = value.split(".")

        if len(parts[-1]) == 3:
            value = value.replace(".", "")

    try:
        return float(value)
    except ValueError:
        return 0.0


# =========================================================
# CATEGORY MAPPING
# =========================================================


def prepare_category_mapping(category_df):
    if category_df is None:
        return {}

    category_df = validate_category_columns(category_df)

    category_df = category_df[["Product", "Category"]].copy()

    category_df["Product"] = category_df["Product"].fillna("").astype(str).str.strip()

    category_df["Category"] = category_df["Category"].fillna("").astype(str).str.strip()

    category_df["_product_key"] = category_df["Product"].apply(normalize_product)

    category_df = category_df[
        (category_df["_product_key"] != "") & (category_df["Category"] != "")
    ]

    category_df = category_df.drop_duplicates(
        subset="_product_key",
        keep="first",
    )

    return dict(
        zip(
            category_df["_product_key"],
            category_df["Category"],
        )
    )


# =========================================================
# BOM PARSING
# =========================================================


def parse_bom_number(value):
    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()

    if not text or text in ["-", "–", "—"]:
        return 0.0

    text = text.replace(",", "")

    match = re.search(r"-?\d+(?:\.\d+)?", text)

    return float(match.group()) if match else 0.0


def prepare_bom_mapping(bom_df):
    if bom_df is None or bom_df.empty:
        return DEFAULT_BOM.copy()

    try:
        raw = bom_df.copy()

        if len(raw) < 3 or raw.shape[1] < 2:
            raise ValueError("Invalid BOM layout.")

        header_groups = raw.iloc[0].tolist()
        sizes = raw.iloc[1].tolist()

        current_group = ""
        flattened = []

        for idx, group in enumerate(header_groups):
            if idx == 0:
                flattened.append("CATEGORY")
                continue

            if (
                pd.notna(group)
                and str(group).strip()
                and not str(group).startswith("Unnamed")
            ):
                current_group = str(group).strip()

            flattened.append(current_group)

        mapping = {}

        for _, row in raw.iloc[2:].iterrows():
            category = row.iloc[0]

            if pd.isna(category) or not str(category).strip():
                continue

            category_key = normalize_category(category)

            mapping.setdefault(category_key, {})

            for col_idx in range(
                1,
                min(len(row), len(flattened)),
            ):
                ingredient_header = flattened[col_idx]

                size_value = sizes[col_idx] if col_idx < len(sizes) else None

                if not ingredient_header:
                    continue

                ingredient_text = normalize_name(ingredient_header)

                material = None

                for material_name, aliases in BOM_COLUMNS.items():
                    if any(
                        normalize_name(alias) == ingredient_text for alias in aliases
                    ):
                        material = material_name
                        break

                size = str(size_value).strip().upper() if pd.notna(size_value) else ""

                if material not in MATERIALS:
                    continue

                if size not in ["M", "L", "XL"]:
                    continue

                mapping[category_key].setdefault(size, {})

                mapping[category_key][size][material] = parse_bom_number(
                    row.iloc[col_idx]
                )

        if not mapping:
            raise ValueError("No BOM recipes found.")

        return mapping

    except Exception:
        return DEFAULT_BOM.copy()


# =========================================================
# DATA CLEANING
# =========================================================


def clean_data(df):
    df = validate_columns(df)

    text_columns = [
        "Transaction No",
        "Outlet",
        "Product",
        "Order Type",
        "Payment Method",
        "Payment",
        "Order",
    ]

    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["Order Time"] = pd.to_datetime(
        df["Order Time"],
        dayfirst=True,
        errors="coerce",
    )

    df["Paid Time"] = pd.to_datetime(
        df["Paid Time"],
        dayfirst=True,
        errors="coerce",
    )

    df["Total Sales (Rp)"] = df["Total Sales (Rp)"].apply(parse_currency)

    df["Sisa Tagihan (Rp.)"] = df["Sisa Tagihan (Rp.)"].apply(parse_currency)

    df = df.dropna(subset=["Order Time"]).copy()

    df["Date"] = df["Order Time"].dt.date
    df["Hour"] = df["Order Time"].dt.hour
    df["Day"] = df["Order Time"].dt.day_name()
    df["Month"] = df["Order Time"].dt.strftime("%b %Y")
    df["Year"] = df["Order Time"].dt.year
    df["Weekday"] = df["Order Time"].dt.dayofweek

    return df


# =========================================================
# PRODUCT PREPARATION
# =========================================================


def prepare_products(df, category_mapping):
    product_df = df[["Transaction No", "Order Time", "Outlet", "Product"]].copy()

    product_df["Product"] = product_df["Product"].fillna("").astype(str).str.split(",")

    product_df = product_df.explode("Product")

    product_df["Product"] = product_df["Product"].astype(str).str.strip()

    product_df = product_df[product_df["Product"].ne("")].copy()

    product_df["Units Sold"] = 1

    size_pattern = r"\s*\((XL|S|M|L)\)\s*$"

    product_df["Size"] = (
        product_df["Product"]
        .str.extract(
            size_pattern,
            flags=re.IGNORECASE,
        )[0]
        .str.upper()
    )

    product_df["Base Product"] = (
        product_df["Product"]
        .str.replace(
            size_pattern,
            "",
            regex=True,
            flags=re.IGNORECASE,
        )
        .str.strip()
    )

    product_df["Size"] = product_df["Size"].fillna("Other")

    product_df["_product_key"] = product_df["Base Product"].apply(normalize_product)

    product_df["Category"] = (
        product_df["_product_key"].map(category_mapping).fillna("Uncategorized")
    )

    product_df["Category"] = product_df["Category"].apply(normalize_category)

    return product_df


# =========================================================
# BOM CALCULATION
# =========================================================


def calculate_bom_usage(product_df, bom_mapping):
    if product_df.empty:
        return pd.DataFrame()

    grouped = (
        product_df.groupby(
            ["Product", "Base Product", "Category", "Size"],
            dropna=False,
        )["Units Sold"]
        .sum()
        .reset_index()
    )

    rows = []

    for _, item in grouped.iterrows():
        category = normalize_category(item["Category"])
        size = str(item["Size"]).upper()

        recipe_size = "M" if category == "ESPRESSO" and size == "OTHER" else size

        recipe = bom_mapping.get(category, {}).get(recipe_size, {})

        has_recipe = bool(recipe)

        if category == "FOOD":
            status = "Non-BOM product"

        elif category in ["", "UNCATEGORIZED"]:
            status = "Unmapped category"

        elif not has_recipe:
            status = "No recipe for category/size"

        else:
            status = "Mapped"

        row = {
            "Product": item["Product"],
            "Base Product": item["Base Product"],
            "Category": (category if category else "Uncategorized"),
            "Size": size,
            "Units Sold": int(item["Units Sold"]),
            "BOM Status": status,
        }

        for material in MATERIALS:
            per_unit = float(recipe.get(material, 0.0)) if recipe else 0.0

            row[f"{material} / Unit"] = per_unit

            row[f"Total {material}"] = per_unit * int(item["Units Sold"])

        rows.append(row)

    result = pd.DataFrame(rows)

    if not result.empty:
        result = result.sort_values(["Category", "Product"]).reset_index(drop=True)

    return result


def material_totals(bom_usage):
    return {
        material: (
            float(bom_usage[f"Total {material}"].sum()) if not bom_usage.empty else 0.0
        )
        for material in MATERIALS
    }


# =========================================================
# RANKING CHART
# =========================================================


def ranking_chart(
    data,
    x,
    y,
    title,
    ascending=False,
    height=520,
):
    if data.empty:
        st.info("No data available for this selection.")
        return

    chart_data = data.copy()

    chart_data["_rank"] = chart_data[x].rank(
        method="average",
        ascending=False,
        pct=True,
    )

    chart_data["_color"] = chart_data["_rank"].apply(
        lambda rank: (GREEN if rank <= 1 / 3 else YELLOW if rank <= 2 / 3 else RED)
    )

    chart_data = chart_data.sort_values(
        x,
        ascending=ascending,
    ).copy()

    category_order = chart_data[y].tolist()[::-1]

    fig = px.bar(
        chart_data,
        x=x,
        y=y,
        orientation="h",
        title=title,
        text=x,
        color="_color",
        color_discrete_map={
            GREEN: GREEN,
            YELLOW: YELLOW,
            RED: RED,
        },
        category_orders={
            y: category_order,
        },
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=category_order,
        ),
        xaxis_title="Units Sold",
        yaxis_title="",
        showlegend=False,
    )

    style_chart(fig, height=height)
    show_chart(fig)


# =========================================================
# SIDEBAR - FILE UPLOADER
# =========================================================

with st.sidebar:
    st.header("📂 Upload Data")

    uploaded_file = st.file_uploader(
        "Upload your sales workbook",
        type=["xlsx", "xls", "csv", "txt"],
    )

    st.caption("Excel workbooks can include Category and BOM reference sheets.")


# =========================================================
# LOAD DATA
# =========================================================

if uploaded_file is None:
    st.info("Please upload your sales file to view the dashboard.")

    st.markdown("""
### Expected Raw Data Columns

- Transaction No
- Order Time
- Paid Time
- time
- Outlet
- Product
- Order Type
- Sisa Tagihan (Rp.)
- Total Sales (Rp)
- Payment Method
- Payment
- Order

### Expected Excel Reference Sheets

- Category: Product, Category
- BOM: Ingredient groups with M/L/XL sizes
""")

    st.stop()


try:
    raw_df, category_df, bom_df = read_file(uploaded_file)

    df = clean_data(raw_df)

    category_mapping = prepare_category_mapping(category_df)

    bom_mapping = prepare_bom_mapping(bom_df)

    if category_df is None:
        st.warning(
            "No Category sheet was found. Products will be "
            "classified as Uncategorized."
        )

    elif not category_mapping:
        st.warning(
            "The Category sheet was found, but no valid mappings were available."
        )

except Exception as e:
    st.error(f"Unable to process the uploaded file: {e}")
    st.stop()


if df.empty:
    st.warning("No valid transaction records were found.")
    st.stop()


# =========================================================
# STICKY HEADER + GLOBAL DATE FILTER
# =========================================================

min_date = df["Order Time"].min().date()
max_date = df["Order Time"].max().date()

with st.container(key="sticky_header"):

    header_col, filter_col = st.columns(
        [2.5, 1.5],
        vertical_alignment="center",
        gap="medium",
    )

    with header_col:
        st.title("☕ Cafe Sales Dashboard")

    with filter_col:

        date_label_col, date_input_col = st.columns(
            [1, 2.5],
            vertical_alignment="center",
            gap="small",
        )

        with date_label_col:
            st.markdown("**📅 Date Filter**")

        with date_input_col:
            selected_dates = st.date_input(
                "Select Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                label_visibility="collapsed",
                key="global_date_filter",
            )


if isinstance(selected_dates, (tuple, list)):

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates

    elif len(selected_dates) == 1:
        start_date = end_date = selected_dates[0]

    else:
        start_date, end_date = min_date, max_date

else:
    start_date = end_date = selected_dates


filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()


if filtered_df.empty:
    st.warning("No transactions found for the selected date range.")
    st.stop()


product_df = prepare_products(
    filtered_df,
    category_mapping,
)

bom_usage = calculate_bom_usage(
    product_df,
    bom_mapping,
)

totals = material_totals(bom_usage)


# =========================================================
# KPI CARDS
# =========================================================

st.markdown("## 📊 Key Performance Indicators")

total_sales = filtered_df["Total Sales (Rp)"].sum()

total_transactions = filtered_df[filtered_df["Transaction No"].ne("")][
    "Transaction No"
].nunique()

average_order_value = total_sales / total_transactions if total_transactions > 0 else 0

outstanding_balance = filtered_df["Sisa Tagihan (Rp.)"].sum()

product_entries = len(product_df)

active_outlets = filtered_df[filtered_df["Outlet"].ne("")]["Outlet"].nunique()


kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(
        "Total Sales",
        format_currency(total_sales),
    )

with kpi2:
    st.metric(
        "Total Transactions",
        f"{total_transactions:,}",
    )

with kpi3:
    st.metric(
        "Average Order Value",
        format_currency(average_order_value),
    )


kpi4, kpi5, kpi6 = st.columns(3)

with kpi4:
    st.metric(
        "Outstanding Balance",
        format_currency(outstanding_balance),
    )

with kpi5:
    st.metric(
        "Product Entries",
        f"{product_entries:,}",
    )

with kpi6:
    st.metric(
        "Active Outlets",
        f"{active_outlets:,}",
    )


st.divider()


# =========================================================
# DASHBOARD TABS
# =========================================================

(
    tab_overview,
    tab_sales,
    tab_products,
    tab_time,
    tab_stores,
    tab_transactions,
    tab_bom,
) = st.tabs(
    [
        "📊 Overview",
        "💰 Sales",
        "📦 Products",
        "🕒 Time Analysis",
        "🏪 Stores",
        "🧾 Transactions",
        "🧪 BOM",
    ]
)


# =========================================================
# TAB 1 - OVERVIEW
# =========================================================

with tab_overview:

    st.subheader("Sales Overview")

    col1, col2 = st.columns(2)

    with col1:

        daily_sales = (
            filtered_df.groupby("Date")["Total Sales (Rp)"].sum().reset_index()
        )

        fig = px.line(
            daily_sales,
            x="Date",
            y="Total Sales (Rp)",
            title="Daily Sales Trend",
            markers=True,
            color_discrete_sequence=[GREEN],
        )

        fig.update_traces(line=dict(width=3))

        style_chart(fig)
        show_chart(fig)

    with col2:

        order_type_sales = (
            filtered_df.groupby("Order Type")["Total Sales (Rp)"]
            .sum()
            .reset_index()
            .sort_values(
                "Total Sales (Rp)",
                ascending=False,
            )
        )

        fig = px.pie(
            order_type_sales,
            names="Order Type",
            values="Total Sales (Rp)",
            title="Sales by Order Type",
            hole=0.55,
            color_discrete_sequence=COLORS,
        )

        style_chart(fig)
        show_chart(fig)

    st.subheader("Top 15 Products by Units Sold")

    if not product_df.empty:

        top_products = (
            product_df.groupby("Product")["Units Sold"]
            .sum()
            .reset_index()
            .sort_values(
                "Units Sold",
                ascending=False,
            )
            .head(15)
        )

        ranking_chart(
            top_products,
            x="Units Sold",
            y="Product",
            title="Top 15 Best-Selling Products",
        )

    else:
        st.info("No product data available.")


# =========================================================
# TAB 2 - SALES
# =========================================================

with tab_sales:

    st.subheader("Sales Analysis")

    col1, col2 = st.columns(2)

    with col1:

        payment_sales = (
            filtered_df.groupby("Payment Method")["Total Sales (Rp)"]
            .sum()
            .reset_index()
            .sort_values(
                "Total Sales (Rp)",
                ascending=False,
            )
        )

        fig = px.bar(
            payment_sales,
            x="Payment Method",
            y="Total Sales (Rp)",
            title="Sales by Payment Method",
            color="Payment Method",
            color_discrete_sequence=COLORS,
        )

        style_chart(fig)
        show_chart(fig)

    with col2:

        outstanding_by_outlet = (
            filtered_df.groupby("Outlet")["Sisa Tagihan (Rp.)"]
            .sum()
            .reset_index()
            .sort_values(
                "Sisa Tagihan (Rp.)",
                ascending=False,
            )
        )

        fig = px.bar(
            outstanding_by_outlet,
            x="Outlet",
            y="Sisa Tagihan (Rp.)",
            title="Outstanding Balance by Outlet",
            color_discrete_sequence=[RED],
        )

        style_chart(fig)
        show_chart(fig)

    daily_sales = filtered_df.groupby("Date")["Total Sales (Rp)"].sum().reset_index()

    fig = px.area(
        daily_sales,
        x="Date",
        y="Total Sales (Rp)",
        title="Daily Revenue Trend",
        color_discrete_sequence=[GREEN],
    )

    style_chart(fig)
    show_chart(fig)


# =========================================================
# TAB 3 - PRODUCTS
# =========================================================

with tab_products:

    st.subheader("Product Performance")

    if product_df.empty:
        st.info("No product data available.")

    else:

        product_summary = (
            product_df.groupby("Product")["Units Sold"].sum().reset_index()
        )

        st.markdown("### Top 15 Movers & Slow Movers")

        st.caption("Each comma-separated product entry counts as one unit.")

        top_movers = product_summary.sort_values("Units Sold", ascending=False).head(15)

        slow_movers = product_summary.sort_values("Units Sold", ascending=True).head(15)

        col1, col2 = st.columns(2)

        with col1:
            ranking_chart(
                top_movers,
                x="Units Sold",
                y="Product",
                title="Top 15 Movers - Units Sold",
            )

        with col2:
            ranking_chart(
                slow_movers,
                x="Units Sold",
                y="Product",
                title="Top 15 Slow Movers - Units Sold",
                ascending=True,
            )

        st.divider()

        st.markdown("## 🏷️ Category Performance")

        category_summary = (
            product_df.groupby("Category")["Units Sold"]
            .sum()
            .reset_index()
            .sort_values(
                "Units Sold",
                ascending=False,
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                category_summary,
                x="Category",
                y="Units Sold",
                title="Units Sold by Category",
                text="Units Sold",
                color="Category",
                color_discrete_sequence=COLORS,
            )

            fig.update_traces(
                textposition="outside",
                cliponaxis=False,
            )

            fig.update_layout(showlegend=False)

            style_chart(fig, height=450)
            show_chart(fig)

        with col2:

            category_pie_data = category_summary[category_summary["Units Sold"] > 0]

            fig = px.pie(
                category_pie_data,
                names="Category",
                values="Units Sold",
                title="Category Distribution",
                hole=0.55,
                color_discrete_sequence=COLORS,
            )

            style_chart(fig, height=450)
            show_chart(fig)

        st.divider()

        st.markdown("### Top Products per Category")

        available_categories = sorted(product_df["Category"].unique().tolist())

        selected_category = st.selectbox(
            "Select Category",
            options=available_categories,
            key="product_category_filter",
        )

        selected_category_data = product_df[product_df["Category"] == selected_category]

        category_product_summary = (
            selected_category_data.groupby("Product")["Units Sold"]
            .sum()
            .reset_index()
            .sort_values(
                "Units Sold",
                ascending=False,
            )
        )

        ranking_chart(
            category_product_summary.head(15),
            x="Units Sold",
            y="Product",
            title=f"Top 15 Products - {selected_category}",
        )

        st.divider()

        st.markdown("### Product Size Performance")

        st.caption("Tracks units sold for products ending in (S), (M), (L), and (XL).")

        size_order = ["S", "M", "L", "XL", "Other"]

        size_summary = (
            product_df.groupby("Size")["Units Sold"]
            .sum()
            .reindex(size_order, fill_value=0)
            .reset_index()
        )

        col1, col2 = st.columns(2)

        with col1:

            fig = px.bar(
                size_summary,
                x="Size",
                y="Units Sold",
                title="Units Sold by Size",
                text="Units Sold",
                color="Size",
                category_orders={"Size": size_order},
                color_discrete_sequence=COLORS,
            )

            fig.update_traces(
                textposition="outside",
                cliponaxis=False,
            )

            fig.update_layout(showlegend=False)

            style_chart(fig)
            show_chart(fig)

        with col2:

            size_pie_data = size_summary[size_summary["Units Sold"] > 0]

            if not size_pie_data.empty:

                fig = px.pie(
                    size_pie_data,
                    names="Size",
                    values="Units Sold",
                    title="Product Size Distribution",
                    hole=0.55,
                    color_discrete_sequence=COLORS,
                )

                style_chart(fig)
                show_chart(fig)

            else:
                st.info("No size information available.")

        st.divider()

        st.markdown("### Product Performance by Size")

        size_product_summary = (
            product_df[product_df["Size"].isin(["S", "M", "L", "XL"])]
            .groupby(["Base Product", "Size"])["Units Sold"]
            .sum()
            .reset_index()
        )

        if not size_product_summary.empty:

            top_base_products = (
                size_product_summary.groupby("Base Product")["Units Sold"]
                .sum()
                .sort_values(ascending=False)
                .head(15)
                .index
            )

            size_product_chart_data = size_product_summary[
                size_product_summary["Base Product"].isin(top_base_products)
            ].copy()

            fig = px.bar(
                size_product_chart_data,
                x="Base Product",
                y="Units Sold",
                color="Size",
                barmode="group",
                title="Top 15 Products - Units Sold by Size",
                category_orders={"Size": ["S", "M", "L", "XL"]},
                color_discrete_sequence=COLORS,
            )

            fig.update_layout(
                xaxis_title="Product",
                yaxis_title="Units Sold",
                xaxis_tickangle=-35,
                legend_title="Size",
            )

            style_chart(fig, height=550)
            show_chart(fig)

        else:
            st.info("No products with size suffixes were found.")

        st.divider()

        st.markdown("### Size Performance per Category")

        category_size_data = (
            product_df[product_df["Size"].isin(["S", "M", "L", "XL"])]
            .groupby(["Category", "Size"])["Units Sold"]
            .sum()
            .reset_index()
        )

        if not category_size_data.empty:

            fig = px.bar(
                category_size_data,
                x="Category",
                y="Units Sold",
                color="Size",
                barmode="group",
                title="Units Sold by Category and Size",
                category_orders={"Size": ["S", "M", "L", "XL"]},
                color_discrete_sequence=COLORS,
            )

            fig.update_layout(
                xaxis_title="Category",
                yaxis_title="Units Sold",
                legend_title="Size",
            )

            style_chart(fig, height=500)
            show_chart(fig)

        else:
            st.info("No categorized product size data available.")


# =========================================================
# TAB 4 - TIME ANALYSIS
# =========================================================

with tab_time:

    st.subheader("Time-Based Analysis")

    hourly_sales = (
        filtered_df.groupby("Hour")["Total Sales (Rp)"]
        .sum()
        .reindex(range(24), fill_value=0)
        .reset_index()
    )

    sales_third = hourly_sales["Total Sales (Rp)"].quantile(0.67)
    sales_first = hourly_sales["Total Sales (Rp)"].quantile(0.33)

    hourly_sales["_color"] = hourly_sales["Total Sales (Rp)"].apply(
        lambda v: (GREEN if v >= sales_third else YELLOW if v >= sales_first else RED)
    )

    fig = px.bar(
        hourly_sales,
        x="Hour",
        y="Total Sales (Rp)",
        title="Sales by Hour",
        color="_color",
        color_discrete_map={
            GREEN: GREEN,
            YELLOW: YELLOW,
            RED: RED,
        },
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="linear",
            dtick=1,
            title="Hour of Day",
        ),
        yaxis_title="Total Sales",
        showlegend=False,
    )

    style_chart(fig, height=450)
    show_chart(fig)

    hourly_transactions = (
        filtered_df.groupby("Hour")["Transaction No"]
        .nunique()
        .reindex(range(24), fill_value=0)
        .reset_index(name="Transactions")
    )

    transaction_third = hourly_transactions["Transactions"].quantile(0.67)
    transaction_first = hourly_transactions["Transactions"].quantile(0.33)

    hourly_transactions["_color"] = hourly_transactions["Transactions"].apply(
        lambda v: (
            GREEN
            if v >= transaction_third
            else YELLOW if v >= transaction_first else RED
        )
    )

    fig = px.bar(
        hourly_transactions,
        x="Hour",
        y="Transactions",
        title="Transactions by Hour",
        color="_color",
        color_discrete_map={
            GREEN: GREEN,
            YELLOW: YELLOW,
            RED: RED,
        },
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="linear",
            dtick=1,
            title="Hour of Day",
        ),
        yaxis_title="Number of Transactions",
        showlegend=False,
    )

    style_chart(fig, height=450)
    show_chart(fig)

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    weekday_sales = (
        filtered_df.groupby("Day")["Total Sales (Rp)"]
        .sum()
        .reindex(weekday_order, fill_value=0)
        .reset_index()
    )

    weekday_third = weekday_sales["Total Sales (Rp)"].quantile(0.67)
    weekday_first = weekday_sales["Total Sales (Rp)"].quantile(0.33)

    weekday_sales["_color"] = weekday_sales["Total Sales (Rp)"].apply(
        lambda v: (
            GREEN if v >= weekday_third else YELLOW if v >= weekday_first else RED
        )
    )

    fig = px.bar(
        weekday_sales,
        x="Day",
        y="Total Sales (Rp)",
        title="Sales by Day of Week",
        color="_color",
        color_discrete_map={
            GREEN: GREEN,
            YELLOW: YELLOW,
            RED: RED,
        },
    )

    fig.update_layout(
        xaxis_title="Day",
        yaxis_title="Total Sales",
        showlegend=False,
    )

    style_chart(fig, height=450)
    show_chart(fig)


# =========================================================
# TAB 5 - STORES
# =========================================================

with tab_stores:

    st.subheader("Outlet Performance")

    col1, col2 = st.columns(2)

    with col1:

        outlet_sales = (
            filtered_df.groupby("Outlet")["Total Sales (Rp)"]
            .sum()
            .reset_index()
            .sort_values(
                "Total Sales (Rp)",
                ascending=False,
            )
        )

        fig = px.bar(
            outlet_sales,
            x="Outlet",
            y="Total Sales (Rp)",
            title="Sales by Outlet",
            color_discrete_sequence=[GREEN],
        )

        style_chart(fig)
        show_chart(fig)

    with col2:

        outlet_transactions = (
            filtered_df.groupby("Outlet")["Transaction No"]
            .nunique()
            .reset_index(name="Transactions")
            .sort_values(
                "Transactions",
                ascending=False,
            )
        )

        fig = px.bar(
            outlet_transactions,
            x="Outlet",
            y="Transactions",
            title="Transactions by Outlet",
            color_discrete_sequence=[YELLOW],
        )

        style_chart(fig)
        show_chart(fig)

    fig = px.pie(
        outlet_sales,
        names="Outlet",
        values="Total Sales (Rp)",
        title="Sales Contribution by Outlet",
        hole=0.55,
        color_discrete_sequence=COLORS,
    )

    style_chart(fig)
    show_chart(fig)


# =========================================================
# TAB 6 - TRANSACTIONS
# =========================================================

with tab_transactions:

    st.subheader("Transaction Details")

    st.caption("Detailed transaction records based on the selected date range.")

    display_columns = [
        "Transaction No",
        "Order Time",
        "Paid Time",
        "Outlet",
        "Product",
        "Order Type",
        "Total Sales (Rp)",
        "Sisa Tagihan (Rp.)",
        "Payment Method",
        "Payment",
        "Order",
    ]

    transaction_display = filtered_df[display_columns].copy()

    transaction_display["Order Time"] = transaction_display["Order Time"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    transaction_display["Paid Time"] = transaction_display["Paid Time"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    search_text = st.text_input(
        "🔎 Search transactions",
        placeholder="Search transaction number, product, outlet...",
    )

    if search_text:

        search_mask = (
            transaction_display.astype(str)
            .apply(
                lambda column: column.str.contains(
                    search_text,
                    case=False,
                    na=False,
                )
            )
            .any(axis=1)
        )

        transaction_display = transaction_display[search_mask]

    st.write(f"Showing {len(transaction_display):,} transaction records")

    st.dataframe(
        transaction_display,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = transaction_display.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download Transactions CSV",
        data=csv_data,
        file_name="filtered_transactions.csv",
        mime="text/csv",
    )


# =========================================================
# TAB 7 - BOM
# =========================================================

with tab_bom:

    st.subheader("🧪 Bill of Materials (BOM)")

    st.caption(
        "Estimated ingredient consumption calculated from product "
        "units sold and the recipe assigned to each product category."
    )

    # -----------------------------------------------------
    # TOTAL MATERIAL CONSUMPTION
    # -----------------------------------------------------

    st.markdown("### Total Material Consumption")

    material_cols = st.columns(3)

    for idx, material in enumerate(MATERIALS):

        with material_cols[idx % 3]:

            st.metric(
                f"{material} Used ({MATERIAL_UNITS[material]})",
                format_quantity(totals[material]),
            )

    st.divider()

    # -----------------------------------------------------
    # MATERIAL CONSUMPTION CHART
    # -----------------------------------------------------

    st.markdown("### Material Consumption by Ingredient")

    total_material_df = pd.DataFrame(
        {
            "Material": MATERIALS,
            "Total Used": [totals[m] for m in MATERIALS],
            "Unit": [MATERIAL_UNITS[m] for m in MATERIALS],
        }
    )

    material_chart_df = total_material_df[total_material_df["Total Used"] > 0]

    if not material_chart_df.empty:

        fig = px.bar(
            material_chart_df,
            x="Material",
            y="Total Used",
            color="Material",
            text="Total Used",
            title="Total Estimated Material Consumption",
            color_discrete_sequence=COLORS,
        )

        fig.update_traces(
            texttemplate="%{text:,.2f}",
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_layout(
            showlegend=False,
            yaxis_title="Quantity (see unit labels)",
        )

        style_chart(fig, height=420)
        show_chart(fig)

        st.dataframe(
            total_material_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.info("No material consumption could be calculated for the selected period.")

    st.divider()

    # =====================================================
    # PRODUCT-LEVEL BOM USAGE - GROUPED BY CATEGORY
    # =====================================================

    st.markdown("### Product-Level BOM Usage")

    st.caption(
        "Products are grouped by category. Only materials used by "
        "each category are displayed. Each category has its own total."
    )

    if bom_usage.empty:

        st.info("No product-level BOM data is available.")

    else:

        all_category_tables = []

        categories = sorted(bom_usage["Category"].dropna().unique())

        for category in categories:

            category_data = bom_usage[bom_usage["Category"] == category].copy()

            if category_data.empty:
                continue

            active_materials = []

            for material in MATERIALS:

                total_used = category_data[f"Total {material}"].sum()

                if total_used > 0:
                    active_materials.append(material)

            st.markdown(f"#### {category}")

            total_units = int(category_data["Units Sold"].sum())

            summary_cols = st.columns(min(len(active_materials) + 1, 4))

            with summary_cols[0]:
                st.metric(
                    "Units Sold",
                    f"{total_units:,}",
                )

            for idx, material in enumerate(active_materials):

                with summary_cols[(idx + 1) % len(summary_cols)]:

                    st.metric(
                        f"{material} Used",
                        (
                            f"{format_quantity(category_data[f'Total {material}'].sum())} "
                            f"{MATERIAL_UNITS[material]}"
                        ),
                    )

            table_columns = [
                "Product",
                "Size",
                "Units Sold",
            ]

            for material in active_materials:

                table_columns.extend(
                    [
                        f"{material} / Unit",
                        f"Total {material}",
                    ]
                )

            category_table = category_data[table_columns].copy()

            rename_columns = {}

            for material in active_materials:

                rename_columns[f"{material} / Unit"] = f"{material}/Unit"

                rename_columns[f"Total {material}"] = f"Total {material}"

            category_table = category_table.rename(columns=rename_columns)

            size_order = {
                "S": 0,
                "M": 1,
                "L": 2,
                "XL": 3,
                "OTHER": 4,
            }

            category_table["_size_order"] = (
                category_table["Size"].map(size_order).fillna(99)
            )

            category_table = category_table.sort_values(
                ["_size_order", "Product"]
            ).drop(columns="_size_order")

            total_row = {col: "" for col in category_table.columns}

            total_row["Product"] = "TOTAL"
            total_row["Units Sold"] = total_units

            for material in active_materials:

                total_row[f"{material}/Unit"] = ""

                total_row[f"Total {material}"] = category_data[
                    f"Total {material}"
                ].sum()

            category_table = pd.concat(
                [
                    category_table,
                    pd.DataFrame([total_row]),
                ],
                ignore_index=True,
            )

            export_table = category_table.copy()

            export_table.insert(
                0,
                "Category",
                category,
            )

            all_category_tables.append(export_table)

            number_config = {
                "Units Sold": st.column_config.NumberColumn(
                    "Units Sold",
                    format="%d",
                )
            }

            for material in active_materials:

                number_config[f"{material}/Unit"] = st.column_config.NumberColumn(
                    f"{material}/Unit",
                    format="%.2f",
                )

                number_config[f"Total {material}"] = st.column_config.NumberColumn(
                    f"Total {material}",
                    format="%,.2f",
                )

            st.dataframe(
                category_table,
                use_container_width=True,
                hide_index=True,
                column_config=number_config,
            )

            st.divider()

        # -------------------------------------------------
        # DOWNLOAD ALL CATEGORY TABLES
        # -------------------------------------------------

        if all_category_tables:

            combined_bom_export = pd.concat(
                all_category_tables,
                ignore_index=True,
            )

            csv_bom = combined_bom_export.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                "⬇️ Download Product-Level BOM CSV",
                data=csv_bom,
                file_name="product_level_bom_usage.csv",
                mime="text/csv",
                key="download_bom_detail",
            )

        # -------------------------------------------------
        # UNMAPPED PRODUCTS
        # -------------------------------------------------

        unmapped = bom_usage[bom_usage["BOM Status"] != "Mapped"]

        if not unmapped.empty:

            with st.expander("⚠️ Products without a matching BOM recipe"):

                st.dataframe(
                    unmapped[
                        [
                            "Product",
                            "Category",
                            "Size",
                            "Units Sold",
                            "BOM Status",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

    st.caption(
        "Extra Shot is excluded. FOOD products do not consume beverage "
        "ingredients. A dash or blank BOM cell is treated as zero. "
        "ESPRESSO without a size uses its fixed 18g beans recipe."
    )

    st.divider()

    # =====================================================
    # MATERIAL CONSUMPTION BY CATEGORY
    # =====================================================

    st.markdown("### Material Consumption by Category")

    if not bom_usage.empty:

        category_material_rows = []

        for category, group in bom_usage.groupby("Category"):

            row = {
                "Category": category,
                "Units Sold": int(group["Units Sold"].sum()),
            }

            for material in MATERIALS:

                row[material] = group[f"Total {material}"].sum()

            category_material_rows.append(row)

        category_material_df = pd.DataFrame(category_material_rows)

        category_material_df = category_material_df.sort_values(
            "Units Sold",
            ascending=False,
        )

        st.dataframe(
            category_material_df,
            use_container_width=True,
            hide_index=True,
        )

    # =====================================================
    # MATERIAL CONSUMPTION BY SIZE
    # =====================================================

    st.divider()

    st.markdown("### Material Consumption by Product Size")

    if not bom_usage.empty:

        size_material_rows = []

        for size, group in bom_usage.groupby("Size"):

            row = {
                "Size": size,
                "Units Sold": int(group["Units Sold"].sum()),
            }

            for material in MATERIALS:

                row[material] = group[f"Total {material}"].sum()

            size_material_rows.append(row)

        size_material_df = pd.DataFrame(size_material_rows)

        size_order = {
            "S": 0,
            "M": 1,
            "L": 2,
            "XL": 3,
            "OTHER": 4,
        }

        size_material_df["_sort"] = size_material_df["Size"].map(size_order).fillna(99)

        size_material_df = size_material_df.sort_values("_sort").drop(columns="_sort")

        st.dataframe(
            size_material_df,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Cafe Sales Dashboard | Product units are counted from "
    "comma-separated product entries. Product-level sales are "
    "not calculated in this version. BOM consumption is an estimate "
    "based on the configured recipe per serving."
)
