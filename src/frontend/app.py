"""
Streamlit Frontend for Alumni Management System.
Provides a web interface for querying alumni data and admin operations.
"""

import os
import io
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import streamlit as st
import pandas as pd

# Import database modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import init_db, get_session, Alumni, Gender, AlumniStatus
from src.database.repository import (
    AlumniRepository, JobHistoryRepository, EducationHistoryRepository
)
from src.config import config

logger = logging.getLogger(__name__)


def check_password() -> bool:
    """Check if admin password is correct."""
    
    def password_entered():
        """Check password when entered."""
        entered_password = st.session_state.get("admin_password", "")
        correct_password = config.admin.password or os.getenv("ADMIN_PASSWORD", "admin123")
        
        if hashlib.sha256(entered_password.encode()).hexdigest() == \
           hashlib.sha256(correct_password.encode()).hexdigest():
            st.session_state["admin_authenticated"] = True
            del st.session_state["admin_password"]
        else:
            st.session_state["admin_authenticated"] = False
    
    if st.session_state.get("admin_authenticated"):
        return True
    
    st.text_input(
        "Admin Password",
        type="password",
        key="admin_password",
        on_change=password_entered
    )
    
    if st.session_state.get("admin_authenticated") is False:
        st.error("Incorrect password")
    
    return False


def get_db_session():
    """Get database session."""
    if "db_engine" not in st.session_state:
        db_url = config.database.get_connection_string()
        st.session_state["db_engine"] = init_db(db_url)
    return get_session(st.session_state["db_engine"])


def export_to_excel(df: pd.DataFrame, filename: str = "alumni_export.xlsx") -> bytes:
    """Export DataFrame to Excel bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Alumni')
    return output.getvalue()


def main_page():
    """Main alumni search and display page."""
    st.header("🎓 Alumni Directory")
    
    try:
        session = get_db_session()
        alumni_repo = AlumniRepository(session)
        
        # Search filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            name_filter = st.text_input("🔍 Search by Name", "")
        
        with col2:
            batches = ["All"] + alumni_repo.get_batches()
            batch_filter = st.selectbox("📅 Batch", batches)
        
        with col3:
            companies = ["All"] + alumni_repo.get_companies()
            company_filter = st.selectbox("🏢 Company", companies)
        
        col4, col5 = st.columns(2)
        
        with col4:
            designation_filter = st.text_input("💼 Designation", "")
        
        with col5:
            location_filter = st.text_input("📍 Location", "")
        
        # Apply filters
        search_params = {}
        if name_filter:
            search_params['name'] = name_filter
        if batch_filter != "All":
            search_params['batch'] = batch_filter
        if company_filter != "All":
            search_params['company'] = company_filter
        if designation_filter:
            search_params['designation'] = designation_filter
        if location_filter:
            search_params['location'] = location_filter
        
        # Get results
        alumni_list = alumni_repo.search(**search_params, limit=500)
        
        st.markdown(f"**Found {len(alumni_list)} alumni**")
        
        if alumni_list:
            # Convert to DataFrame
            df_data = []
            for alum in alumni_list:
                df_data.append({
                    'ID': alum.id,
                    'Name': alum.name,
                    'Batch': alum.batch,
                    'Roll No': alum.roll_number,
                    'Current Company': alum.current_company,
                    'Designation': alum.current_designation,
                    'Location': alum.current_location,
                    'Email': alum.personal_email or alum.college_email,
                    'LinkedIn': alum.linkedin_url or (f"https://linkedin.com/in/{alum.linkedin_id}" if alum.linkedin_id else None),
                    'WhatsApp': alum.whatsapp_number,
                })
            
            df = pd.DataFrame(df_data)
            
            # Display table
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export button
            excel_data = export_to_excel(df)
            st.download_button(
                label="📥 Download as Excel",
                data=excel_data,
                file_name=f"alumni_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Detail view
            st.subheader("👤 Alumni Details")
            selected_id = st.selectbox(
                "Select alumni to view details",
                options=[a.id for a in alumni_list],
                format_func=lambda x: next((a.name for a in alumni_list if a.id == x), str(x))
            )
            
            if selected_id:
                selected_alumni = alumni_repo.get_by_id(selected_id)
                if selected_alumni:
                    display_alumni_details(selected_alumni, session)
        else:
            st.info("No alumni found matching your criteria.")
            
    except Exception as e:
        st.error(f"Database error: {e}")
        logger.error(f"Database error: {e}")


def display_alumni_details(alumni: Alumni, session):
    """Display detailed information about an alumni."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Name:** {alumni.name}")
        st.markdown(f"**Batch:** {alumni.batch or 'N/A'}")
        st.markdown(f"**Roll Number:** {alumni.roll_number or 'N/A'}")
        st.markdown(f"**Gender:** {alumni.gender.value if alumni.gender else 'N/A'}")
    
    with col2:
        st.markdown(f"**Current Company:** {alumni.current_company or 'N/A'}")
        st.markdown(f"**Designation:** {alumni.current_designation or 'N/A'}")
        st.markdown(f"**Location:** {alumni.current_location or 'N/A'}")
    
    st.markdown("---")
    st.markdown("**📧 Contact Information**")
    contact_col1, contact_col2 = st.columns(2)
    
    with contact_col1:
        st.markdown(f"Personal Email: {alumni.personal_email or 'N/A'}")
        st.markdown(f"College Email: {alumni.college_email or 'N/A'}")
        st.markdown(f"Corporate Email: {alumni.corporate_email or 'N/A'}")
    
    with contact_col2:
        st.markdown(f"WhatsApp: {alumni.whatsapp_number or 'N/A'}")
        st.markdown(f"Mobile: {alumni.mobile_number or 'N/A'}")
        if alumni.linkedin_url:
            st.markdown(f"[LinkedIn Profile]({alumni.linkedin_url})")
        elif alumni.linkedin_id:
            st.markdown(f"[LinkedIn Profile](https://linkedin.com/in/{alumni.linkedin_id})")
    
    # Job History
    job_repo = JobHistoryRepository(session)
    jobs = job_repo.get_by_alumni_id(alumni.id)
    
    if jobs:
        st.markdown("---")
        st.markdown("**💼 Work Experience**")
        for job in jobs:
            with st.expander(f"{job.job_title or 'Position'} at {job.company_name}"):
                st.markdown(f"**Company:** {job.company_name}")
                st.markdown(f"**Title:** {job.job_title or 'N/A'}")
                st.markdown(f"**Location:** {job.location or 'N/A'}")
                st.markdown(f"**Duration:** {job.start_date or 'N/A'} - {job.end_date or 'Present'}")
                if job.description:
                    st.markdown(f"**Description:** {job.description}")
    
    # Education History
    edu_repo = EducationHistoryRepository(session)
    educations = edu_repo.get_by_alumni_id(alumni.id)
    
    if educations:
        st.markdown("---")
        st.markdown("**🎓 Education**")
        for edu in educations:
            with st.expander(f"{edu.degree or 'Degree'} from {edu.institution_name}"):
                st.markdown(f"**Institution:** {edu.institution_name}")
                st.markdown(f"**Degree:** {edu.degree or 'N/A'}")
                st.markdown(f"**Field:** {edu.field_of_study or 'N/A'}")
                st.markdown(f"**Years:** {edu.start_year or 'N/A'} - {edu.end_year or 'N/A'}")


def admin_page():
    """Admin interface for managing alumni data."""
    st.header("⚙️ Admin Panel")
    
    if not check_password():
        st.warning("Please enter the admin password to access this section.")
        return
    
    st.success("✅ Authenticated")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Alumni", "Edit Alumni", "Import Data", "Statistics"])
    
    with tab1:
        add_alumni_form()
    
    with tab2:
        edit_alumni_form()
    
    with tab3:
        import_data_section()
    
    with tab4:
        display_statistics()


def add_alumni_form():
    """Form to add a new alumni."""
    st.subheader("➕ Add New Alumni")
    
    with st.form("add_alumni_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name *", key="add_name")
            batch = st.text_input("Batch", key="add_batch")
            roll_number = st.text_input("Roll Number", key="add_roll")
            gender = st.selectbox("Gender", ["Not Specified", "Male", "Female", "Other"], key="add_gender")
        
        with col2:
            current_company = st.text_input("Current Company", key="add_company")
            current_designation = st.text_input("Current Designation", key="add_designation")
            current_location = st.text_input("Location", key="add_location")
        
        st.markdown("**Contact Information**")
        contact_col1, contact_col2 = st.columns(2)
        
        with contact_col1:
            personal_email = st.text_input("Personal Email", key="add_personal_email")
            college_email = st.text_input("College Email", key="add_college_email")
            corporate_email = st.text_input("Corporate Email", key="add_corporate_email")
        
        with contact_col2:
            whatsapp = st.text_input("WhatsApp Number", key="add_whatsapp")
            mobile = st.text_input("Mobile Number", key="add_mobile")
            linkedin_id = st.text_input("LinkedIn ID", key="add_linkedin")
        
        submitted = st.form_submit_button("Add Alumni")
        
        if submitted:
            if not name:
                st.error("Name is required!")
            else:
                try:
                    session = get_db_session()
                    alumni_repo = AlumniRepository(session)
                    
                    gender_map = {
                        "Not Specified": Gender.NOT_SPECIFIED,
                        "Male": Gender.MALE,
                        "Female": Gender.FEMALE,
                        "Other": Gender.OTHER
                    }
                    
                    alumni_data = {
                        'name': name,
                        'batch': batch or None,
                        'roll_number': roll_number or None,
                        'gender': gender_map.get(gender, Gender.NOT_SPECIFIED),
                        'current_company': current_company or None,
                        'current_designation': current_designation or None,
                        'current_location': current_location or None,
                        'personal_email': personal_email or None,
                        'college_email': college_email or None,
                        'corporate_email': corporate_email or None,
                        'whatsapp_number': whatsapp or None,
                        'mobile_number': mobile or None,
                        'linkedin_id': linkedin_id or None,
                    }
                    
                    new_alumni = alumni_repo.create(alumni_data)
                    st.success(f"✅ Alumni '{name}' added successfully! ID: {new_alumni.id}")
                    
                except Exception as e:
                    st.error(f"Error adding alumni: {e}")


def edit_alumni_form():
    """Form to edit existing alumni."""
    st.subheader("✏️ Edit Alumni")
    
    try:
        session = get_db_session()
        alumni_repo = AlumniRepository(session)
        
        # Search for alumni to edit
        search_term = st.text_input("Search alumni by name or roll number", key="edit_search")
        
        if search_term:
            results = alumni_repo.search(name=search_term, limit=10)
            
            if results:
                selected_id = st.selectbox(
                    "Select alumni to edit",
                    options=[a.id for a in results],
                    format_func=lambda x: f"{next((a.name for a in results if a.id == x), '')} ({next((a.batch for a in results if a.id == x), 'N/A')})"
                )
                
                alumni = alumni_repo.get_by_id(selected_id)
                
                if alumni:
                    with st.form("edit_alumni_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            name = st.text_input("Name *", value=alumni.name or "", key="edit_name")
                            batch = st.text_input("Batch", value=alumni.batch or "", key="edit_batch")
                            current_company = st.text_input("Current Company", value=alumni.current_company or "", key="edit_company")
                        
                        with col2:
                            current_designation = st.text_input("Designation", value=alumni.current_designation or "", key="edit_designation")
                            current_location = st.text_input("Location", value=alumni.current_location or "", key="edit_location")
                            personal_email = st.text_input("Personal Email", value=alumni.personal_email or "", key="edit_email")
                        
                        submitted = st.form_submit_button("Update Alumni")
                        
                        if submitted:
                            update_data = {
                                'name': name,
                                'batch': batch or None,
                                'current_company': current_company or None,
                                'current_designation': current_designation or None,
                                'current_location': current_location or None,
                                'personal_email': personal_email or None,
                            }
                            
                            alumni_repo.update(alumni.id, update_data)
                            st.success(f"✅ Alumni '{name}' updated successfully!")
            else:
                st.info("No alumni found matching your search.")
    
    except Exception as e:
        st.error(f"Error: {e}")


def import_data_section():
    """Section to import alumni data from CSV/Excel."""
    st.subheader("📤 Import Alumni Data")
    
    st.markdown("""
    Upload a CSV or Excel file with alumni data. The file should have columns matching:
    - Name (required)
    - Batch
    - Roll Number
    - Gender
    - WhatsApp Number
    - Mobile Number
    - College Email
    - Personal Email
    - Corporate Email
    - LinkedIn ID
    - Current Company
    - Current Designation
    - Location
    """)
    
    uploaded_file = st.file_uploader("Choose a file", type=['csv', 'xlsx'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("Preview of uploaded data:")
            st.dataframe(df.head(10))
            
            # Column mapping
            st.markdown("**Map columns to database fields:**")
            
            column_mapping = {}
            db_fields = ['name', 'batch', 'roll_number', 'gender', 'whatsapp_number', 
                        'mobile_number', 'college_email', 'personal_email', 'corporate_email',
                        'linkedin_id', 'current_company', 'current_designation', 'current_location']
            
            cols = st.columns(3)
            for i, field in enumerate(db_fields):
                with cols[i % 3]:
                    mapped_col = st.selectbox(
                        f"{field}",
                        options=['-- Not Mapped --'] + list(df.columns),
                        key=f"map_{field}"
                    )
                    if mapped_col != '-- Not Mapped --':
                        column_mapping[field] = mapped_col
            
            if st.button("Import Data"):
                if 'name' not in column_mapping:
                    st.error("Name field must be mapped!")
                else:
                    session = get_db_session()
                    alumni_repo = AlumniRepository(session)
                    
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx, row in df.iterrows():
                        try:
                            alumni_data = {}
                            for db_field, csv_col in column_mapping.items():
                                value = row.get(csv_col)
                                if pd.notna(value):
                                    alumni_data[db_field] = str(value).strip()
                            
                            if alumni_data.get('name'):
                                alumni_repo.create(alumni_data)
                                success_count += 1
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Error importing row {idx}: {e}")
                        
                        progress = (idx + 1) / len(df)
                        progress_bar.progress(progress)
                        status_text.text(f"Processing... {idx + 1}/{len(df)}")
                    
                    status_text.empty()
                    st.success(f"✅ Import complete! Success: {success_count}, Errors: {error_count}")
        
        except Exception as e:
            st.error(f"Error reading file: {e}")


def display_statistics():
    """Display alumni statistics."""
    st.subheader("📊 Statistics")
    
    try:
        session = get_db_session()
        alumni_repo = AlumniRepository(session)
        stats = alumni_repo.get_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Alumni", stats.get('total_alumni', 0))
        
        with col2:
            st.metric("Batches", len(stats.get('by_batch', {})))
        
        with col3:
            st.metric("Companies", len(stats.get('top_companies', {})))
        
        # Batch distribution
        if stats.get('by_batch'):
            st.markdown("**Alumni by Batch**")
            batch_df = pd.DataFrame([
                {'Batch': k, 'Count': v} 
                for k, v in sorted(stats['by_batch'].items())
            ])
            st.bar_chart(batch_df.set_index('Batch'))
        
        # Top companies
        if stats.get('top_companies'):
            st.markdown("**Top Companies**")
            company_df = pd.DataFrame([
                {'Company': k, 'Count': v} 
                for k, v in stats['top_companies'].items()
            ])
            st.dataframe(company_df)
    
    except Exception as e:
        st.error(f"Error loading statistics: {e}")


def chatbot_page():
    """Chatbot interface for querying alumni data."""
    st.header("🤖 Alumni Chatbot")
    
    st.markdown("""
    Ask questions about alumni in natural language! Examples:
    - "Who works at Google?"
    - "Find alumni from batch 2020"
    - "List software engineers in Bangalore"
    """)
    
    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about alumni..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process query
        with st.chat_message("assistant"):
            response = process_chatbot_query(prompt)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})


def process_chatbot_query(query: str) -> str:
    """Process chatbot query and return response."""
    query_lower = query.lower()
    
    try:
        session = get_db_session()
        alumni_repo = AlumniRepository(session)
        
        results = []
        
        # Simple keyword matching for demo
        if 'company' in query_lower or 'works at' in query_lower or 'working at' in query_lower:
            # Extract company name
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() in ['at', 'company']:
                    if i + 1 < len(words):
                        company_name = ' '.join(words[i+1:]).strip('?.,!')
                        results = alumni_repo.search(company=company_name, limit=10)
                        break
        
        elif 'batch' in query_lower:
            # Extract batch year
            import re
            batch_match = re.search(r'\b(20\d{2})\b', query)
            if batch_match:
                batch_year = batch_match.group(1)
                results = alumni_repo.search(batch=batch_year, limit=10)
        
        elif 'location' in query_lower or 'in ' in query_lower:
            # Extract location
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() == 'in' and i + 1 < len(words):
                    location = ' '.join(words[i+1:]).strip('?.,!')
                    results = alumni_repo.search(location=location, limit=10)
                    break
        
        elif 'designation' in query_lower or 'title' in query_lower:
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() in ['designation', 'title', 'as']:
                    if i + 1 < len(words):
                        designation = ' '.join(words[i+1:]).strip('?.,!')
                        results = alumni_repo.search(designation=designation, limit=10)
                        break
        
        else:
            # General name search
            results = alumni_repo.search(name=query, limit=10)
        
        if results:
            response = f"Found {len(results)} alumni:\n\n"
            for alum in results[:5]:
                response += f"- **{alum.name}**"
                if alum.batch:
                    response += f" (Batch {alum.batch})"
                if alum.current_company:
                    response += f" - {alum.current_designation or 'Employee'} at {alum.current_company}"
                if alum.current_location:
                    response += f", {alum.current_location}"
                response += "\n"
            
            if len(results) > 5:
                response += f"\n... and {len(results) - 5} more"
            
            return response
        else:
            return "I couldn't find any alumni matching your query. Try searching by name, company, batch, or location."
    
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Alumni Management System",
        page_icon="🎓",
        layout="wide"
    )
    
    st.title("🎓 IIM Ranchi Alumni Management System")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Alumni Directory", "Chatbot", "Admin Panel"]
    )
    
    if page == "Alumni Directory":
        main_page()
    elif page == "Chatbot":
        chatbot_page()
    elif page == "Admin Panel":
        admin_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("Alumni Management System v1.0")


if __name__ == "__main__":
    main()
