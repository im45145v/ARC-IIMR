import streamlit as st
import pandas as pd
from utils.db import fetch_df, run_sql
from utils.helpers import sanitize, linkedin_slug

st.set_page_config(layout="wide")

st.title("📝 Add / Edit Alumni Data — Simple Manager-Friendly Form")
st.markdown(
    "Use this page to add or update alumni records. Non-technical users: fill the required fields and click the buttons. Use the Edit tab to safely update mappings."
)

st.divider()

# ----------------------------------------------------
# LOAD INTERNAL ALUMNI LIST
# ----------------------------------------------------
df_internal = fetch_df("SELECT * FROM alumni_internal ORDER BY batch, student_name;")

if df_internal.empty:
    st.warning("No internal alumni records found in `alumni_internal`.")
    st.stop()

# For quick lookup
df_internal["label"] = df_internal.apply(
    lambda r: f"{r.get('student_name','')} ({r.get('batch','')}) - {r.get('roll_no','')}",
    axis=1
)

# ----------------------------------------------------
# TABS: ADD NEW / EDIT EXISTING
# ----------------------------------------------------
tab_add, tab_edit = st.tabs(["➕ Add New Alumni", "✏️ Edit Existing Alumni"])

# ====================================================
# TAB 1: ADD NEW ALUMNI
# ====================================================
with tab_add:
    st.subheader("➕ Add New Alumni (Internal)")

    with st.form("add_alumni_form"):
        col1, col2 = st.columns(2)

        with col1:
            student_name = st.text_input("Student Name *", "")
            batch = st.text_input("Batch (e.g. 2019-2021)", "")
            roll_no = st.text_input("Roll Number", "")
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"])

        with col2:
            whatsapp_no = st.text_input("WhatsApp Number")
            mobile_no = st.text_input("Mobile Number")
            college_email = st.text_input("College Email")
            personal_email = st.text_input("Personal Email")
            corporate_email = st.text_input("Corporate Email")

        linkedin_url = st.text_input("LinkedIn URL (optional)")
        por = st.text_area("Positions of Responsibility (POR) (optional)")

        submitted_add = st.form_submit_button("Add Alumni")

        if submitted_add:
            if not student_name.strip():
                st.error("Student Name is required. Please enter a full name.")
            else:
                # Insert into alumni_internal
                insert_sql = """
                    INSERT INTO alumni_internal
                    (student_name, batch, roll_no, gender,
                     whatsapp_no, mobile_no,
                     college_email, personal_email, corporate_email,
                     linkedin_url, linkedin_slug, por)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                """

                slug = linkedin_slug(linkedin_url) if linkedin_url else None

                try:
                    run_sql(
                        insert_sql,
                        [
                            sanitize(student_name),
                            sanitize(batch),
                            sanitize(roll_no),
                            sanitize(gender),
                            sanitize(whatsapp_no),
                            sanitize(mobile_no),
                            sanitize(college_email),
                            sanitize(personal_email),
                            sanitize(corporate_email),
                            sanitize(linkedin_url),
                            slug,
                            sanitize(por),
                        ],
                    )
                    st.success("✅ New alumni record added.")
                    st.info("Tip: Refresh other pages to see updated data.")
                except Exception as e:
                    st.error(f"Failed to add record: {e}")


# ====================================================
# TAB 2: EDIT EXISTING ALUMNI
# ====================================================
with tab_edit:
    st.subheader("✏️ Edit Existing Alumni")

    # Select alumni to edit
    selected_label = st.selectbox(
        "Select an alumni to edit",
        options=df_internal["label"].tolist()
    )

    # Get selected row
    row = df_internal[df_internal["label"] == selected_label].iloc[0]
    internal_id = row["internal_id"]

    st.info(f"Editing record for: **{row.get('student_name', '')}** (Internal ID: `{internal_id}`)")

    # Load current mapping (if exists)
    df_map = fetch_df(
        "SELECT * FROM alumni_identity_map WHERE internal_id = %s;",
        (internal_id,)
    )

    current_linkedin_id = df_map["linkedin_id"].iloc[0] if not df_map.empty else None

    with st.form("edit_alumni_form"):
        col1, col2 = st.columns(2)

        with col1:
            student_name_e = st.text_input("Student Name", row.get("student_name", ""))
            batch_e = st.text_input("Batch", row.get("batch", ""))
            roll_no_e = st.text_input("Roll Number", row.get("roll_no", ""))
            gender_e = st.selectbox(
                "Gender",
                ["", "Male", "Female", "Other"],
                index=["", "Male", "Female", "Other"].index(row.get("gender", "") or "")
            )

        with col2:
            whatsapp_no_e = st.text_input("WhatsApp Number", row.get("whatsapp_no", ""))
            mobile_no_e = st.text_input("Mobile Number", row.get("mobile_no", ""))
            college_email_e = st.text_input("College Email", row.get("college_email", ""))
            personal_email_e = st.text_input("Personal Email", row.get("personal_email", ""))
            corporate_email_e = st.text_input("Corporate Email", row.get("corporate_email", ""))

        linkedin_url_e = st.text_input("LinkedIn URL", row.get("linkedin_url", ""))
        por_e = st.text_area("POR", row.get("por", ""))

        st.markdown("---")
        st.markdown("### 🔗 LinkedIn Mapping")

        st.write(f"Current mapped `linkedin_id`: `{current_linkedin_id}`" if current_linkedin_id else "No linked LinkedIn profile mapped yet.")

        new_linkedin_id = st.text_input(
            "Update LinkedIn ID (from alumni_external_linkedin, optional)",
            value=current_linkedin_id or ""
        )

        submitted_edit = st.form_submit_button("Save Changes")

        if submitted_edit:
            # Update internal table
            update_sql = """
                UPDATE alumni_internal
                SET student_name=%s,
                    batch=%s,
                    roll_no=%s,
                    gender=%s,
                    whatsapp_no=%s,
                    mobile_no=%s,
                    college_email=%s,
                    personal_email=%s,
                    corporate_email=%s,
                    linkedin_url=%s,
                    linkedin_slug=%s,
                    por=%s,
                    updated_at=NOW()
                WHERE internal_id=%s;
            """

            slug_e = linkedin_slug(linkedin_url_e) if linkedin_url_e else None

            run_sql(
                update_sql,
                [
                    sanitize(student_name_e),
                    sanitize(batch_e),
                    sanitize(roll_no_e),
                    sanitize(gender_e),
                    sanitize(whatsapp_no_e),
                    sanitize(mobile_no_e),
                    sanitize(college_email_e),
                    sanitize(personal_email_e),
                    sanitize(corporate_email_e),
                    sanitize(linkedin_url_e),
                    slug_e,
                    sanitize(por_e),
                    internal_id,
                ],
            )

            # Update mapping if linkedin_id provided
            if new_linkedin_id.strip():
                # Upsert into identity map
                map_sql = """
                    INSERT INTO alumni_identity_map (internal_id, linkedin_id, match_confidence, match_method)
                    VALUES (%s, %s, 1.0, 'manual')
                    ON CONFLICT (internal_id, linkedin_id) DO UPDATE
                    SET match_confidence = EXCLUDED.match_confidence,
                        match_method = EXCLUDED.match_method;
                """
                run_sql(map_sql, [internal_id, sanitize(new_linkedin_id.strip())])

            st.success("✅ Alumni record updated successfully.")
            st.info("Reload the page to see the latest data in other tabs.")
