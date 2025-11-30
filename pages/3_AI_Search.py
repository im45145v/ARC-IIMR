import streamlit as st
import pandas as pd
from utils.db import fetch_df, vector_search, get_table_columns
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
    # Build SQL safely: check available columns and use parameterized filters
    try:
        cols_df = fetch_df("SELECT column_name FROM information_schema.columns WHERE table_name = 'alumni_internal';")
        available_cols = set(cols_df['column_name'].tolist()) if not cols_df.empty else set()
    except Exception:
        available_cols = set()

    # Base select columns
    select_cols = [c for c in ['internal_id', 'student_name', 'batch'] if c in available_cols]
    if 'city' in available_cols:
        select_cols.append('city')

    if not select_cols:
        select_clause = 'ai.internal_id'
    else:
        select_clause = ', '.join([f'ai.{c}' for c in select_cols])

    sql = f"SELECT {select_clause} FROM alumni_internal ai WHERE 1=1"

    params = []
    for col, val in sql_filters.items():
        if col not in available_cols:
            continue
        sql += f" AND ai.{col} ILIKE %s"
        params.append(f"%{val}%")

    try:
        sql_results = fetch_df(sql, params) if params else fetch_df(sql)
        results.extend(sql_results.to_dict(orient="records"))
    except Exception as e:
        st.error(f"SQL search failed: {e}")


# ----------------------------------------------------
# DISPLAY RESULTS
# ----------------------------------------------------
st.subheader("🔍 Search Results")

if not results:
    st.warning("No matching alumni found.")
    st.stop()

for r in results:
    # Support both dict (from fetch_df) and tuple/list (from vector_search)
    if isinstance(r, (list, tuple)):
        internal_id = r[0] if len(r) > 0 else None
        linkedin_id = r[1] if len(r) > 1 else None
        combined_text = r[2] if len(r) > 2 else ""
        distance = r[3] if len(r) > 3 else None
    else:
        internal_id = r.get("alumni_internal_id") or r.get("internal_id")
        linkedin_id = r.get("linkedin_id")
        combined_text = r.get("combined_text", "")
        distance = r.get("distance")

    # Fetch basic profile safely
    profile = pd.DataFrame()
    if linkedin_id:
        try:
            profile = fetch_df("SELECT * FROM alumni_external_linkedin WHERE linkedin_id = %s", (linkedin_id,))
        except Exception:
            profile = pd.DataFrame()

    internal = pd.DataFrame()
    if internal_id:
        try:
            internal = fetch_df("SELECT * FROM alumni_internal WHERE internal_id = %s", (internal_id,))
        except Exception:
            internal = pd.DataFrame()

    # Build manager-friendly summary
    name = None
    headline = None
    city = None
    if not profile.empty:
        prof = profile.iloc[0].fillna("")
        name = prof.get('full_name') or prof.get('student_name') or prof.get('headline')
        headline = prof.get('headline')
        city = prof.get('city') or prof.get('location')
    if not name and not internal.empty:
        name = internal.iloc[0].get('student_name')

    # Get skills and recent companies (try common FK column names)
    def safe_children(table, id_val):
        if not id_val:
            return pd.DataFrame()
        candidates = ['alumni_id', 'internal_id', 'alumni_internal_id']
        cols = get_table_columns(table)
        fk = next((c for c in candidates if c in cols), None)
        if not fk:
            return pd.DataFrame()
        try:
            return fetch_df(f"SELECT * FROM {table} WHERE {fk} = %s", (id_val,))
        except Exception:
            return pd.DataFrame()

    skills_df = safe_children('alumni_skills', internal_id)
    exp_df = safe_children('alumni_experiences', internal_id)

    top_skills = ", ".join(skills_df.get('skill_name', pd.Series(dtype=str)).dropna().unique()[:8]) if not skills_df.empty else "N/A"
    recent_companies = ", ".join(exp_df.get('company_name', pd.Series(dtype=str)).dropna().unique()[:3]) if not exp_df.empty else "N/A"

    st.markdown("---")
    st.markdown(f"### 👤 {name or 'Unknown'}")
    if headline:
        st.write(f"**Headline:** {headline}")
    if city:
        st.write(f"**Location:** {city}")
    st.write(f"**Internal ID:** {internal_id}")
    st.write(f"**LinkedIn ID:** {linkedin_id}")
    if distance is not None:
        try:
            st.write(f"**Similarity score:** {float(distance):.4f} (lower = more similar)")
        except Exception:
            st.write(f"**Similarity score:** {distance}")

    st.write(f"**Top skills:** {top_skills}")
    st.write(f"**Recent companies:** {recent_companies}")

    # Manager-friendly AI summary
    with st.expander("📘 AI Profile Summary (Manager)"):
        try:
            text_blob = combined_text or ""
            if not text_blob and not profile.empty:
                text_blob = '\n'.join([str(profile.iloc[0].get('headline','')), str(profile.iloc[0].get('about',''))])
            if text_blob.strip():
                summary = summarize_profile(text_blob)
                st.write(summary)
            else:
                st.info("Not enough profile text available for AI summarization.")
        except Exception as e:
            st.error(f"AI summarization unavailable: {e}")

    # Analyst details
    with st.expander("🔎 Analyst Details (Experience & Skills)"):
        if not exp_df.empty:
            st.dataframe(exp_df)
        else:
            st.info("No experience data available.")
        if not skills_df.empty:
            st.dataframe(skills_df)
        else:
            st.info("No skills data available.")

