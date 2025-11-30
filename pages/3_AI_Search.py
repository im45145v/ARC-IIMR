import streamlit as st
import pandas as pd
from utils.db import fetch_df, vector_search
from utils.ai_utils import get_embedding, embedding_to_pgvector, summarize_profile, interpret_query
from utils.helpers import sanitize, safe_join

st.set_page_config(layout="wide")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("🤖 AI-Powered Alumni Search")
st.markdown("""
Search alumni semantically using natural language queries.
For example:
- "Fintech alumni in Bangalore"
- "Someone with HR + analytics experience"
- "Alumni who worked at Amazon or Google"
""")

st.divider()

# ----------------------------------------------------
# TEXT INPUT
# ----------------------------------------------------
query = st.text_input("Ask your query:", placeholder="e.g. Find alumni with product management experience in Bangalore")

if not query:
    st.stop()

# ----------------------------------------------------
# AI ROUTER (SQL / VECTOR / HYBRID DECISION)
# ----------------------------------------------------
with st.spinner("Interpreting your query..."):
    route = interpret_query(query)

mode = route.get("mode", "vector")
sql_filters = route.get("sql_filters", {})
vector_query = route.get("vector_query", query)

st.info(f"AI decided search mode: **{mode.upper()}**")


# ----------------------------------------------------
# VECTOR SEARCH
# ----------------------------------------------------
results = []

if mode in ("vector", "hybrid"):
    with st.spinner("Generating embedding and searching vector DB..."):

        # Generate embedding from user query
        emb = get_embedding(vector_query)
        pg_emb = embedding_to_pgvector(emb)

        # Query Postgres vector index
        rows = vector_search(pg_emb, limit=10)
        results.extend(rows)


# ----------------------------------------------------
# SQL FILTER (Hybrid or SQL-only)
# ----------------------------------------------------
if mode in ("sql", "hybrid"):
    sql = "SELECT ai.internal_id, ai.student_name, ai.batch, ai.city FROM alumni_internal ai WHERE 1=1"

    for col, val in sql_filters.items():
        sql += f" AND {col} ILIKE '%{val}%' "

    sql_results = fetch_df(sql)
    results.extend(sql_results.to_dict(orient="records"))


# ----------------------------------------------------
# DISPLAY RESULTS
# ----------------------------------------------------
st.subheader("🔍 Search Results")

if not results:
    st.warning("No matching alumni found.")
    st.stop()

for r in results:
    with st.container(border=True):

        internal_id = r.get("alumni_internal_id") or r.get("internal_id")
        linkedin_id = r.get("linkedin_id")

        # Basic info
        name = r.get("full_name") or r.get("student_name") or "Unknown"
        st.markdown(f"### 👤 {name}")

        st.write(f"**Internal ID:** {internal_id}")
        st.write(f"**LinkedIn ID:** {linkedin_id}")

        # Fetch full profile
        profile = fetch_df(f"SELECT * FROM alumni_external_linkedin WHERE linkedin_id = '{linkedin_id}'")
        internal = fetch_df(f"SELECT * FROM alumni_internal WHERE internal_id = '{internal_id}'")
        exp = fetch_df(f"SELECT * FROM alumni_experiences WHERE alumni_id = '{internal_id}'")
        skills = fetch_df(f"SELECT * FROM alumni_skills WHERE alumni_id = '{internal_id}'")
        edu = fetch_df(f"SELECT * FROM alumni_education WHERE alumni_id = '{internal_id}'")

        # Summary
        full_text = ""

        if len(profile) > 0:
            prof = profile.iloc[0].fillna("")
            full_text += f"{prof['headline']}\n{prof['about']}\n"

        for _, e in exp.iterrows():
            full_text += safe_join([
                f"{e['title']} at {e['company_name']}",
                f"{e['start_date']} - {e['end_date']}",
                e["description"]
            ]) + "\n"

        with st.expander("📘 AI Profile Summary", expanded=False):

            if full_text.strip():
                summary = summarize_profile(full_text)
                st.write(summary)
            else:
                st.info("No profile data available for AI summarization.")

        # Experience details
        with st.expander("💼 Experience"):
            if len(exp) == 0:
                st.info("No experience found.")
            else:
                st.dataframe(exp)

        # Education
        with st.expander("🎓 Education"):
            if len(edu) == 0:
                st.info("No education data.")
            else:
                st.dataframe(edu)

        # Skills
        with st.expander("🧠 Skills"):
            if len(skills) == 0:
                st.info("No skills found.")
            else:
                st.dataframe(skills)

        st.markdown("---")
