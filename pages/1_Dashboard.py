import streamlit as st
import pandas as pd
import altair as alt
from utils.db import fetch_df

st.set_page_config(layout="wide")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("🏠 Alumni Dashboard — Manager View")
st.markdown(
    "This page summarizes key alumni metrics and trends in a simple, executive-friendly layout. Use the filters to the left to focus on batches, locations or time ranges."
)


# ----------------------------------------------------
# LOAD DATA (safe)
# ----------------------------------------------------
def safe_fetch(q):
    try:
        return fetch_df(q)
    except Exception as e:
        st.error(f"Data load failed: {e}")
        return pd.DataFrame()


# Load datasets
df_internal = safe_fetch("SELECT * FROM alumni_internal")
df_external = safe_fetch("SELECT * FROM alumni_external_linkedin")
df_map = safe_fetch("SELECT * FROM alumni_identity_map")
df_experience = safe_fetch("SELECT * FROM alumni_experiences")
df_skills = safe_fetch("SELECT * FROM alumni_skills")


# ----------------------------------------------------
# KPIs
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Internal Alumni", int(len(df_internal)))
col2.metric("LinkedIn Profiles Scraped", int(len(df_external)))
col3.metric("Profiles Mapped", f"{int(len(df_map))}")
col4.metric("Experience Records", int(len(df_experience)))

st.markdown("---")


# ----------------------------------------------------
# MAPPING STATUS (simple)
# ----------------------------------------------------
st.subheader("🔗 Mapping Status")
if df_internal.empty:
    st.info("No internal alumni data available.")
else:
    mapped_internal_ids = set(df_map.get("internal_id", [])) if not df_map.empty else set()
    mapped = len(mapped_internal_ids)
    unmapped = len(df_internal) - mapped

    status_df = pd.DataFrame({"Status": ["Mapped", "Unmapped"], "Count": [mapped, unmapped]})
    pie = alt.Chart(status_df).mark_arc().encode(theta="Count", color="Status")
    st.altair_chart(pie, use_container_width=True)

# ----------------------------------------------------
# VISUALS: Batch distribution, Top Skills, Top Companies, City distribution
# Use Altair charts for manager-friendly visuals
# ----------------------------------------------------
st.subheader("🎓 Batch Distribution (Top 20)")
if "batch" in df_internal.columns and not df_internal.empty:
    batch_df = df_internal['batch'].value_counts().head(20).reset_index()
    batch_df.columns = ["Batch", "Count"]
    chart_batch = alt.Chart(batch_df).mark_bar().encode(
        x=alt.X('Batch:N', sort='-y'),
        y='Count:Q',
        tooltip=['Batch', 'Count']
    )
    st.altair_chart(chart_batch, use_container_width=True)
else:
    st.info("Batch data not available.")

st.subheader("💡 Top Skills (Top 15)")
if not df_skills.empty and 'skill_name' in df_skills.columns:
    top_skills = df_skills['skill_name'].value_counts().head(15).reset_index()
    top_skills.columns = ["Skill", "Count"]
    skill_chart = alt.Chart(top_skills).mark_bar().encode(
        x='Count:Q',
        y=alt.Y('Skill:N', sort='-x'),
        tooltip=['Skill', 'Count']
    )
    st.altair_chart(skill_chart, use_container_width=True)
else:
    st.info("Skills data not available.")

st.subheader("🏢 Top Companies (Top 15)")
if not df_experience.empty and 'company_name' in df_experience.columns:
    company_df = df_experience['company_name'].value_counts().head(15).reset_index()
    company_df.columns = ["Company", "Count"]
    chart_comp = alt.Chart(company_df).mark_bar().encode(
        x='Count:Q',
        y=alt.Y('Company:N', sort='-x'),
        tooltip=['Company', 'Count']
    )
    st.altair_chart(chart_comp, use_container_width=True)
else:
    st.info("Experience/company data not available.")

st.subheader("🌍 City Distribution (Top 10)")
if not df_external.empty and 'city' in df_external.columns:
    city_df = df_external['city'].value_counts().head(10).reset_index()
    city_df.columns = ["city", "count"]
    city_chart = alt.Chart(city_df).mark_bar().encode(
        x='count:Q',
        y=alt.Y('city:N', sort='-x'),
        tooltip=['city', 'count']
    )
    st.altair_chart(city_chart, use_container_width=True)
else:
    st.info("City data not available.")


# ----------------------------------------------------
# Top metrics and distributions (manager friendly)
# ----------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🎓 Batch Distribution (Top)")
    if "batch" in df_internal.columns and not df_internal.empty:
        batch_df = df_internal['batch'].value_counts().head(10).reset_index()
        batch_df.columns = ["Batch", "Count"]
        st.table(batch_df)
    else:
        st.info("Batch data not available.")

with col_b:
    st.subheader("💡 Top Skills (Summary)")
    if not df_skills.empty and 'skill_name' in df_skills.columns:
        top_skills = df_skills['skill_name'].value_counts().head(10).reset_index()
        top_skills.columns = ["Skill", "Count"]
        st.table(top_skills)
    else:
        st.info("Skills data not available.")


st.markdown("---")

st.subheader("🏢 Top Companies (from experience)")
if not df_experience.empty and 'company_name' in df_experience.columns:
    company_df = df_experience['company_name'].value_counts().head(10).reset_index()
    company_df.columns = ["Company", "Count"]
    st.table(company_df)
else:
    st.info("Experience/company data not available.")


# FOOTER
st.markdown("---")
st.caption("Dashboard — executive summary. Export any table from individual pages.")
