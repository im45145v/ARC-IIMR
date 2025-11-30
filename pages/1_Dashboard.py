import streamlit as st
import pandas as pd
import altair as alt
from utils.db import fetch_df

st.set_page_config(layout="wide")

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("🏠 Alumni Dashboard")
st.markdown("Overview of alumni dataset, distributions & trends.")


# ----------------------------------------------------
# LOAD DATA
# ----------------------------------------------------

# Total internal alumni
df_internal = fetch_df("SELECT * FROM alumni_internal")

# Total scraped external LinkedIn profiles
df_external = fetch_df("SELECT * FROM alumni_external_linkedin")

# Identity mapping table
df_map = fetch_df("SELECT * FROM alumni_identity_map")

# Experiences & skills
df_experience = fetch_df("SELECT * FROM alumni_experiences")
df_skills = fetch_df("SELECT * FROM alumni_skills")


# ----------------------------------------------------
# TOP METRICS
# ----------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Internal Alumni", len(df_internal))
col2.metric("LinkedIn Profiles", len(df_external))
col3.metric("Mapped Profiles", len(df_map))
col4.metric("Experiences Logged", len(df_experience))


# ----------------------------------------------------
# Mapped vs Unmapped
# ----------------------------------------------------
st.subheader("🔗 Mapping Status")

mapped_internal_ids = set(df_map["internal_id"])
unmapped = len(df_internal) - len(mapped_internal_ids)

map_df = pd.DataFrame({
    "Status": ["Mapped", "Unmapped"],
    "Count": [len(df_map), unmapped]
})

chart = alt.Chart(map_df).mark_arc().encode(
    theta="Count",
    color="Status",
    tooltip=["Status", "Count"]
)

st.altair_chart(chart, use_container_width=True)


# ----------------------------------------------------
# Batch Distribution
# ----------------------------------------------------
st.subheader("🎓 Batch Distribution")
if "batch" in df_internal.columns:
    batch_df = df_internal["batch"].value_counts().reset_index()
    batch_df.columns = ["Batch", "Count"]

    chart_batch = alt.Chart(batch_df).mark_bar().encode(
        x="Batch",
        y="Count",
        tooltip=["Batch", "Count"]
    )

    st.altair_chart(chart_batch, use_container_width=True)
else:
    st.info("Batch column not found in alumni_internal table.")


# ----------------------------------------------------
# Top Skills
# ----------------------------------------------------
st.subheader("💡 Top Skills (Most Common)")

if len(df_skills) > 0:
    top_skills = df_skills["skill_name"].value_counts().head(15).reset_index()
    top_skills.columns = ["skill", "count"]

    skill_chart = alt.Chart(top_skills).mark_bar().encode(
        x="count",
        y=alt.Y("skill", sort="-x"),
        tooltip=["skill", "count"]
    )
    st.altair_chart(skill_chart, use_container_width=True)
else:
    st.info("No skills data available.")


# ----------------------------------------------------
# Top Companies (From Experience)
# ----------------------------------------------------
st.subheader("🏢 Top Companies (Experience Data)")

if len(df_experience) > 0:
    company_df = df_experience["company_name"].value_counts().head(15).reset_index()
    company_df.columns = ["company", "count"]

    chart_comp = alt.Chart(company_df).mark_bar().encode(
        x="count",
        y=alt.Y("company", sort="-x"),
        tooltip=["company", "count"]
    )
    st.altair_chart(chart_comp, use_container_width=True)
else:
    st.info("No experience data available.")


# ----------------------------------------------------
# City Distribution (if present)
# ----------------------------------------------------
st.subheader("🌍 City Distribution (Top 10)")

if "city" in df_external.columns:
    city_df = df_external["city"].value_counts().head(10).reset_index()
    city_df.columns = ["city", "count"]

    city_chart = alt.Chart(city_df).mark_bar().encode(
        x="count",
        y=alt.Y("city", sort="-x"),
        tooltip=["city", "count"]
    )
    st.altair_chart(city_chart, use_container_width=True)
else:
    st.info("City column missing from LinkedIn data.")


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.caption("Dashboard powered by Supabase + Streamlit 🚀")
