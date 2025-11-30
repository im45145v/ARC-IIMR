import streamlit as st
import pandas as pd
from utils.db import fetch_df, run_sql

st.set_page_config(layout="wide")

st.title("🧰 Admin Tools & Data Quality Checks — Manager View")
st.markdown("Use these tools to find mapping gaps, missing fields, duplicates, and data quality issues. Export problem rows to CSV for remediation.")
st.divider()


# ----------------------------------------------------
# LOAD REQUIRED DATA (safe)
# ----------------------------------------------------
def safe_fetch(q):
    try:
        return fetch_df(q)
    except Exception as e:
        st.error(f"Data load failed: {e}")
        return pd.DataFrame()

df_internal = safe_fetch("SELECT * FROM alumni_internal")
df_external = safe_fetch("SELECT * FROM alumni_external_linkedin")
df_map = safe_fetch("SELECT * FROM alumni_identity_map")


# ----------------------------------------------------
# SECTION 1 — UNMAPPED LINKEDIN PROFILES
# ----------------------------------------------------
st.subheader("🔗 Unmapped LinkedIn Profiles")

mapped_linkedin_ids = set(df_map.get("linkedin_id", pd.Series(dtype=str)).astype(str)) if not df_map.empty else set()
df_unmapped_linkedin = df_external[~df_external.get("linkedin_id", pd.Series(dtype=str)).astype(str).isin(mapped_linkedin_ids)] if not df_external.empty else pd.DataFrame()

if df_unmapped_linkedin.empty:
    st.success("All LinkedIn profiles are mapped or no LinkedIn data available.")
else:
    st.warning(f"{len(df_unmapped_linkedin)} LinkedIn profiles are not mapped to internal alumni.")
    st.dataframe(df_unmapped_linkedin, use_container_width=True)
    csv = df_unmapped_linkedin.to_csv(index=False)
    st.download_button("Export Unmapped LinkedIn", csv.encode('utf-8'), "unmapped_linkedin.csv")


# ----------------------------------------------------
# SECTION 2 — INTERNAL ALUMNI WITHOUT MAPPING
# ----------------------------------------------------
st.subheader("👤 Internal Alumni Without LinkedIn Mapping")

mapped_internal_ids = set(df_map.get("internal_id", pd.Series(dtype=str)).astype(str)) if not df_map.empty else set()
df_unmapped_internal = df_internal[~df_internal.get("internal_id", pd.Series(dtype=str)).astype(str).isin(mapped_internal_ids)] if not df_internal.empty else pd.DataFrame()

if df_unmapped_internal.empty:
    st.success("All internal alumni have mapping or no internal data available.")
else:
    st.warning(f"{len(df_unmapped_internal)} internal alumni are not mapped to LinkedIn.")
    st.dataframe(df_unmapped_internal, use_container_width=True)
    st.download_button("Export Unmapped Internal", df_unmapped_internal.to_csv(index=False).encode('utf-8'), "unmapped_internal.csv")


# ----------------------------------------------------
# SECTION 3 — MISSING DATA FIELDS
# ----------------------------------------------------
st.subheader("⚠️ Missing Fields (Data Completeness)")

missing = []
if not df_internal.empty:
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
                "internal_id": row.get("internal_id"),
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
    st.download_button("Export Missing Fields", df_missing.to_csv(index=False).encode('utf-8'), "missing_fields.csv")


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
        st.download_button("Export Duplicate LinkedIn", dup.to_csv(index=False).encode('utf-8'), "duplicate_linkedin.csv")


# ----------------------------------------------------
# SECTION 5 — DUPLICATE INTERNAL ALUMNI (BY NAME + BATCH)
# ----------------------------------------------------
st.subheader("👥 Possible Duplicate Alumni Records")

if not df_internal.empty and "student_name" in df_internal.columns:
    dup_int = df_internal[df_internal.duplicated(subset=["student_name", "batch"], keep=False)]
    if dup_int.empty:
        st.success("No duplicates found in internal alumni.")
    else:
        st.error("Potential duplicates found:")
        st.dataframe(dup_int, use_container_width=True)
        st.download_button("Export Duplicate Internals", dup_int.to_csv(index=False).encode('utf-8'), "duplicate_internal.csv")


# ----------------------------------------------------
# SECTION 6 — QUICK STATS
# ----------------------------------------------------
st.subheader("📊 Quick Stats Summary")

st.metric("Total Internal Alumni", int(len(df_internal)))
st.metric("Total LinkedIn Profiles Scraped", int(len(df_external)))
st.metric("Mapped Profiles", int(len(df_map)))
st.metric("Unmapped Internal", int(len(df_unmapped_internal)))
st.metric("Unmapped LinkedIn", int(len(df_unmapped_linkedin)))


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.markdown("---")
st.caption("Admin tools to ensure data quality & accuracy.")
