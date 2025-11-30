import streamlit as st
import pandas as pd
import io
from utils.db import fetch_df

st.set_page_config(layout="wide")

st.title("💻 SQL Runner — Safe (Manager Templates)")
st.markdown(
    "Run **read-only** SQL queries. For managers, choose a template and run safe SELECTs. Analysts can enter custom SELECT queries."
)

st.divider()

# Templates for managers (safe, read-only)
templates = {
    "Recent internal alumni (10)": "SELECT * FROM alumni_internal ORDER BY updated_at DESC NULLS LAST LIMIT 10;",
    "Counts by Batch": "SELECT batch, COUNT(*) AS count FROM alumni_internal GROUP BY batch ORDER BY count DESC;",
    "Top Companies (experience)": "SELECT company_name, COUNT(*) AS count FROM alumni_experiences GROUP BY company_name ORDER BY count DESC LIMIT 20;"
}

mode = st.radio("Mode", ["Template (Manager)", "Custom (Analyst)"], index=0)

if mode == "Template (Manager)":
    choice = st.selectbox("Choose a template:", list(templates.keys()))
    query = templates[choice]
    st.code(query)
else:
    query = st.text_area("Enter SQL SELECT query:", value="SELECT * FROM alumni_internal LIMIT 25;", height=200)

# Safety checks
lower_q = query.strip().lower()
unsafe_keywords = ["delete", "update", "insert", "drop", "alter", "truncate"]
if any(k in lower_q for k in unsafe_keywords):
    st.error("Unsafe SQL detected. Only read-only SELECT queries are allowed.")
    st.stop()
if not lower_q.startswith("select"):
    st.warning("Please enter a SELECT query.")
    st.stop()

run = st.button("▶️ Run Query")

if run:
    try:
        with st.spinner("Running query..."):
            df = fetch_df(query)

        st.success(f"Query executed successfully. Returned {len(df)} rows.")
        st.dataframe(df)

        st.subheader("Export")
        col1, col2 = st.columns(2)
        col1.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), "query_results.csv")
        try:
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine=(EXCEL_ENGINE or 'openpyxl')) as writer:
                df.to_excel(writer, index=False, sheet_name='Results')
            col2.download_button("Download Excel", buf.getvalue(), "query_results.xlsx")
        except Exception:
            col2.info("Excel export not available. Install XlsxWriter or openpyxl.")

    except Exception as e:
        st.error(f"SQL Error: {e}")

st.markdown("---")
st.caption("Use templates for common manager queries. Analysts can use custom SELECTs but destructive queries are blocked.")
