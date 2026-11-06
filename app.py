import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
# THEME / CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>
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

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
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

_chart_counter = 0


# =========================================================
# CHART HELPER
# =========================================================


def show_chart(fig, use_container_width=True, config=None):
    """
    Assigns a unique key to every Plotly chart.
    This prevents StreamlitDuplicateElementId errors.
    """
    global _chart_counter
    _chart_counter += 1

    st.plotly_chart(
        fig,
        use_container_width=use_container_width,
        config=config,
        key=f"dashboard_chart_{_chart_counter}",
    )


def style_chart(fig, height=400):
    fig.update_layout(
        height=height,
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(color="#E5E7EB"),
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#CBD5E1")),
        xaxis=dict(gridcolor="#263449", zerolinecolor="#263449"),
        yaxis=dict(gridcolor="#263449", zerolinecolor="#263449"),
    )
    return fig


def format_currency(value):
    try:
        return f"Rp {value:,.0f}"
    except (ValueError, TypeError):
        return "Rp 0"


# =========================================================
# FILE READING
# =========================================================


def read_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    if file_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))

    if file_name.endswith(".csv"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python")
        except Exception:
            return pd.read_csv(io.BytesIO(file_bytes))

    if file_name.endswith(".txt"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python")
        except Exception:
            return pd.read_csv(io.BytesIO(file_bytes), sep="\t")

    raise ValueError("Unsupported file format.")


# =========================================================
# COLUMN VALIDATION
# =========================================================


def normalize_column_name(column):
    column = str(column).strip().lower()
    column = re.sub(r"\s+", " ", column)
    return column


def validate_columns(df):
    """
    Matches columns regardless of capitalization
    or extra spaces between words.
    """

    original_columns = list(df.columns)

    normalized_lookup = {normalize_column_name(col): col for col in original_columns}

    rename_map = {}

    for required in REQUIRED_COLUMNS:
        normalized_required = normalize_column_name(required)

        if normalized_required not in normalized_lookup:
            raise ValueError(f"Missing required column: {required}")

        original_name = normalized_lookup[normalized_required]
        rename_map[original_name] = required

    df = df.rename(columns=rename_map)

    return df


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

    # Both comma and dot present:
    # Use the last separator as the decimal separator.
    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "")
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")

    # Only comma present
    elif "," in value:
        parts = value.split(",")

        if len(parts[-1]) == 2:
            value = value.replace(".", "")
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")

    # Only dot present
    elif "." in value:
        parts = value.split(".")

        if len(parts[-1]) == 3:
            value = value.replace(".", "")

    try:
        return float(value)
    except ValueError:
        return 0.0


# =========================================================
# DATA CLEANING
# =========================================================


def clean_data(df):

    df = validate_columns(df)

    # Clean text columns
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

    # Parse dates using day-first format
    df["Order Time"] = pd.to_datetime(df["Order Time"], dayfirst=True, errors="coerce")

    df["Paid Time"] = pd.to_datetime(df["Paid Time"], dayfirst=True, errors="coerce")

    # Parse currency columns
    df["Total Sales (Rp)"] = df["Total Sales (Rp)"].apply(parse_currency)

    df["Sisa Tagihan (Rp.)"] = df["Sisa Tagihan (Rp.)"].apply(parse_currency)

    # Remove rows without a valid order date
    df = df.dropna(subset=["Order Time"]).copy()

    # Time dimensions
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


def prepare_products(df):

    product_df = df[["Transaction No", "Order Time", "Outlet", "Product"]].copy()

    # Split comma-separated product entries
    product_df["Product"] = product_df["Product"].fillna("").astype(str).str.split(",")

    # One product entry per row
    product_df = product_df.explode("Product")

    product_df["Product"] = product_df["Product"].astype(str).str.strip()

    # Remove empty product entries
    product_df = product_df[product_df["Product"].ne("")].copy()

    # Each product occurrence counts as one unit
    product_df["Units Sold"] = 1

    # Extract size suffix: (S), (M), (L), (XL)
    size_pattern = r"\s*\((XL|S|M|L)\)\s*$"

    product_df["Size"] = (
        product_df["Product"]
        .str.extract(size_pattern, flags=re.IGNORECASE)[0]
        .str.upper()
    )

    product_df["Base Product"] = (
        product_df["Product"]
        .str.replace(size_pattern, "", regex=True, flags=re.IGNORECASE)
        .str.strip()
    )

    product_df["Size"] = product_df["Size"].fillna("Other")

    return product_df


# =========================================================
# RANKING CHART
# =========================================================


def ranking_chart(data, x, y, title, ascending=False, height=520):

    if data.empty:
        st.info("No data available for this selection.")
        return

    chart_data = data.copy()

    # Rank based on units sold
    chart_data["_rank"] = chart_data[x].rank(
        method="average", ascending=False, pct=True
    )

    # Traffic-light color assignment
    chart_data["_color"] = chart_data["_rank"].apply(
        lambda rank: (GREEN if rank <= 1 / 3 else YELLOW if rank <= 2 / 3 else RED)
    )

    # Sort products
    chart_data = chart_data.sort_values(x, ascending=ascending).copy()

    # Reverse category order for horizontal bar display
    # Top Movers: Green appears at the top
    # Slow Movers: Red appears at the top
    category_order = chart_data[y].tolist()[::-1]

    fig = px.bar(
        chart_data,
        x=x,
        y=y,
        orientation="h",
        title=title,
        text=x,
        color="_color",
        color_discrete_map={GREEN: GREEN, YELLOW: YELLOW, RED: RED},
        category_orders={y: category_order},
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False
    )

    fig.update_layout(
        yaxis=dict(categoryorder="array", categoryarray=category_order),
        xaxis_title="Units Sold",
        yaxis_title="",
        showlegend=False,
    )

    style_chart(fig, height=height)
    show_chart(fig)


# =========================================================
# DASHBOARD HEADER
# =========================================================

st.title("☕ Cafe Sales Dashboard")
st.caption("Interactive sales and product performance analytics")


# =========================================================
# SIDEBAR - FILE UPLOADER ONLY
# =========================================================

with st.sidebar:
    st.header("📂 Upload Data")

    uploaded_file = st.file_uploader(
        "Upload your sales file", type=["xlsx", "xls", "csv", "txt"]
    )

    st.caption("Supported formats: Excel, CSV, TXT")


# =========================================================
# LOAD DATA
# =========================================================

if uploaded_file is None:
    st.info("Please upload your sales file to view the dashboard.")

    st.markdown("""
    ### Expected columns

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
    """)

    st.stop()


try:
    raw_df = read_file(uploaded_file)
    df = clean_data(raw_df)

except Exception as e:
    st.error(f"Unable to process the uploaded file: {e}")
    st.stop()


if df.empty:
    st.warning("No valid transaction records were found.")
    st.stop()


# =========================================================
# GLOBAL DATE FILTER
# =========================================================

st.subheader("📅 Dashboard Filters")

min_date = df["Order Time"].min().date()
max_date = df["Order Time"].max().date()

selected_dates = st.date_input(
    "Select Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, (tuple, list)):

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
    elif len(selected_dates) == 1:
        start_date = selected_dates[0]
        end_date = selected_dates[0]
    else:
        start_date, end_date = min_date, max_date

else:
    start_date = selected_dates
    end_date = selected_dates


filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()


if filtered_df.empty:
    st.warning("No transactions found for the selected date range.")
    st.stop()


# Prepare product-level data using the filtered transactions
product_df = prepare_products(filtered_df)


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
    st.metric("Total Sales", format_currency(total_sales))

with kpi2:
    st.metric("Total Transactions", f"{total_transactions:,}")

with kpi3:
    st.metric("Average Order Value", format_currency(average_order_value))


kpi4, kpi5, kpi6 = st.columns(3)

with kpi4:
    st.metric("Outstanding Balance", format_currency(outstanding_balance))

with kpi5:
    st.metric("Product Entries", f"{product_entries:,}")

with kpi6:
    st.metric("Active Outlets", f"{active_outlets:,}")


st.divider()


# =========================================================
# TABS
# =========================================================

tab_overview, tab_sales, tab_products, tab_time, tab_stores, tab_transactions = st.tabs(
    [
        "📊 Overview",
        "💰 Sales",
        "📦 Products",
        "🕒 Time Analysis",
        "🏪 Stores",
        "🧾 Transactions",
    ]
)


# =========================================================
# TAB 1 - OVERVIEW
# =========================================================

with tab_overview:

    st.subheader("Sales Overview")

    col1, col2 = st.columns(2)

    # Daily sales trend
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
        )

        fig.update_traces(line=dict(width=3))

        style_chart(fig)
        show_chart(fig)

    # Sales by order type
    with col2:

        order_type_sales = (
            filtered_df.groupby("Order Type")["Total Sales (Rp)"]
            .sum()
            .reset_index()
            .sort_values("Total Sales (Rp)", ascending=False)
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
            .sort_values("Units Sold", ascending=False)
            .head(15)
        )

        ranking_chart(
            top_products,
            x="Units Sold",
            y="Product",
            title="Top 15 Best-Selling Products",
            ascending=False,
        )

    else:
        st.info("No product data available.")


# =========================================================
# TAB 2 - SALES
# =========================================================

with tab_sales:

    st.subheader("Sales Analysis")

    col1, col2 = st.columns(2)

    # Sales by payment method
    with col1:

        payment_sales = (
            filtered_df.groupby("Payment Method")["Total Sales (Rp)"]
            .sum()
            .reset_index()
            .sort_values("Total Sales (Rp)", ascending=False)
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

    # Outstanding balance by outlet
    with col2:

        outstanding_by_outlet = (
            filtered_df.groupby("Outlet")["Sisa Tagihan (Rp.)"]
            .sum()
            .reset_index()
            .sort_values("Sisa Tagihan (Rp.)", ascending=False)
        )

        fig = px.bar(
            outstanding_by_outlet,
            x="Outlet",
            y="Sisa Tagihan (Rp.)",
            title="Outstanding Balance by Outlet",
            color_discrete_sequence=[COLORS[3]],
        )

        style_chart(fig)
        show_chart(fig)

    # Daily sales trend
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

        # -------------------------------------------------
        # TOP 15 MOVERS AND SLOW MOVERS
        # -------------------------------------------------

        st.markdown("### Top 15 Movers & Slow Movers")
        st.caption(
            "Ranked by the number of product entries. "
            "Each comma-separated product entry counts as one unit."
        )

        top_movers = product_summary.sort_values("Units Sold", ascending=False).head(15)

        slow_movers = product_summary.sort_values("Units Sold", ascending=True).head(15)

        col1, col2 = st.columns(2)

        with col1:
            ranking_chart(
                top_movers,
                x="Units Sold",
                y="Product",
                title="Top 15 Movers - Units Sold",
                ascending=False,
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

        # -------------------------------------------------
        # SIZE PERFORMANCE
        # -------------------------------------------------

        st.markdown("### Product Size Performance")

        st.caption(
            "Tracks product entries ending in (S), (M), (L), and (XL). "
            "Products without one of these suffixes are classified as Other."
        )

        size_order = ["S", "M", "L", "XL", "Other"]

        size_summary = (
            product_df.groupby("Size")["Units Sold"]
            .sum()
            .reindex(size_order, fill_value=0)
            .reset_index()
        )

        col1, col2 = st.columns(2)

        # Units sold by size
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

            fig.update_traces(textposition="outside", cliponaxis=False)

            fig.update_layout(showlegend=False)

            style_chart(fig)
            show_chart(fig)

        # Share of units by size
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

        # -------------------------------------------------
        # PRODUCT PERFORMANCE BY SIZE
        # -------------------------------------------------

        st.markdown("### Product Performance by Size")

        st.caption(
            "Compare how each base product performs across S, M, L, and XL variants."
        )

        size_product_summary = (
            product_df[product_df["Size"].isin(["S", "M", "L", "XL"])]
            .groupby(["Base Product", "Size"])["Units Sold"]
            .sum()
            .reset_index()
        )

        if not size_product_summary.empty:

            # Limit the chart to the 15 most popular base products
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
            st.info("No products with size suffixes (S), (M), (L), or (XL) were found.")


# =========================================================
# TAB 4 - TIME ANALYSIS
# =========================================================

with tab_time:

    st.subheader("Time-Based Analysis")

    col1, col2 = st.columns(2)

    # Sales by hour
    with col1:

        hourly_sales = (
            filtered_df.groupby("Hour")["Total Sales (Rp)"].sum().reset_index()
        )

        fig = px.bar(
            hourly_sales,
            x="Hour",
            y="Total Sales (Rp)",
            title="Sales by Hour",
            color_discrete_sequence=[COLORS[0]],
        )

        fig.update_xaxes(tickmode="linear", dtick=1)

        style_chart(fig)
        show_chart(fig)

    # Transactions by hour
    with col2:

        hourly_transactions = (
            filtered_df.groupby("Hour")["Transaction No"]
            .nunique()
            .reset_index(name="Transactions")
        )

        fig = px.line(
            hourly_transactions,
            x="Hour",
            y="Transactions",
            title="Transactions by Hour",
            markers=True,
            color_discrete_sequence=[YELLOW],
        )

        fig.update_xaxes(tickmode="linear", dtick=1)

        style_chart(fig)
        show_chart(fig)

    # Sales by weekday
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

    fig = px.bar(
        weekday_sales,
        x="Day",
        y="Total Sales (Rp)",
        title="Sales by Day of Week",
        color_discrete_sequence=[COLORS[2]],
    )

    style_chart(fig)
    show_chart(fig)


# =========================================================
# TAB 5 - STORES
# =========================================================

with tab_stores:

    st.subheader("Outlet Performance")

    col1, col2 = st.columns(2)

    # Sales by outlet
    with col1:

        outlet_sales = (
            filtered_df.groupby("Outlet")["Total Sales (Rp)"]
            .sum()
            .reset_index()
            .sort_values("Total Sales (Rp)", ascending=False)
        )

        fig = px.bar(
            outlet_sales,
            x="Outlet",
            y="Total Sales (Rp)",
            title="Sales by Outlet",
            color_discrete_sequence=[COLORS[0]],
        )

        style_chart(fig)
        show_chart(fig)

    # Transactions by outlet
    with col2:

        outlet_transactions = (
            filtered_df.groupby("Outlet")["Transaction No"]
            .nunique()
            .reset_index(name="Transactions")
            .sort_values("Transactions", ascending=False)
        )

        fig = px.bar(
            outlet_transactions,
            x="Outlet",
            y="Transactions",
            title="Transactions by Outlet",
            color_discrete_sequence=[COLORS[1]],
        )

        style_chart(fig)
        show_chart(fig)

    # Sales share by outlet
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

    # Format datetime for display
    transaction_display["Order Time"] = transaction_display["Order Time"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    transaction_display["Paid Time"] = transaction_display["Paid Time"].dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    # Search filter
    search_text = st.text_input(
        "🔎 Search transactions",
        placeholder="Search transaction number, product, outlet...",
    )

    if search_text:

        search_mask = (
            transaction_display.astype(str)
            .apply(
                lambda column: column.str.contains(search_text, case=False, na=False)
            )
            .any(axis=1)
        )

        transaction_display = transaction_display[search_mask]

    st.write(f"Showing {len(transaction_display):,} transaction records")

    st.dataframe(transaction_display, use_container_width=True, hide_index=True)

    # Download filtered transactions
    csv_data = transaction_display.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download Transactions CSV",
        data=csv_data,
        file_name="filtered_transactions.csv",
        mime="text/csv",
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Cafe Sales Dashboard | Product units are counted from "
    "comma-separated product entries. Product-level sales are not "
    "calculated in this version."
)
