import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import json

# Page config
st.set_page_config(
    page_title="Internship Selection Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {background-color: #f8f9fa;}
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {color: #1f2937;}
    h2 {color: #374151;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    .candidate-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        transition: all 0.3s;
    }
    .candidate-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85em;
    }
    .status-shortlisted {
        background-color: #d1fae5;
        color: #065f46;
    }
    .status-rejected {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .status-pending {
        background-color: #fef3c7;
        color: #92400e;
    }
    .status-contacted {
        background-color: #dbeafe;
        color: #1e40af;
    }
    .remarks-box {
        background: #f9fafb;
        padding: 10px;
        border-radius: 8px;
        border-left: 3px solid #6366f1;
        margin: 10px 0;
    }
    .document-link {
        display: inline-block;
        padding: 8px 16px;
        background: #6366f1;
        color: white;
        border-radius: 6px;
        text-decoration: none;
        margin: 5px;
        font-weight: 600;
    }
    .document-link:hover {
        background: #4f46e5;
    }
    .timeline-item {
        padding: 10px;
        border-left: 2px solid #e5e7eb;
        margin-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'shortlisted' not in st.session_state:
    st.session_state.shortlisted = set()
if 'rejected' not in st.session_state:
    st.session_state.rejected = set()
if 'remarks' not in st.session_state:
    st.session_state.remarks = {}
if 'contact_status' not in st.session_state:
    st.session_state.contact_status = {}
if 'interview_scheduled' not in st.session_state:
    st.session_state.interview_scheduled = {}
if 'ratings' not in st.session_state:
    st.session_state.ratings = {}

# Helper functions
@st.cache_data
def load_data(file):
    """Load and parse CSV data"""
    try:
        df = pd.read_csv(file)
        df['ID'] = range(len(df))
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def calculate_age(age_str):
    """Calculate age from date string"""
    try:
        if pd.isna(age_str) or age_str == '':
            return None
        birth_date = pd.to_datetime(age_str, format='%d-%m-%Y', errors='coerce')
        if pd.isna(birth_date):
            return None
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return None

def get_status(row_id):
    """Get application status"""
    if row_id in st.session_state.shortlisted:
        return "✅ Shortlisted"
    elif row_id in st.session_state.rejected:
        return "❌ Rejected"
    else:
        return "⏳ Pending"

def get_contact_status(row_id):
    """Get contact status"""
    return st.session_state.contact_status.get(row_id, "Not Contacted")

def add_remark(row_id, remark):
    """Add a remark to a candidate"""
    if row_id not in st.session_state.remarks:
        st.session_state.remarks[row_id] = []
    st.session_state.remarks[row_id].append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'remark': remark
    })

def get_remarks(row_id):
    """Get all remarks for a candidate"""
    return st.session_state.remarks.get(row_id, [])

def apply_filters(df, filters):
    """Apply all filters to dataframe"""
    filtered_df = df.copy()
    
    # Search filter
    if filters['search']:
        mask = filtered_df.astype(str).apply(
            lambda x: x.str.contains(filters['search'], case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[mask]
    
    # Categorical filters
    if filters['gender'] != 'All':
        filtered_df = filtered_df[filtered_df['Gender'] == filters['gender']]
    
    if filters['qualification'] != 'All':
        filtered_df = filtered_df[filtered_df['Your highest qualification'] == filters['qualification']]
    
    if filters['internship_type'] != 'All':
        filtered_df = filtered_df[filtered_df['Which type of internship would you prefer?'] == filters['internship_type']]
    
    if filters['laptop'] != 'All':
        filtered_df = filtered_df[filtered_df['Do you have a laptop?'] == filters['laptop']]
    
    if filters['smartphone'] != 'All':
        filtered_df = filtered_df[filtered_df['Do you have a smartphone?'] == filters['smartphone']]
    
    if filters['district'] != 'All':
        filtered_df = filtered_df[filtered_df['District of Residence'] == filters['district']]
    
    if filters['availability'] != 'All':
        filtered_df = filtered_df[filtered_df['Hours of internship you can provide'] == filters['availability']]
    
    # Contact status filter
    if filters['contact_status'] != 'All':
        if filters['contact_status'] == 'Contacted':
            filtered_df = filtered_df[filtered_df['ID'].isin(st.session_state.contact_status.keys())]
        elif filters['contact_status'] == 'Not Contacted':
            filtered_df = filtered_df[~filtered_df['ID'].isin(st.session_state.contact_status.keys())]
    
    # Interview filter
    if filters['interview_status'] != 'All':
        if filters['interview_status'] == 'Scheduled':
            filtered_df = filtered_df[filtered_df['ID'].isin(st.session_state.interview_scheduled.keys())]
        elif filters['interview_status'] == 'Not Scheduled':
            filtered_df = filtered_df[~filtered_df['ID'].isin(st.session_state.interview_scheduled.keys())]
    
    # Age filter
    if filters['min_age'] or filters['max_age']:
        filtered_df['Age'] = filtered_df['Your age as on date of application'].apply(calculate_age)
        if filters['min_age']:
            filtered_df = filtered_df[filtered_df['Age'] >= filters['min_age']]
        if filters['max_age']:
            filtered_df = filtered_df[filtered_df['Age'] <= filters['max_age']]
    
    # View mode filter
    if filters['view_mode'] == 'Shortlisted':
        filtered_df = filtered_df[filtered_df['ID'].isin(st.session_state.shortlisted)]
    elif filters['view_mode'] == 'Rejected':
        filtered_df = filtered_df[filtered_df['ID'].isin(st.session_state.rejected)]
    elif filters['view_mode'] == 'Pending':
        filtered_df = filtered_df[
            ~filtered_df['ID'].isin(st.session_state.shortlisted) & 
            ~filtered_df['ID'].isin(st.session_state.rejected)
        ]
    
    return filtered_df

def export_onboarding_package(row_id, df):
    """Export onboarding package for a candidate"""
    candidate = df[df['ID'] == row_id].iloc[0]
    remarks = get_remarks(row_id)
    
    package = {
        'Personal Information': {
            'Name': candidate['Your Full name'],
            'Email': candidate['Your Email id'],
            'Phone': candidate['Mobile number '],
            'Age': calculate_age(candidate['Your age as on date of application']),
            'Gender': candidate['Gender']
        },
        'Address': {
            'District': candidate['District of Residence'],
            'Police Station': candidate['Police station name of your place of residence '],
            'Full Address': candidate['Full address']
        },
        'Education': {
            'Qualification': candidate['Your highest qualification'],
            'Institution': candidate['Name of the campus (Highest qualification) '],
            'Year': candidate['Qualifying year']
        },
        'Technical Details': {
            'Has Laptop': candidate['Do you have a laptop?'],
            'Has Smartphone': candidate['Do you have a smartphone?'],
            'Skills': candidate['Tools and softwares you\'re familiar with'],
            'Languages': candidate['Languages you can speak']
        },
        'Internship Preferences': {
            'Type': candidate['Which type of internship would you prefer?'],
            'Availability': candidate['Hours of internship you can provide'],
            'Areas of Interest': candidate.get('Areas of Interest (only for those applying for Project Based Internships - 4 months).', 'N/A')
        },
        'Documents': {
            'Resume': candidate.get('Resume with photo upload', 'N/A'),
            'ID Proof': candidate.get('Enter a copy of your valid id proof', 'N/A')
        },
        'Selection History': {
            'Status': get_status(row_id),
            'Contact Status': get_contact_status(row_id),
            'Rating': st.session_state.ratings.get(row_id, 'Not Rated'),
            'Interview Scheduled': 'Yes' if row_id in st.session_state.interview_scheduled else 'No',
            'Remarks': remarks
        }
    }
    
    return json.dumps(package, indent=2)

# Main App
st.title("🎓 Internship Selection & Onboarding Platform")
st.markdown("### Complete Recruitment Management System")

# File upload
if st.session_state.df is None:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 📤 Upload Your CSV File")
        uploaded_file = st.file_uploader(
            "Upload internship applications CSV",
            type=['csv'],
            help="Upload the CSV file containing internship applications"
        )
        
        if uploaded_file:
            with st.spinner("Loading data..."):
                df = load_data(uploaded_file)
                if df is not None:
                    st.session_state.df = df
                    st.success(f"✅ Successfully loaded {len(df)} applications!")
                    st.rerun()
else:
    df = st.session_state.df
    
    # Sidebar - Filters
    with st.sidebar:
        st.header("🔍 Filters & Settings")
        
        # View mode
        view_mode = st.radio(
            "View Mode",
            ['All Applications', 'Shortlisted', 'Rejected', 'Pending'],
            help="Filter by application status"
        )
        
        st.markdown("---")
        
        # Search
        search_term = st.text_input("🔎 Search", placeholder="Search by name, email, etc.")
        
        st.markdown("---")
        st.subheader("📊 Filters")
        
        # Contact status filter
        contact_filter = st.selectbox("Contact Status", ['All', 'Contacted', 'Not Contacted'])
        
        # Interview status filter
        interview_filter = st.selectbox("Interview Status", ['All', 'Scheduled', 'Not Scheduled'])
        
        # Gender filter
        gender_options = ['All'] + sorted(df['Gender'].dropna().unique().tolist())
        gender_filter = st.selectbox("Gender", gender_options)
        
        # Qualification filter
        qual_options = ['All'] + sorted(df['Your highest qualification'].dropna().unique().tolist())
        qual_filter = st.selectbox("Qualification", qual_options)
        
        # Internship type filter
        internship_options = ['All'] + sorted(df['Which type of internship would you prefer?'].dropna().unique().tolist())
        internship_filter = st.selectbox("Internship Type", internship_options)
        
        # District filter
        district_options = ['All'] + sorted(df['District of Residence'].dropna().unique().tolist())
        district_filter = st.selectbox("District", district_options)
        
        # Laptop filter
        laptop_filter = st.selectbox("Has Laptop", ['All', 'Yes', 'No'])
        
        # Smartphone filter
        smartphone_filter = st.selectbox("Has Smartphone", ['All', 'Yes', 'No'])
        
        # Availability filter
        avail_options = ['All'] + sorted(df['Hours of internship you can provide'].dropna().unique().tolist())
        avail_filter = st.selectbox("Availability", avail_options)
        
        # Age range
        st.markdown("**Age Range**")
        col1, col2 = st.columns(2)
        with col1:
            min_age = st.number_input("Min", min_value=0, max_value=100, value=0, step=1)
        with col2:
            max_age = st.number_input("Max", min_value=0, max_value=100, value=0, step=1)
        
        if min_age == 0:
            min_age = None
        if max_age == 0:
            max_age = None
        
        st.markdown("---")
        
        # Sort by
        sort_by = st.selectbox(
            "Sort By",
            ['Submission Date (Newest)', 'Submission Date (Oldest)', 'Name (A-Z)', 'Name (Z-A)', 'Rating (High-Low)']
        )
        
        # Clear filters
        if st.button("🔄 Clear All Filters", width='stretch'):
            st.rerun()
        
        st.markdown("---")
        
        # Export options
        st.subheader("📥 Export")
        if st.button("Export Shortlisted", width='stretch'):
            shortlisted_df = df[df['ID'].isin(st.session_state.shortlisted)]
            if len(shortlisted_df) > 0:
                csv = shortlisted_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "shortlisted_candidates.csv",
                    "text/csv",
                    width='stretch'
                )
            else:
                st.warning("No shortlisted candidates")
        
        if st.button("Export Interview List", width='stretch'):
            interview_ids = list(st.session_state.interview_scheduled.keys())
            if interview_ids:
                interview_df = df[df['ID'].isin(interview_ids)].copy()
                interview_df['Interview Date'] = interview_df['ID'].map(st.session_state.interview_scheduled)
                csv = interview_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "interview_schedule.csv",
                    "text/csv",
                    width='stretch'
                )
            else:
                st.warning("No interviews scheduled")
    
    # Apply filters
    filters = {
        'search': search_term,
        'gender': gender_filter,
        'qualification': qual_filter,
        'internship_type': internship_filter,
        'district': district_filter,
        'laptop': laptop_filter,
        'smartphone': smartphone_filter,
        'availability': avail_filter,
        'min_age': min_age,
        'max_age': max_age,
        'view_mode': view_mode,
        'contact_status': contact_filter,
        'interview_status': interview_filter
    }
    
    filtered_df = apply_filters(df, filters)
    
    # Apply sorting
    if 'Newest' in sort_by:
        filtered_df = filtered_df.sort_values('Submission Date', ascending=False)
    elif 'Oldest' in sort_by:
        filtered_df = filtered_df.sort_values('Submission Date', ascending=True)
    elif 'A-Z' in sort_by:
        filtered_df = filtered_df.sort_values('Your Full name', ascending=True)
    elif 'Z-A' in sort_by:
        filtered_df = filtered_df.sort_values('Your Full name', ascending=False)
    elif 'Rating' in sort_by:
        filtered_df['Rating_Sort'] = filtered_df['ID'].map(lambda x: st.session_state.ratings.get(x, 0))
        filtered_df = filtered_df.sort_values('Rating_Sort', ascending=False)
    
    # Statistics
    st.markdown("---")
    st.header("📊 Dashboard Overview")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Applications", len(df))
    with col2:
        st.metric("Shortlisted", len(st.session_state.shortlisted), 
                 delta=f"{len(st.session_state.shortlisted)/len(df)*100:.1f}%")
    with col3:
        st.metric("Rejected", len(st.session_state.rejected),
                 delta=f"{len(st.session_state.rejected)/len(df)*100:.1f}%")
    with col4:
        pending = len(df) - len(st.session_state.shortlisted) - len(st.session_state.rejected)
        st.metric("Pending", pending,
                 delta=f"{pending/len(df)*100:.1f}%")
    with col5:
        st.metric("Contacted", len(st.session_state.contact_status))
    with col6:
        st.metric("Interviews", len(st.session_state.interview_scheduled))
    
    # Visualizations
    st.markdown("---")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Analytics", "👥 Applications", "📞 Contact Management", "🎯 Quick Actions", "📋 Onboarding"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Gender distribution
            gender_counts = df['Gender'].value_counts()
            fig_gender = px.pie(
                values=gender_counts.values,
                names=gender_counts.index,
                title="Gender Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_gender.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_gender, use_container_width=True)
            
            # Contact status
            contacted = len(st.session_state.contact_status)
            not_contacted = len(df) - contacted
            fig_contact = go.Figure(data=[
                go.Bar(x=['Contacted', 'Not Contacted'], y=[contacted, not_contacted],
                       marker_color=['#10b981', '#ef4444'])
            ])
            fig_contact.update_layout(title="Contact Status", xaxis_title="", yaxis_title="Count")
            st.plotly_chart(fig_contact, use_container_width=True)
        
        with col2:
            # Qualification distribution
            qual_counts = df['Your highest qualification'].value_counts()
            fig_qual = px.bar(
                x=qual_counts.values,
                y=qual_counts.index,
                orientation='h',
                title="Qualification Distribution",
                color=qual_counts.values,
                color_continuous_scale='Blues'
            )
            fig_qual.update_layout(showlegend=False, xaxis_title="Count", yaxis_title="")
            st.plotly_chart(fig_qual, use_container_width=True)
            
            # Selection funnel
            funnel_data = {
                'Stage': ['Applications', 'Contacted', 'Interview Scheduled', 'Shortlisted'],
                'Count': [len(df), len(st.session_state.contact_status), 
                         len(st.session_state.interview_scheduled), len(st.session_state.shortlisted)]
            }
            fig_funnel = go.Figure(go.Funnel(
                y=funnel_data['Stage'],
                x=funnel_data['Count'],
                textinfo="value+percent initial"
            ))
            fig_funnel.update_layout(title="Recruitment Funnel")
            st.plotly_chart(fig_funnel, use_container_width=True)
    
    with tab2:
        st.subheader(f"Applications ({len(filtered_df)} results)")
        
        if len(filtered_df) == 0:
            st.warning("No applications match the current filters.")
        else:
            # Pagination
            items_per_page = 5
            total_pages = (len(filtered_df) - 1) // items_per_page + 1
            
            col1, col2, col3 = st.columns([2, 3, 2])
            with col2:
                page = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    help=f"Total {total_pages} pages"
                )
            
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_df = filtered_df.iloc[start_idx:end_idx]
            
            for idx, row in page_df.iterrows():
                row_id = row['ID']
                status = get_status(row_id)
                age = calculate_age(row['Your age as on date of application'])
                contact_status = get_contact_status(row_id)
                remarks = get_remarks(row_id)
                rating = st.session_state.ratings.get(row_id, 0)
                
                # Status color
                if "Shortlisted" in status:
                    border_color = "#10b981"
                elif "Rejected" in status:
                    border_color = "#ef4444"
                else:
                    border_color = "#d1d5db"
                
                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 5px solid {border_color}; padding-left: 15px; margin-bottom: 20px; background: white; padding: 20px; border-radius: 10px;">
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        st.markdown(f"### {row['Your Full name']}")
                        st.markdown(f"**{status}** | Contact: **{contact_status}**")
                        st.markdown(f"⭐ Rating: {'⭐' * rating if rating > 0 else 'Not Rated'}")
                    
                    with col2:
                        st.markdown(f"📧 {row['Your Email id']}")
                        st.markdown(f"📱 {row['Mobile number ']}")
                        if age:
                            st.markdown(f"🎂 {age} years | {row['Gender']}")
                    
                    with col3:
                        st.markdown(f"**District:** {row['District of Residence']}")
                        st.markdown(f"**Qualification:** {row['Your highest qualification']}")
                        st.markdown(f"💻 Laptop: {row['Do you have a laptop?']} | 📱 Phone: {row['Do you have a smartphone?']}")
                    
                    with col4:
                        st.markdown(f"**Availability:**")
                        st.markdown(f"{row['Hours of internship you can provide']}")
                    
                    # Documents Section
                    st.markdown("---")
                    st.markdown("#### 📄 Documents & Resources")
                    doc_col1, doc_col2, doc_col3 = st.columns(3)
                    
                    with doc_col1:
                        resume_url = row.get('Resume with photo upload', '')
                        if resume_url and resume_url != 'N/A' and str(resume_url) != 'nan':
                            st.markdown(f'<a href="{resume_url}" target="_blank" class="document-link">📄 View Resume</a>', unsafe_allow_html=True)
                        else:
                            st.markdown("📄 Resume: Not Available")
                    
                    with doc_col2:
                        id_proof_url = row.get('Enter a copy of your valid id proof', '')
                        if id_proof_url and id_proof_url != 'N/A' and str(id_proof_url) != 'nan':
                            st.markdown(f'<a href="{id_proof_url}" target="_blank" class="document-link">🆔 View ID Proof</a>', unsafe_allow_html=True)
                        else:
                            st.markdown("🆔 ID Proof: Not Available")
                    
                    with doc_col3:
                        # Export candidate package
                        if st.button("📦 Export Package", key=f"export_{row_id}"):
                            package = export_onboarding_package(row_id, df)
                            st.download_button(
                                "⬇️ Download",
                                package,
                                f"{row['Your Full name']}_package.json",
                                "application/json",
                                key=f"download_{row_id}"
                            )
                    
                    # Remarks Section
                    st.markdown("---")
                    st.markdown("#### 💬 Remarks & Notes")
                    
                    if remarks:
                        for remark in remarks[-3:]:  # Show last 3 remarks
                            st.markdown(f"""
                            <div class="remarks-box">
                                <small><strong>{remark['timestamp']}</strong></small><br>
                                {remark['remark']}
                            </div>
                            """, unsafe_allow_html=True)
                        if len(remarks) > 3:
                            with st.expander(f"View all {len(remarks)} remarks"):
                                for remark in remarks:
                                    st.markdown(f"**{remark['timestamp']}**: {remark['remark']}")
                    else:
                        st.info("No remarks yet. Add your first note below.")
                    
                    # Add new remark
                    remark_col1, remark_col2 = st.columns([4, 1])
                    with remark_col1:
                        new_remark = st.text_area(
                            "Add Remark",
                            placeholder="E.g., Called candidate - confirmed availability, interested in position...",
                            key=f"remark_{row_id}",
                            height=80
                        )
                    with remark_col2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("💾 Save", key=f"save_remark_{row_id}", width='stretch'):
                            if new_remark.strip():
                                add_remark(row_id, new_remark)
                                st.success("Remark saved!")
                                st.rerun()
                    
                    # Expandable full details
                    with st.expander("📋 View Complete Profile"):
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            st.markdown(f"**Submission Date:** {row['Submission Date']}")
                            st.markdown(f"**Internship Type:** {row['Which type of internship would you prefer?']}")
                            st.markdown(f"**Campus:** {row['Name of the campus (Highest qualification) ']}")
                            st.markdown(f"**Qualifying Year:** {row['Qualifying year']}")
                            st.markdown(f"**Police Station:** {row['Police station name of your place of residence ']}")
                            st.markdown(f"**Address:** {row['Full address']}")
                        
                        with detail_col2:
                            st.markdown(f"**Languages:** {row['Languages you can speak']}")
                            if pd.notna(row['Have you been referred by any officer? ']):
                                st.markdown(f"**Referred By:** {row['Have you been referred by any officer? ']}")
                            if pd.notna(row['Tools and softwares you\'re familiar with']):
                                st.markdown(f"**Skills/Tools:**")
                                st.text(row['Tools and softwares you\'re familiar with'])
                            if pd.notna(row.get('Areas of Interest (only for those applying for Project Based Internships - 4 months).')):
                                st.markdown(f"**Areas of Interest:**")
                                st.text(row['Areas of Interest (only for those applying for Project Based Internships - 4 months).'])
                    
                    # Action buttons
                    st.markdown("---")
                    action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns(5)
                    
                    with action_col1:
                        if st.button("✅ Shortlist", key=f"short_{row_id}", width='stretch'):
                            st.session_state.shortlisted.add(row_id)
                            st.session_state.rejected.discard(row_id)
                            st.rerun()
                    
                    with action_col2:
                        if st.button("❌ Reject", key=f"reject_{row_id}", width='stretch'):
                            st.session_state.rejected.add(row_id)
                            st.session_state.shortlisted.discard(row_id)
                            st.rerun()
                    
                    with action_col3:
                        contact_options = ["Not Contacted", "Called - No Answer", "Called - Interested", 
                                         "Called - Not Interested", "Email Sent", "Follow-up Needed"]
                        current_contact = st.session_state.contact_status.get(row_id, "Not Contacted")
                        new_contact = st.selectbox(
                            "Contact Status",
                            contact_options,
                            index=contact_options.index(current_contact) if current_contact in contact_options else 0,
                            key=f"contact_{row_id}"
                        )
                        if new_contact != current_contact:
                            st.session_state.contact_status[row_id] = new_contact
                            st.rerun()
                    
                    with action_col4:
                        new_rating = st.selectbox(
                            "Rating",
                            [0, 1, 2, 3, 4, 5],
                            index=st.session_state.ratings.get(row_id, 0),
                            format_func=lambda x: "⭐" * x if x > 0 else "No Rating",
                            key=f"rating_{row_id}"
                        )
                        if new_rating != st.session_state.ratings.get(row_id, 0):
                            st.session_state.ratings[row_id] = new_rating
                            st.rerun()
                    
                    with action_col5:
                        if row_id not in st.session_state.interview_scheduled:
                            interview_date = st.date_input(
                                "Schedule Interview",
                                key=f"interview_{row_id}",
                                min_value=datetime.now().date()
                            )
                            if st.button("📅 Schedule", key=f"sched_{row_id}"):
                                st.session_state.interview_scheduled[row_id] = interview_date.strftime("%Y-%m-%d")
                                st.success("Interview scheduled!")
                                st.rerun()
                        else:
                            st.markdown(f"**Interview:**")
                            st.markdown(f"📅 {st.session_state.interview_scheduled[row_id]}")
                            if st.button("❌ Cancel", key=f"cancel_{row_id}"):
                                del st.session_state.interview_scheduled[row_id]
                                st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")
    
    with tab3:
        st.subheader("📞 Contact Management & Follow-ups")
        
        # Contact summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Contact Status Summary")
            if st.session_state.contact_status:
                contact_df = pd.DataFrame([
                    {'Status': status, 'Count': list(st.session_state.contact_status.values()).count(status)}
                    for status in set(st.session_state.contact_status.values())
                ])
                st.dataframe(contact_df, use_container_width=True, hide_index=True)
            else:
                st.info("No contacts made yet")
        
        with col2:
            st.markdown("### Pending Follow-ups")
            follow_ups = [id for id, status in st.session_state.contact_status.items() 
                         if 'Follow-up' in status or 'No Answer' in status]
            st.metric("Need Follow-up", len(follow_ups))
            
            if follow_ups and st.button("📋 View Follow-up List", width='stretch'):
                follow_up_df = df[df['ID'].isin(follow_ups)][['Your Full name', 'Your Email id', 'Mobile number ']]
                st.dataframe(follow_up_df, use_container_width=True, hide_index=True)
        
        with col3:
            st.markdown("### Interested Candidates")
            interested = [id for id, status in st.session_state.contact_status.items() 
                         if 'Interested' in status]
            st.metric("Interested", len(interested))
            
            if interested and st.button("📋 View Interested List", width='stretch'):
                interested_df = df[df['ID'].isin(interested)][['Your Full name', 'Your Email id', 'Mobile number ']]
                st.dataframe(interested_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Quick contact actions
        st.markdown("### Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Mark Multiple as Contacted")
            if st.button("Mark All Shortlisted as 'Email Sent'", width='stretch'):
                for id in st.session_state.shortlisted:
                    st.session_state.contact_status[id] = "Email Sent"
                st.success(f"Updated {len(st.session_state.shortlisted)} candidates!")
                st.rerun()
            
            if st.button("Mark All Filtered as 'Called - No Answer'", width='stretch'):
                for idx, row in filtered_df.iterrows():
                    st.session_state.contact_status[row['ID']] = "Called - No Answer"
                st.success(f"Updated {len(filtered_df)} candidates!")
                st.rerun()
        
        with col2:
            st.markdown("#### Export Contact Lists")
            if st.button("Export All Phone Numbers", width='stretch'):
                phone_df = df[['Your Full name', 'Mobile number ', 'Alternate Mobile number ']].copy()
                csv = phone_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "phone_numbers.csv",
                    "text/csv",
                    width='stretch'
                )
            
            if st.button("Export All Emails", width='stretch'):
                email_df = df[['Your Full name', 'Your Email id']].copy()
                csv = email_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download CSV",
                    csv,
                    "email_list.csv",
                    "text/csv",
                    width='stretch'
                )
    
    with tab4:
        st.subheader("🎯 Quick Selection Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Auto-Shortlist Criteria")
            
            if st.button("✅ Shortlist: Has Laptop + Smartphone", width='stretch'):
                count = 0
                for idx, row in filtered_df.iterrows():
                    if row['Do you have a laptop?'] == 'Yes' and row['Do you have a smartphone?'] == 'Yes':
                        st.session_state.shortlisted.add(row['ID'])
                        st.session_state.rejected.discard(row['ID'])
                        count += 1
                st.success(f"Auto-shortlisted {count} candidates!")
                st.rerun()
            
            if st.button("✅ Shortlist: Full-time Available", width='stretch'):
                count = 0
                for idx, row in filtered_df.iterrows():
                    if 'Full' in str(row['Hours of internship you can provide']):
                        st.session_state.shortlisted.add(row['ID'])
                        st.session_state.rejected.discard(row['ID'])
                        count += 1
                st.success(f"Auto-shortlisted {count} candidates!")
                st.rerun()
            
            if st.button("✅ Shortlist: Graduate/Engineer", width='stretch'):
                count = 0
                for idx, row in filtered_df.iterrows():
                    if row['Your highest qualification'] in ['Graduate', 'Engineer']:
                        st.session_state.shortlisted.add(row['ID'])
                        st.session_state.rejected.discard(row['ID'])
                        count += 1
                st.success(f"Auto-shortlisted {count} candidates!")
                st.rerun()
            
            if st.button("✅ Shortlist: Rated 4+ Stars", width='stretch'):
                count = 0
                for idx, row in filtered_df.iterrows():
                    if st.session_state.ratings.get(row['ID'], 0) >= 4:
                        st.session_state.shortlisted.add(row['ID'])
                        st.session_state.rejected.discard(row['ID'])
                        count += 1
                st.success(f"Auto-shortlisted {count} candidates!")
                st.rerun()
        
        with col2:
            st.markdown("#### Bulk Actions")
            
            if st.button("✅ Shortlist All Filtered", width='stretch'):
                for idx, row in filtered_df.iterrows():
                    st.session_state.shortlisted.add(row['ID'])
                    st.session_state.rejected.discard(row['ID'])
                st.success(f"Shortlisted {len(filtered_df)} candidates!")
                st.rerun()
            
            if st.button("❌ Reject All Filtered", width='stretch'):
                for idx, row in filtered_df.iterrows():
                    st.session_state.rejected.add(row['ID'])
                    st.session_state.shortlisted.discard(row['ID'])
                st.warning(f"Rejected {len(filtered_df)} candidates!")
                st.rerun()
            
            if st.button("🔄 Reset All Filtered to Pending", width='stretch'):
                for idx, row in filtered_df.iterrows():
                    st.session_state.shortlisted.discard(row['ID'])
                    st.session_state.rejected.discard(row['ID'])
                st.info(f"Reset {len(filtered_df)} candidates to pending!")
                st.rerun()
            
            if st.button("⭐ Auto-Rate by Qualification", width='stretch'):
                rating_map = {
                    'Engineer': 5,
                    'Graduate': 4,
                    'Post Graduate': 5,
                    'Diploma': 3,
                    'Intermediate': 2
                }
                count = 0
                for idx, row in filtered_df.iterrows():
                    qual = row['Your highest qualification']
                    if qual in rating_map:
                        st.session_state.ratings[row['ID']] = rating_map[qual]
                        count += 1
                st.success(f"Auto-rated {count} candidates!")
                st.rerun()
    
    with tab5:
        st.subheader("📋 Onboarding & Final Selection")
        
        # Onboarding pipeline
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Ready for Onboarding")
            ready_candidates = [id for id in st.session_state.shortlisted 
                              if id in st.session_state.contact_status 
                              and 'Interested' in st.session_state.contact_status[id]]
            st.metric("Candidates Ready", len(ready_candidates))
            
            if ready_candidates:
                if st.button("📋 View Ready Candidates", width='stretch'):
                    ready_df = df[df['ID'].isin(ready_candidates)][
                        ['Your Full name', 'Your Email id', 'Mobile number ', 'Your highest qualification']
                    ]
                    st.dataframe(ready_df, use_container_width=True, hide_index=True)
                
                if st.button("📦 Export Onboarding Package (All)", width='stretch'):
                    packages = []
                    for id in ready_candidates:
                        package = export_onboarding_package(id, df)
                        packages.append(package)
                    
                    combined = "[\n" + ",\n".join(packages) + "\n]"
                    st.download_button(
                        "⬇️ Download All Packages",
                        combined,
                        "onboarding_packages.json",
                        "application/json",
                        width='stretch'
                    )
        
        with col2:
            st.markdown("### Interview Scheduled")
            st.metric("Interviews", len(st.session_state.interview_scheduled))
            
            if st.session_state.interview_scheduled:
                interview_list = []
                for id, date in st.session_state.interview_scheduled.items():
                    candidate = df[df['ID'] == id].iloc[0]
                    interview_list.append({
                        'Name': candidate['Your Full name'],
                        'Date': date,
                        'Contact': candidate['Mobile number '],
                        'Email': candidate['Your Email id']
                    })
                
                interview_df = pd.DataFrame(interview_list).sort_values('Date')
                st.dataframe(interview_df, use_container_width=True, hide_index=True)
        
        with col3:
            st.markdown("### Top Rated Candidates")
            top_rated = sorted(
                [(id, rating) for id, rating in st.session_state.ratings.items() if rating >= 4],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            if top_rated:
                top_rated_ids = [id for id, _ in top_rated]
                top_df = df[df['ID'].isin(top_rated_ids)][['Your Full name', 'Your Email id']]
                top_df['Rating'] = top_df.index.map(lambda x: st.session_state.ratings.get(x, 0))
                st.dataframe(top_df, use_container_width=True, hide_index=True)
            else:
                st.info("No candidates rated yet")
        
        st.markdown("---")
        
        # Offer letter generation data
        st.markdown("### 📄 Offer Letter Data Export")
        st.info("Export selected candidates' data in format ready for offer letter generation")
        
        if st.session_state.shortlisted:
            offer_col1, offer_col2 = st.columns(2)
            
            with offer_col1:
                if st.button("Generate Offer Letter Data (Shortlisted)", width='stretch'):
                    shortlisted_candidates = df[df['ID'].isin(st.session_state.shortlisted)].copy()
                    
                    # Add selection metadata
                    shortlisted_candidates['Selection_Date'] = datetime.now().strftime("%Y-%m-%d")
                    shortlisted_candidates['Contact_Status'] = shortlisted_candidates['ID'].map(
                        lambda x: st.session_state.contact_status.get(x, 'Not Contacted')
                    )
                    shortlisted_candidates['Rating'] = shortlisted_candidates['ID'].map(
                        lambda x: st.session_state.ratings.get(x, 0)
                    )
                    shortlisted_candidates['Interview_Date'] = shortlisted_candidates['ID'].map(
                        lambda x: st.session_state.interview_scheduled.get(x, 'Not Scheduled')
                    )
                    
                    csv = shortlisted_candidates.to_csv(index=False)
                    st.download_button(
                        "⬇️ Download Offer Data",
                        csv,
                        "offer_letter_data.csv",
                        "text/csv",
                        width='stretch'
                    )
            
            with offer_col2:
                if st.button("Generate Summary Report", width='stretch'):
                    report = f"""
INTERNSHIP RECRUITMENT SUMMARY REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

OVERVIEW
========
Total Applications: {len(df)}
Shortlisted: {len(st.session_state.shortlisted)}
Rejected: {len(st.session_state.rejected)}
Pending Review: {len(df) - len(st.session_state.shortlisted) - len(st.session_state.rejected)}

CONTACT STATISTICS
==================
Total Contacted: {len(st.session_state.contact_status)}
Interested Candidates: {len([id for id, s in st.session_state.contact_status.items() if 'Interested' in s])}
Follow-ups Needed: {len([id for id, s in st.session_state.contact_status.items() if 'Follow-up' in s or 'No Answer' in s])}

INTERVIEW STATISTICS
====================
Interviews Scheduled: {len(st.session_state.interview_scheduled)}

RATINGS DISTRIBUTION
====================
5 Stars: {len([r for r in st.session_state.ratings.values() if r == 5])}
4 Stars: {len([r for r in st.session_state.ratings.values() if r == 4])}
3 Stars: {len([r for r in st.session_state.ratings.values() if r == 3])}
2 Stars: {len([r for r in st.session_state.ratings.values() if r == 2])}
1 Star: {len([r for r in st.session_state.ratings.values() if r == 1])}

READY FOR ONBOARDING
=====================
Candidates Ready: {len([id for id in st.session_state.shortlisted if id in st.session_state.contact_status and 'Interested' in st.session_state.contact_status[id]])}
                    """
                    
                    st.download_button(
                        "⬇️ Download Report",
                        report,
                        "recruitment_summary.txt",
                        "text/plain",
                        width='stretch'
                    )
    
    # Footer
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Reset All Selections", width='stretch'):
            st.session_state.shortlisted = set()
            st.session_state.rejected = set()
            st.success("All selections reset!")
            st.rerun()
    
    with col2:
        if st.button("💾 Save Progress", width='stretch'):
            progress_data = {
                'shortlisted': list(st.session_state.shortlisted),
                'rejected': list(st.session_state.rejected),
                'remarks': st.session_state.remarks,
                'contact_status': st.session_state.contact_status,
                'interview_scheduled': st.session_state.interview_scheduled,
                'ratings': st.session_state.ratings,
                'saved_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.download_button(
                "⬇️ Download Progress",
                json.dumps(progress_data, indent=2),
                "recruitment_progress.json",
                "application/json",
                width='stretch'
            )
    
    with col3:
        if st.button("📊 Download Full Report", width='stretch'):
            report_df = df.copy()
            report_df['Status'] = report_df['ID'].apply(get_status)
            report_df['Contact_Status'] = report_df['ID'].map(lambda x: st.session_state.contact_status.get(x, 'Not Contacted'))
            report_df['Rating'] = report_df['ID'].map(lambda x: st.session_state.ratings.get(x, 0))
            report_df['Interview_Date'] = report_df['ID'].map(lambda x: st.session_state.interview_scheduled.get(x, 'Not Scheduled'))
            
            csv = report_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download CSV",
                csv,
                "full_report.csv",
                "text/csv",
                width='stretch'
            )
    
    with col4:
        if st.button("🆕 Upload New File", width='stretch'):
            st.session_state.df = None
            st.session_state.shortlisted = set()
            st.session_state.rejected = set()
            st.session_state.remarks = {}
            st.session_state.contact_status = {}
            st.session_state.interview_scheduled = {}
            st.session_state.ratings = {}
            st.rerun()