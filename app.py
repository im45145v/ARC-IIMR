import streamlit as st
import os
from dotenv import load_dotenv

# Initialize environment variables
load_dotenv()

# Streamlit Page Config
st.set_page_config(
    page_title="IIM Alumni Intelligence Dashboard",
    page_icon="🎓",
    layout="wide"
)

# App Header
st.markdown("""
# 🎓 IIM Alumni Intelligence Dashboard  
Welcome to your centralized alumni intelligence platform.

Use the sidebar to navigate across modules. Toggle between **Manager View** (high level KPIs) and **Data View** (detailed tables).
---
""")

# Sidebar Navigation Info
st.sidebar.title("📂 Navigation")

st.sidebar.markdown("""
### Modules
- 🏠 **Dashboard** — Overview & insights  
- 📊 **Explore Data** — Filter, search, export  
- 🤖 **AI Search** — Semantic alumni search  
- 📝 **Add / Edit Data** — Manage alumni info  
- 🧰 **Admin Tools** — Mapping, cleanup, quality  
- 💻 **SQL Runner** — Safe SQL playground  
""")


# Footer
st.markdown("""
<hr>
<center>
Built with ❤️ using Streamlit & Supabase  
</center>
""")
