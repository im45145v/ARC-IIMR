import streamlit as st
import pandas as pd
from utils.db import fetch_df, run_sql

st.set_page_config(layout="wide")

st.title("🧰 Admin Tools & Data Quality Checks")
st.markdown("Use these tools to find mapping gaps, missing fields, duplicates, and data quality issues.")
st.divider()


# ----------------------------------------------------
# LOAD REQUIRED DATA
# ----------------------------------------------------
df_internal = fetch_df("SELECT * FROM alumni_internal")
df_external = fetch_df("SELECT * FROM alumni_external_linkedin")
df_map = fetch_df("SELECT * FROM alumni_identity_map")


# ----------------------------------------------------
# SECTION 1 — UNMAPPED LINKEDIN PROFILES
# ----------------------------------------------------
st.subheader("🔗 Unmapped LinkedIn Profiles")

mapped_linkedin_ids = set(df_map["linkedin_id"].astype(str))
df_unmapped_linkedin = df_external[~df_external["linkedin_id"].astype(str).isin(mapped_linkedin_ids)]

if df_unmapped_linkedin.empty:
    st.success("All LinkedIn profiles are mapped! 🎉")
else:
    st.warning(f"{len(df_unmapped_linkedin)} LinkedIn profiles are not mapped to internal alumni.")
    st.dataframe(df_unmapped_linkedin, use_container_width=True)


# ----------------------------------------------------
# SECTION 2 — INTERNAL ALUMNI WITHOUT MAPPING
# ----------------------------------------------------
st.subheader("👤 Internal Alumni Without LinkedIn Mapping")

mapped_internal_ids = set(df_map["internal_id"].astype(str))
df_unmapped_internal = df_internal[~df_internal["internal_id"].astype(str).isin(mapped_internal_ids)]

if df_unmapped_internal.empty:
    st.success("All internal alumni have been mapped to LinkedIn profiles! 🎉")
else:
    st.warning(f"{len(df_unmapped_internal)} internal alumni are not mapped to LinkedIn.")
    st.dataframe(df_unmapped_internal, use_container_width=True)


# ----------------------------------------------------
# SECTION 3 — MISSING DATA FIELDS
# ----------------------------------------------------
st.subheader("⚠️ Missing Fields (Data Completeness)")

missing = []

for _, row in df_internal.iterrows():
    issues = []

    if not row.get("student_name"):
        issues.append("Missing Name")

    if not row.get("batch"):
        issues.append("Missing Batch")

    if not row.get("college_email") and not row.get("personal_email"):
        issues.append("No Email")

    if not row.get("mobile_no") and not row.get("whatsapp_no"):
        issues.append("No Phone Number")

    if issues:
        missing.append({
            "internal_id": row["internal_id"],
            "name": row.get("student_name"),
            "batch": row.get("batch"),
            "issues": ", ".join(issues)
        })

df_missing = pd.DataFrame(missing)

if df_missing.empty:
    st.success("No missing critical fields detected.")
else:
    st.warning("Some alumni have missing important fields:")
    st.dataframe(df_missing, use_container_width=True)


# ----------------------------------------------------
# SECTION 4 — DUPLICATE LINKEDIN IDs
# ----------------------------------------------------
st.subheader("🔁 Duplicate LinkedIn IDs")

if not df_external.empty:
    dup = df_external[df_external.duplicated(subset="linkedin_id", keep=False)]
    if dup.empty:
        st.success("No duplicate LinkedIn IDs found.")
    else:
        st.error("Duplicate LinkedIn profiles detected (CRITICAL).")
        st.dataframe(dup, use_container_width=True)


# ----------------------------------------------------
# SECTION 5 — DUPLICATE INTERNAL ALUMNI (BY NAME + BATCH)
# ----------------------------------------------------
st.subheader("👥 Possible Duplicate Alumni Records")

if "student_name" in df_internal.columns:
    dup_int = df_internal[
        df_internal.duplicated(subset=["student_name", "batch"], keep=False)
    ]
    if dup_int.empty:
        st.success("No duplicates found in internal alumni.")
    else:
        st.error("Potential duplicates found:")
        st.dataframe(dup_int, use_container_width=True)


# ----------------------------------------------------
# SECTION 6 — QUICK STATS
# ----------------------------------------------------
st.subheader("📊 Quick Stats Summary")

st.metric("Total Internal Alumni", len(df_internal))
st.metric("Total LinkedIn Profiles Scraped", len(df_external))
st.metric("Mapped Profiles", len(df_map))
st.metric("Unmapped Internal", len(df_unmapped_internal))
st.metric("Unmapped LinkedIn", len(df_unmapped_linkedin))


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.caption("Admin tools to ensure data quality & accuracy.")
