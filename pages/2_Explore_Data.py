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
st.set_page_config(layout="wide")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("📊 Explore Alumni Data")
st.markdown(
    "Filter, search, and export alumni data. Use **Manager View** for aggregated summaries, or **Data View** for row-level details."
)

st.divider()

# Load data safely
def safe_fetch(q):
    try:
        return fetch_df(q)
    except Exception as e:
        st.error(f"Data load failed: {e}")
        return pd.DataFrame()


df_internal = safe_fetch("SELECT * FROM alumni_internal")
df_external = safe_fetch("SELECT * FROM alumni_external_linkedin")
df_map = safe_fetch("SELECT * FROM alumni_identity_map")
exp_df = safe_fetch("SELECT * FROM alumni_experiences")

# Merge internal + external via mapping when possible
if not df_internal.empty and not df_map.empty:
    try:
        df = df_map.merge(df_internal, left_on="internal_id", right_on="internal_id", how="left")
    except Exception:
        df = df_internal.copy()
else:
    df = df_internal.copy()

if not df_external.empty and 'linkedin_id' in df.columns:
    df = df.merge(df_external, left_on='linkedin_id', right_on='linkedin_id', how='left', suffixes=('_int', '_ext'))

df.fillna("", inplace=True)

# Sidebar filters
st.sidebar.header("🔍 Filters")
view_mode = st.sidebar.radio("View Mode", ["Manager View", "Data View"]) 
# Build safe, clean filter lists (drop nulls, cast to str)
batch_vals = df.get("batch", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
batch_vals = sorted([b for b in batch_vals if b and b.strip()])
batch_filter = st.sidebar.multiselect("Batch", batch_vals)

# City filter
city_vals = df.get("city", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
city_vals = sorted([c for c in city_vals if c and c.strip()])
city_filter = st.sidebar.multiselect("City", city_vals)

# Company filter (from experience table)
exp_df = fetch_df("SELECT * FROM alumni_experiences WHERE company_name <> ''")
company_vals = exp_df.get("company_name", pd.Series(dtype=str)).dropna().astype(str).unique().tolist() if not exp_df.empty else []
company_vals = sorted([c for c in company_vals if c and c.strip()])
company_filter = st.sidebar.multiselect("Company (Experience)", company_vals)
name_search = st.sidebar.text_input("Name Contains")

# Apply filters
df_filtered = df.copy()
if batch_filter:
    df_filtered = df_filtered[df_filtered["batch"].isin(batch_filter)]
if city_filter:
    df_filtered = df_filtered[df_filtered["city"].isin(city_filter)]
if name_search.strip():
    df_filtered = df_filtered[df_filtered["student_name"].str.contains(name_search, case=False, na=False)]
if company_filter and not exp_df.empty:
    internal_ids_from_company = exp_df[exp_df["company_name"].isin(company_filter)]["alumni_id"].unique()
    df_filtered = df_filtered[df_filtered["internal_id"].isin(internal_ids_from_company)]

# Manager View: aggregations
if view_mode == "Manager View":
    st.subheader("Manager Summary")
    st.markdown("High-level aggregations you can share with stakeholders.")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Records Shown", len(df_filtered))
        st.metric("Unique Batches", df_filtered["batch"].nunique() if "batch" in df_filtered.columns else 0)
    with col2:
        st.metric("Unique Cities", df_filtered["city"].nunique() if "city" in df_filtered.columns else 0)
        st.metric("Unique Companies (exp)", exp_df["company_name"].nunique() if not exp_df.empty and "company_name" in exp_df.columns else 0)

    st.subheader("Top 10 Companies")
    if not exp_df.empty and 'company_name' in exp_df.columns:
        top_comp = exp_df['company_name'].value_counts().head(10).reset_index()
        top_comp.columns = ['Company', 'Count']
        st.table(top_comp)
    else:
        st.info("No experience/company data available.")

    st.subheader("Top 10 Skills")
    skills_df = safe_fetch("SELECT skill_name FROM alumni_skills")
    if not skills_df.empty and 'skill_name' in skills_df.columns:
        top_sk = skills_df['skill_name'].value_counts().head(10).reset_index()
        top_sk.columns = ['Skill', 'Count']
        st.table(top_sk)
    else:
        st.info("No skills data available.")

else:
    # Data View: show table with AG-Grid if available, otherwise show simple table
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
        st.info("`st-aggrid` not installed — displaying a simple table. Install `streamlit-aggrid` for a richer table UI.")
        st.dataframe(df_filtered)

# Export
st.markdown("---")
st.subheader("📤 Export")
col1, col2 = st.columns(2)
with col1:
    st.download_button("Download CSV", df_filtered.to_csv(index=False).encode("utf-8"), file_name="alumni_export.csv", mime="text/csv")
with col2:
    try:
        import io
        from pandas import ExcelWriter
        output = io.BytesIO()
        with ExcelWriter(output, engine=(EXCEL_ENGINE or 'openpyxl')) as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Alumni')
        st.download_button("Download Excel", output.getvalue(), file_name="alumni_export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception:
        st.info("Excel export not available in this environment. Install XlsxWriter or openpyxl.")

st.markdown("---")
st.caption("Explore data in Manager or Data views. Use filters to focus the dataset and export for reporting.")

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.caption("Explore & export alumni data with filters and AG-Grid.")
