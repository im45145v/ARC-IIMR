import streamlit as st
import pandas as pd
from utils.db import fetch_df
import io

# Excel writer engine detection
EXCEL_ENGINE = None
try:
    import xlsxwriter  # type: ignore
    EXCEL_ENGINE = "xlsxwriter"
except Exception:
    try:
        import openpyxl  # type: ignore
        EXCEL_ENGINE = "openpyxl"
    except Exception:
        EXCEL_ENGINE = None

# Optional AG-Grid support: provide graceful fallback if package not installed
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    HAS_AGGRID = True
except Exception:
    HAS_AGGRID = False

st.set_page_config(layout="wide")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("📊 Explore Alumni Data")
st.markdown("Filter, search, and export alumni data with AG-Grid.")

st.divider()

# ----------------------------------------------------
# LOAD REQUIRED DATA
# ----------------------------------------------------

df_internal = fetch_df("SELECT * FROM alumni_internal")
df_external = fetch_df("SELECT * FROM alumni_external_linkedin")
df_map = fetch_df("SELECT * FROM alumni_identity_map")

# Merge internal + external via mapping
df = df_map.merge(df_internal, on="internal_id", how="left")\
           .merge(df_external, on="linkedin_id", how="left", suffixes=("_int", "_ext"))

# Fallback for unmapped internal profiles
remaining = df_internal[~df_internal["internal_id"].isin(df_map["internal_id"])]

if len(remaining) > 0:
    remaining["linkedin_id"] = None
    df = pd.concat([df, remaining], ignore_index=True)

# Basic cleanup
df.fillna("", inplace=True)

# ----------------------------------------------------
# FILTER SIDEBAR
# ----------------------------------------------------

st.sidebar.header("🔍 Filters")

# Batch filter
batch_list = sorted(df["batch"].unique())
batch_filter = st.sidebar.multiselect("Batch", batch_list)

# City filter
city_list = sorted(df["city"].unique())
city_filter = st.sidebar.multiselect("City", city_list)

# Company filter (from experience table)
exp_df = fetch_df("SELECT * FROM alumni_experiences WHERE company_name <> ''")
company_list = sorted(exp_df["company_name"].unique())
company_filter = st.sidebar.multiselect("Company (Experience)", company_list)

# Name keyword filter
name_search = st.sidebar.text_input("Name Contains")

# Apply filters
df_filtered = df.copy()

if batch_filter:
    df_filtered = df_filtered[df_filtered["batch"].isin(batch_filter)]

if city_filter:
    df_filtered = df_filtered[df_filtered["city"].isin(city_filter)]

if name_search.strip():
    df_filtered = df_filtered[df_filtered["student_name"].str.contains(name_search, case=False, na=False)]

if company_filter:
    internal_ids_from_company = exp_df[exp_df["company_name"].isin(company_filter)]["alumni_id"].unique()
    df_filtered = df_filtered[df_filtered["internal_id"].isin(internal_ids_from_company)]

# ----------------------------------------------------
# AG GRID TABLE
# ----------------------------------------------------

st.subheader("📋 Alumni Records")

if HAS_AGGRID:
    gb = GridOptionsBuilder.from_dataframe(df_filtered)
    gb.configure_default_column(filter=True, sortable=True, resizable=True, editable=False)
    gb.configure_pagination(enabled=True, paginationPageSize=25)
    gb.configure_side_bar()
    gb.configure_selection("multiple")

    grid_options = gb.build()

    grid_response = AgGrid(
        df_filtered,
        gridOptions=grid_options,
        height=600,
        width="100%",
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        data_return_mode="FILTERED",
        enable_enterprise_modules=False
    )

    selected = grid_response.get("selected_rows", [])

    if selected:
        st.success(f"Selected {len(selected)} rows")
else:
    st.warning("`st-aggrid` not installed — showing a simple table. Install with `pip install st-aggrid` for improved table features.")
    st.dataframe(df_filtered)
    selected = []

# ----------------------------------------------------
# EXPORT BUTTON
# ----------------------------------------------------

def export_excel(df):
    """Return Excel bytes using available engine, or None if no engine is available."""
    if EXCEL_ENGINE is None:
        return None

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine=EXCEL_ENGINE) as writer:
        df.to_excel(writer, index=False, sheet_name="Alumni Data")
    return output.getvalue()

st.subheader("📤 Export Data")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        "Download CSV",
        df_filtered.to_csv(index=False).encode("utf-8"),
        file_name="alumni_export.csv",
        mime="text/csv"
    )

with col2:
    excel_bytes = export_excel(df_filtered)
    if excel_bytes is not None:
        st.download_button(
            "Download Excel",
            excel_bytes,
            file_name="alumni_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("Excel export not available: install `XlsxWriter` or `openpyxl` (e.g. `pip install XlsxWriter openpyxl`) to enable this feature.")


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.caption("Explore & export alumni data with filters and AG-Grid.")
