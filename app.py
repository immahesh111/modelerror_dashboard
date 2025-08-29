import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import time

# Page configuration
st.set_page_config(
    page_title="Modelwise Error Codes Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for styling with custom theme integration
st.markdown("""
<style>
    /* Main styling respecting Streamlit theme variables */
    .main-header {
        font-size: clamp(1.8rem, 4vw, 3rem);
        font-weight: 700;
        color: var(--text-color, #000000);
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        padding: 1rem 0;
    }
    
    .sub-header {
        font-size: clamp(1.2rem, 3vw, 1.8rem);
        font-weight: 600;
        color: var(--text-color, #000000);
        margin-bottom: 1.5rem;
        border-bottom: 2px solid var(--secondary-background-color, #1db5f7);
        padding-bottom: 0.5rem;
    }
    
    /* Modern metric cards */
    .metric-card {
        background: linear-gradient(135deg, var(--secondary-background-color, #1db5f7) 0%, #357abd 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    /* Professional table styling with dynamic column widths */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-radius: 8px;
        overflow: hidden;
    }
    
    .custom-table th {
        background-color: var(--secondary-background-color, #1db5f7) !important;
        color: var(--text-color, #000000) !important;
        font-weight: bold !important;
        padding: 12px 15px;
        text-align: left;
        border-bottom: 2px solid #87ceeb;
        font-size: 0.9rem;
    }
    
    .custom-table td {
        background-color: #ffffff !important;
        color: var(--text-color, #000000) !important;
        padding: 10px 15px;
        border-bottom: 1px solid #e0e0e0;
        font-size: 0.85rem;
    }
    
    .custom-table tr:hover td {
        background-color: #f8f9fa !important;
    }
    
    /* Dark theme adjustments for better visibility */
    .stApp[data-theme="dark"] .main-header {
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .sub-header {
        color: #e0f7fa !important;
        border-bottom-color: var(--secondary-background-color, #1db5f7) !important;
    }
    
    .stApp[data-theme="dark"] .metric-card {
        background: linear-gradient(135deg, #01579b 0%, #0277bd 100%) !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .info-card {
        background: linear-gradient(135deg, #37474f 0%, #263238 100%) !important;
        border-color: #546e7a !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .custom-table th {
        background-color: #01579b !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .custom-table td {
        background-color: #263238 !important;
        color: #ffffff !important;
    }
    
    .stApp[data-theme="dark"] .custom-table tr:hover td {
        background-color: #37474f !important;
    }
    
    /* Dynamic column widths based on content */
    .custom-table th, .custom-table td {
        min-width: 100px;
        max-width: 300px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Mobile responsive table */
    @media (max-width: 768px) {
        .custom-table {
            font-size: 0.8rem;
        }
        
        .custom-table th,
        .custom-table td {
            padding: 8px 10px;
        }
        
        .stDataFrame {
            overflow-x: auto;
        }
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    .stApp[data-theme="dark"] .sidebar .sidebar-content {
        background: linear-gradient(180deg, #263238 0%, #37474f 100%) !important;
    }
    
    /* Modern selectbox styling */
    .stSelectbox > div > div {
        background-color: #ffffff;
        border: 2px solid var(--secondary-background-color, #1db5f7);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus {
        border-color: #357abd;
        box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
    }
    
    /* Professional cards */
    .info-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s ease;
    }
    
    .info-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Status indicators */
    .status-good {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-critical {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, var(--secondary-background-color, #1db5f7), #357abd);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(74, 144, 226, 0.3);
    }
    
    /* Loading animation */
    .loading {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-radius: 50%;
        border-top: 3px solid var(--secondary-background-color, #1db5f7);
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1rem;
            margin: 0.25rem;
        }
        
        .info-card {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# MongoDB connection with error handling
@st.cache_resource
def init_connection():
    try:
        MONGO_URI = "mongodb+srv://nsneditz111_db_user:gK4RIMYPNjIW8JRV@mqscluster.ahth286.mongodb.net/?retryWrites=true&w=majority&appName=mqscluster"
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client["error_data"]
    except Exception as e:
        st.error(f"🔴 Database connection failed: {str(e)}")
        return None

# Data fetching functions
@st.cache_data(ttl=300)
def get_models():
    db = init_connection()
    if db is not None:
        try:
            return db.list_collection_names()
        except Exception as e:
            st.error(f"Error fetching models: {str(e)}")
            return []
    return []

@st.cache_data(ttl=300)
def get_model_data(model, shift=None):
    db = init_connection()
    if db is not None:
        try:
            coll = db[model]
            query = {}
            if shift:
                query["shift"] = shift
            data = list(coll.find(query))
            return pd.DataFrame(data) if data else pd.DataFrame()
        except Exception as e:
            st.error(f"Error fetching data for {model}: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

def display_custom_table(df, height=500):
    """Display a custom-styled dataframe with professional table styling and dynamic column widths"""
    if df.empty:
        st.warning("📋 No data available")
        return
    
    # Clean the dataframe
    display_df = df.copy()
    if '_id' in display_df.columns:
        display_df = display_df.drop('_id', axis=1)
    
    # Calculate max content length for each column to set dynamic widths
    col_widths = {}
    for col in display_df.columns:
        # Convert all values to strings and find the max length
        max_len = max(display_df[col].astype(str).str.len().max(), len(str(col)))
        # Convert character length to approximate pixel width (assuming ~8px per character)
        col_widths[col] = min(max(100, max_len * 8), 300)  # Min 100px, max 300px

    # Apply styling using Pandas Styler
    styled_df = display_df.style.set_table_styles([
        {'selector': 'thead th', 'props': 'background-color: var(--secondary-background-color, #1db5f7); color: var(--text-color, #000000); font-weight: bold; text-align: left; padding: 12px 15px; border-bottom: 2px solid #87ceeb; font-size: 0.9rem;'},
        {'selector': 'tbody td', 'props': 'background-color: #ffffff; color: var(--text-color, #000000); padding: 10px 15px; border-bottom: 1px solid #e0e0e0; font-size: 0.85rem;'},
        {'selector': 'tr:hover td', 'props': 'background-color: #f8f9fa;'},
    ]).set_table_attributes('class="custom-table"')
    
    # Apply dynamic column widths
    for col in display_df.columns:
        styled_df = styled_df.set_properties(**{f'width': f'{col_widths[col]}px', 'max-width': f'{col_widths[col]}px'}, subset=[col])
    
    # Display with custom styling
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=height,
        hide_index=True
    )

def main():
    # Header
    st.markdown('<h1 class="main-header">🏭 Modelwise Error Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("## 🔧 Dashboard Controls")
        
        # Auto-refresh
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
        
        # Model selection
        models = get_models()
        if not models:
            st.error("⚠️ No models available")
            return
        
        selected_model = st.selectbox(
            "📱 Select Model",
            options=models,
            help="Choose a model to view error data",
            index=0
        )
        
        # Shift selection
        shift_options = {
            "All Shifts": None,
            "Shift 1 (7AM - 7PM)": 1,
            "Shift 2 (7PM - 7AM)": 2
        }
        selected_shift = st.selectbox(
            "⏰ Shift Filter",
            options=list(shift_options.keys()),
            help="Filter by production shift"
        )
        
        # Refresh button
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Info section
        st.markdown("---")
        st.markdown("### ℹ️ Information")
        st.info("💡 Select a model to view detailed error analysis and testcode data.")
    
    if not selected_model:
        st.warning("👆 Please select a model from the sidebar")
        return
    
    # Load data for selected model
    with st.spinner('Loading data...'):
        df = get_model_data(selected_model, shift_options[selected_shift])
    
    if df.empty:
        st.warning(f"📋 No data found for model: **{selected_model}**")
        return
    
    # Main dashboard layout
    st.markdown(f'<h2 class="sub-header">📱 {selected_model} - Error Analysis</h2>', unsafe_allow_html=True)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    total_errors = len(df)
    unique_testcodes = len(df['Testcode'].unique()) if 'Testcode' in df.columns else 0
    unique_units = len(df['Track Id'].unique()) if 'Track Id' in df.columns else 0
    
    # Calculate error rate
    error_rate = (total_errors / unique_units * 100) if unique_units > 0 else 0
    
    with col1:
        st.metric("🔢 Total Errors", total_errors)
    with col2:
        st.metric("🔍 Unique Testcodes", unique_testcodes)
    with col3:
        st.metric("📦 Affected Units", unique_units)
    with col4:
        st.metric("📊 Error Rate", f"{error_rate:.1f}%")
    
    # Process filter (only filter available)
    if 'Process' in df.columns:
        st.markdown("### 🔍 Filter Options")
        col1, col2 = st.columns([1, 3])
        with col1:
            processes = ['All Processes'] + sorted(df['Process'].unique().tolist())
            selected_process = st.selectbox("Process Filter:", processes)
        
        # Apply process filter
        if selected_process != 'All Processes':
            df = df[df['Process'] == selected_process]
            st.info(f"🔍 Filtered by Process: **{selected_process}** | {len(df)} records")
    
    # Main data table
    st.markdown("### 📊 Error Data Table")
    
    if not df.empty:
        # Prepare data for display
        display_df = df.copy()
        
        # Reorder columns for better presentation
        priority_columns = ['Track Id', 'Testcode', 'Process']
        other_columns = [col for col in display_df.columns if col not in priority_columns and col != '_id']
        column_order = [col for col in priority_columns if col in display_df.columns] + other_columns
        display_df = display_df[column_order]
        
        # Display the table
        display_custom_table(display_df, height=600)
        
        # Download section
        st.markdown("### 📥 Export Data")
        col1, col2 = st.columns([1, 3])
        with col1:
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="📁 Download CSV",
                data=csv,
                file_name=f"{selected_model}_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # Quick insights section
    if 'Testcode' in df.columns and not df.empty:
        st.markdown("### 📈 Quick Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top error codes
            top_errors = df['Testcode'].value_counts().head(5)
            if not top_errors.empty:
                st.markdown("**🔥 Top 5 Error Codes:**")
                for i, (testcode, count) in enumerate(top_errors.items(), 1):
                    status_class = "status-critical" if count >= 10 else "status-warning" if count >= 5 else "status-good"
                    st.markdown(f"{i}. `{testcode}` - <span class='{status_class}'>{count} occurrences</span>", 
                               unsafe_allow_html=True)
        
        with col2:
            # Process breakdown
            if 'Process' in df.columns:
                process_counts = df['Process'].value_counts()
                if not process_counts.empty:
                    st.markdown("**⚙️ Process Distribution:**")
                    for process, count in process_counts.items():
                        percentage = (count / len(df)) * 100
                        st.markdown(f"• {process}: **{count}** ({percentage:.1f}%)")

# Footer
def show_footer():
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: var(--text-color, #666); padding: 20px; font-size: 0.9rem;'>
            <p>🏭 <strong>Manufacturing Error Dashboard</strong> | 
            Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 
            Built with ❤️ By Process Team</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Adjust footer color for dark theme
    st.markdown("""
    <style>
    .stApp[data-theme="dark"] [style*="color: #666"] {
        color: #bbbbbb !important;
    }
    </style>
    """, unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
    show_footer()