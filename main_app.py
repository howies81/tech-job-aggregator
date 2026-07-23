import streamlit as st
import database as db


st.set_page_config(
    page_title= "Tech Job Hub",
    page_icon= "💼",
    layout="wide"
)

st.markdown(
    """
    <style>
    .job_card{
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        background-color: #f9f9f9;
        margin-bottom: 1rem;
    }
    .job-title {
        color: #1E3A8A;
        margin-bottom: 0.2rem !important;
    }
    .metadata-tag {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 0.2rem 0.6rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💼 Personal Tech Job Hub")

# 2. Workspace View Tabs
tab_feed, tab_pipeline = st.tabs(["🔍 All Jobs", "📂 Saved Jobs"])

with tab_feed:
    # Compact Filter Tray Container (Keeps main focus below)
    filter_and_search_controls = st.expander("⚙️ Filter & Search Controls", expanded=False)
    with filter_and_search_controls:
        job_col1, job_col2, job_col3 = st.columns(3)
        search_query = job_col1.text_input("Keywords", placeholder="Search title, company...")

        # Setup connections to database and retrieve jobs from jobs table in database
        # according to entered keywords
        with db.getConnection() as conn:
            raw_categories = [r[0] for r in\
            conn.execute("SELECT DISTINCT category FROM jobs WHERE category IS NOT NULL").fetchall()]
            raw_scopes = [r[0] for r in\
            conn.execute\
            ("SELECT DISTINCT location_scope FROM jobs WHERE location_scope IS NOT NULL").fetchall()]

            category_labels = {
            "software": "💻 Software Engineering",
            "software_development": "💻 Software Development",
            "frontend": "🎨 Frontend Development",
            "backend": "⚙️ Backend Development",
            "fullstack": "🥞 Full Stack Development",
            "devops": "🚀 DevOps & Infrastructure",
            "devops_and_infrastructure": "🚀 DevOps & Infrastructure",
            "design": "📐 UI/UX & Design",
            "web_and_app_design": "📐 UI/UX & Design",
            "marketing": "📈 Sales & Marketing",
            "data_science": "📊 Data Science",
            "data_science_and_analytics": "📊 Data Science & Analytics",
            "data_and_analytics ": "📊 Data & Analytics",
            "data": "📊 Data Engineering",
            "python": "🐍 Python Specific",
            "product_management": "📋 Product Management",
            "artificial_intelligence": "🤖 Artificial Intelligence",
            "engineering": "🛠️ General Engineering",
            "information_technology": "🖥️ Information Technology",
            "other": "✨ Other Technical Roles"
        }

            scope_labels = {
                "remote_worldwide": "🌍 Worldwide (Anywhere)",
                "remote_us_only": "🇺🇸 United States Only",
                "remote_uk_only": "🇬🇧 United Kingdom Only",
                "remote_eu_only": "🇪🇺 European Union Only",
                "remote_europe": "Europe Only",
                "remote_emea": "Emea Only",
                "remote_latam": "💃 Latin America Only",
                "remote_tz_restricted": "⏳ Timezone Restricted",
                "remote_location_restricted": "📍 Location Restricted"
            }

            # 3. Create the drop-down lists using the pretty labels
            # If a database tag isn't in our dictionary, capitalize it as a backup fallback
            ui_categories = ["All Categories"] + [category_labels.get(cat, cat.replace('_', ' ').title()) for cat in raw_categories]
            ui_scopes = ["All Locations"] + [scope_labels.get(sc, sc.replace('_', ' ').title()) for sc in raw_scopes]

            category_selection = job_col2.selectbox("Category", ui_categories)
            scope_selection = job_col3.selectbox("Geographic Scope", ui_scopes)

            category_to_query = "All"
            if category_selection != "All Categories":
                category_to_query = next((k for k,v in category_labels.items() if v == category_selection), "All")

            scope_to_query = "All"
            if scope_selection != "All Locations":
                scope_to_query = next((k for k,v in scope_labels.items() if v == scope_selection), "All")

            
            

    jobs = db.search_jobs(
    keywords=[search_query] if search_query else None,
    categories=[category_to_query] if category_to_query != "All" else None,
    scopes=[scope_to_query] if scope_to_query != "All" else None
    )

    #print(len(jobs))

# 5. Rendering the Main Focus Feed
    st.subheader(f"📋 Latest Openings ({len(jobs)} showing)")

    if not jobs:
        st.info("No jobs match your active filters. Try adjusting your keywords!")

    for job in jobs:
    # Wrap each card in a clean container
        with st.container():
            st.markdown(f"""
                <div class="job_card">
                    <h3 class="job-title"><a href="{job['link']}" target="_blank">{job['title']}</a></h3>
                    <div style="font-weight: 500; color: #4B5563; margin-bottom: 0.5rem;">🏢 {job['company']}</div>
                    <div style="margin-bottom: 0.8rem;">
                        <span class="metadata-tag">🌐 {job['location_scope']}</span>
                        <span class="metadata-tag">⏱️ {job['job_type'] or 'N/A'}</span>
                        <span class="metadata-tag">📡 {job['job_board']}</span>
                        <span class="metadata-tag">📅 Scraped: {job['date_scraped']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Action controls neatly tucked into the card footer
            act_col1, act_col2 = st.columns([1, 5])
            with act_col1:
                # Unique key constraint per loop using row ID
                if st.button("⭐ Save Job", key=f"save_{job['id']}"):
                    db.save_job(job['id'], status='saved')
                    st.success("Saved!")
                    st.rerun()
            with act_col2:
                with st.expander("📖 View Full Description"):
                    st.write(job['job_description'])
            st.markdown("<br>", unsafe_allow_html=True)   

with tab_pipeline:
    st.subheader("📂 Your Application Tracker")
    saved_jobs = db.get_saved_jobs()
    
    if not saved_jobs:
        st.info("You haven't bookmarked any jobs yet! Browse the Live Feed to save openings.")
        
    for s_job in saved_jobs:
        with st.container():
            st.markdown(f"### {s_job['title']} — *{s_job['company']}*")
            
            p_col1, p_col2 = st.columns([2, 4])
            with p_col1:
                # Tracking application status via dynamic updating dropdown
                pipeline_statuses = ['saved', 'applied', 'interviewing', 'offered', 'rejected']
                current_idx = pipeline_statuses.index(s_job['job_status']) if s_job['job_status'] in pipeline_statuses else 0
                
                new_status = st.selectbox(
                    "Pipeline Stage", 
                    pipeline_statuses, 
                    index=current_idx, 
                    key=f"status_{s_job['id']}"
                )
                
                if new_status != s_job['job_status']:
                    db.update_saved_job_status(s_job['id'], new_status)
                    st.toast(f"Updated status to {new_status}!")
                    st.rerun()
            with p_col2:
                st.write(f"**Saved on:** {s_job['date_saved']} | **Source Link:** [Apply Here]({s_job['link']})")
            st.markdown("---")