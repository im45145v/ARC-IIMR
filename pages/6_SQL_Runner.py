import streamlit as st
import pandas as pd
import io
from utils.db import fetch_df

st.set_page_config(layout="wide")

st.title("💻 SQL Runner (Safe)")
st.markdown("""
Run **read-only SQL queries** on your Supabase Postgres database.  
Only `SELECT` statements are allowed for safety.
""")

st.divider()

# ----------------------------------------------------
# SQL INPUT BOX
# ----------------------------------------------------
default_query = "SELECT * FROM alumni_internal LIMIT 10;"

query = st.text_area(
    "Enter SQL query (must start with SELECT):",
    value=default_query,
    height=200
)

# Safety check — block destructive queries
unsafe_keywords = ["delete", "update", "insert", "drop", "alter", "truncate"]

if any(k in query.lower() for k in unsafe_keywords):
    st.error("❌ Unsafe SQL detected. Only SELECT queries are allowed.")
    st.stop()

if not query.strip().lower().startswith("select"):
    st.warning("Only SELECT queries are allowed.")
    st.stop()


# ----------------------------------------------------
# RUN QUERY BUTTON
# ----------------------------------------------------
run = st.button("▶️ Run Query")

if run:
    try:
        with st.spinner("Running query..."):
            df = fetch_df(query)

        st.success(f"Query executed successfully. Returned {len(df)} rows.")

        st.dataframe(df, use_container_width=True)

        # Export buttons
        st.subheader("📤 Export")

        col1, col2 = st.columns(2)

        # CSV
        col1.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="query_results.csv",
            mime="text/csv"
        )

        # Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Results")

        col2.download_button(
            "Download Excel",
            buffer.getvalue(),
            file_name="query_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ SQL Error: {str(e)}")


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.caption("Safe SQL execution tool for internal use.")
