import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
import pytz
import altair as alt
import re

# --- 1. THEME & PAGE CONFIG ---
st.set_page_config(page_title="McGill Dragon Boat Z Attendance", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Teko:wght@600;700&display=swap');
    
    /* Background & Layout */

    [data-testid="stAppViewContainer"] { 
        background: radial-gradient(circle at 50% 0%, rgba(255, 51, 51, 0.12) 0%, #0e1117 75%) !important; 
        color: #e0e0e0; 
        font-family: 'Inter', sans-serif; 
    }
    [data-testid="stSidebar"] { 
        background-color: rgba(14, 17, 23, 0.4) !important; 
        backdrop-filter: blur(20px) !important; 
        border-right: 1px solid rgba(43, 45, 49, 0.5) !important; 
    }

    hr { border: none !important; height: 1px !important; background: linear-gradient(90deg, transparent, rgba(255, 51, 51, 0.5), transparent) !important; margin: 2rem 0 !important; }

    /* Typography */

    /* Liquid Shimmer Title */
    @keyframes textShine {
        to { background-position: 200% center; }
    }
    .main-title { 
        text-align: center; 
        font-family: 'Teko', sans-serif; 
        font-weight: 800; 
        font-size: 5.5rem; 
        text-transform: uppercase; 
        /* The liquid gradient */
        background: linear-gradient(to right, #ff3333 20%, #ff7a7a 40%, #ffffff 50%, #ff7a7a 60%, #ff3333 80%);
        background-size: 200% auto; 
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        animation: textShine 3s linear infinite; /* Controls the speed of the shine */
        margin-bottom: 0px; 
        padding-bottom: 0px; 
        letter-spacing: -1.5px; 
        filter: drop-shadow(0px 4px 15px rgba(255, 51, 51, 0.25)); 
    }
    .sub-title { text-align: center; font-family: 'Inter', sans-serif; font-weight: 600; font-size: 2rem; color: #8b8d91; margin-top: -5px; margin-bottom: 30px; letter-spacing: -0.5px; }
    .instructions { text-align: center; font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #a0a0a5; max-width: 850px; margin: 0 auto; line-height: 1.6; background: #16181c; padding: 20px; border-radius: 12px; border: 1px solid #2b2d31; }
    
    /* Inputs */

    /* 3. Glassmorphic Dropdown Portals */
    div[data-baseweb="popover"] > div {
        background-color: rgba(22, 24, 28, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(43, 45, 49, 0.8) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }
    /* Style the hover state of items inside the dropdown list */
    ul[role="listbox"] li:hover {
        background-color: rgba(255, 51, 51, 0.15) !important;
        color: #ff3333 !important;
    }

    .stSelectbox label { font-family: 'Inter', sans-serif !important; font-size: 1.4rem !important; font-weight: 600; color: #ffffff !important; text-align: center; }
    div[data-baseweb="select"] > div { background-color: #1a1c23 !important; border-radius: 12px !important; border: 1px solid #3a3d45 !important; }
    
    /* Buttons with Pulse Glow */
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 5px rgba(255, 51, 51, 0.2); }
        50% { box-shadow: 0 0 20px rgba(255, 51, 51, 0.6); }
        100% { box-shadow: 0 0 5px rgba(255, 51, 51, 0.2); }
    }
    .stButton>button { 
        background-color: #ff3333 !important; 
        color: white !important; 
        height: 3.2rem; 
        font-size: 1.1rem; 
        font-weight: 600; 
        font-family: 'Inter', sans-serif; 
        border-radius: 12px; 
        border: None; 
        width: 100%; 
        transition: all 0.3s ease; 
        animation: pulseGlow 3s infinite;
    }
    .stButton>button:hover { 
        background-color: #ff4d4d !important; 
        transform: translateY(-2px); 
        animation: none; 
        box-shadow: 0 6px 15px rgba(255, 51, 51, 0.5) !important; 
    }

    /* Cards & Lists */
    .roster-card { background-color: rgba(22, 24, 28, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 16px; border: 1px solid rgba(43, 45, 49, 0.8); border-top: 4px solid #ff3333; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); transition: all 0.3s ease; }
    .roster-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(255, 51, 51, 0.15); border-color: #4a4d55; }
    .roster-title { color: #ffffff; font-weight: 600; font-family: 'Inter', sans-serif; font-size: 1.2rem; margin-bottom: 12px; border-bottom: 1px solid #2b2d31; padding-bottom: 8px; }
    .paddler-list { font-family: 'Inter', sans-serif; font-size: 1.05rem; line-height: 1.6; color: #a0a0a5; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { height: 40px; background-color: #16181c; border-radius: 50px !important; border: 1px solid #2b2d31; padding: 0px 20px; font-weight: 600; font-family: 'Inter', sans-serif; color: #8b8d91; }
    /* Modern Subtle Active Tab Style */
    .stTabs [aria-selected="true"] { 
        background-color: rgba(255, 51, 51, 0.15) !important; 
        color: #ff7a7a !important; 
        border-color: rgba(255, 51, 51, 0.5) !important; 
        box-shadow: 0 4px 12px rgba(255, 51, 51, 0.2);
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
    
    /* Mobile Responsive */
    @media (max-width: 768px) { .main-title { font-size: 2.5rem; letter-spacing: -1px; } .sub-title { font-size: 1.4rem; } .instructions { font-size: 1rem; padding: 15px; text-align: left; } .stSelectbox label { font-size: 1.2rem !important; } .stTabs [data-baseweb="tab-list"] { display: flex; flex-direction: column; gap: 8px; } }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0e1117; }
    ::-webkit-scrollbar-thumb { background: #2b2d31; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #ff3333; }

    /* Clean Expanders */
    [data-testid="stExpander"] { background-color: rgba(22, 24, 28, 0.4); border-radius: 12px; border: 1px solid #2b2d31; }
    [data-testid="stExpander"] summary { transition: background-color 0.3s ease; }
    [data-testid="stExpander"] summary:hover { background-color: rgba(43, 45, 49, 0.5); }

    /* --- ADVANCED MICRO-INTERACTIONS --- */
    
    /* 1. Custom Text Selection Highlight */
    ::selection { 
        background: rgba(255, 51, 51, 0.4); 
        color: #ffffff; 
    }
    
    /* 2. DBZ Focus Rings (Replaces Default Streamlit Blue) */
    div[data-baseweb="input"] > div:focus-within, 
    div[data-baseweb="select"] > div:focus-within {
        border-color: #ff3333 !important;
        box-shadow: 0 0 0 1px #ff3333 !important;
    }
    
    /* 3. Interactive Resource Containers */
    [data-testid="stVerticalBlockBorderWrapper"] { 
        transition: all 0.3s ease; 
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover { 
        transform: translateY(-2px); 
        border-color: rgba(255, 51, 51, 0.5) !important; 
        box-shadow: 0 4px 12px rgba(255, 51, 51, 0.1);
    }

    /* 4. Secondary Link Button Hover States */
    [data-testid="baseButton-secondary"] { 
        transition: all 0.2s ease; 
    }
    [data-testid="baseButton-secondary"]:hover {
        border-color: #ff3333 !important;
        color: #ff3333 !important;
        background-color: rgba(255, 51, 51, 0.05) !important;
    }

    /* Tactile Form Inputs */
    [data-testid="stRadio"] label, [data-testid="stCheckbox"] label {
        transition: color 0.2s ease, transform 0.2s ease;
    }
    [data-testid="stRadio"] label:hover, [data-testid="stCheckbox"] label:hover {
        color: #ff7a7a !important;
        transform: translateX(4px); /* Gently nudges the text to the right on hover */
    }

    /* Magnetic Sidebar Navigation */
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        border: none !important;
        border-left: 3px solid transparent !important;
        border-radius: 0 12px 12px 0 !important;
        justify-content: flex-start !important;
        padding-left: 15px !important;
        box-shadow: none !important;
        animation: none !important; /* Removes the pulse from sidebar buttons */
    }
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255, 51, 51, 0.1) !important;
        border-left: 3px solid #ff3333 !important;
        color: #ffffff !important;
        transform: translateX(6px) !important;
    }

    /* 5. Waiver Box Highlight */
    [data-testid="stVerticalBlockBorderWrapper"]:has(.waiver-hook) {
        border-color: rgba(255, 51, 51, 0.6) !important;
        box-shadow: 0 4px 15px rgba(255, 51, 51, 0.15) !important;
        background-color: rgba(255, 51, 51, 0.03) !important;
    }

    /* Fluid Entrance Animations */
    @keyframes fadeSlideUp {
        0% { opacity: 0; transform: translateY(15px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .roster-card, [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stExpander"] {
        animation: fadeSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    .roster-card {
    position: relative;
    overflow: hidden;
}
.roster-card:hover::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(800px circle at var(--mouse-x) var(--mouse-y), rgba(255, 51, 51, 0.15), transparent 40%);
    pointer-events: none;
}

    /* Custom Centered App Banners */
    .app-banner {
        text-align: center;
        background-color: rgba(22, 24, 28, 0.7);
        backdrop-filter: blur(12px);
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(43, 45, 49, 0.8);
        color: #a0a0a5;
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        max-width: 600px;
        margin: 20px auto;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .app-banner-success {
        border-color: rgba(0, 230, 118, 0.4);
        background-color: rgba(0, 230, 118, 0.05);
        color: #00e676;
    }

    @keyframes borderRotate {
    100% { filter: hue-rotate(360deg); }
    }
    .glowing-border-box {
        border: 2px solid transparent;
        background: linear-gradient(#16181c, #16181c) padding-box, linear-gradient(45deg, #ff3333, #ff7a7a, #2b2d31) border-box;
        border-radius: 16px;
    }   

    /* Custom Action Button Colors */
    /* Green Add Button */
    div.stFormSubmitButton > button:has-text("Add to Roster") {
        background-color: #00e676 !important;
        color: #0e1117 !important;
        font-weight: 700 !important;
    }
    div.stFormSubmitButton > button:has-text("Add to Roster"):hover {
        background-color: #00c853 !important;
    }

    /* Blue Save Changes Button */
    div.stFormSubmitButton > button:has-text("Save Changes") {
        background-color: #4dabf7 !important;
        color: #0e1117 !important;
        font-weight: 700 !important;
    }
    div.stFormSubmitButton > button:has-text("Save Changes"):hover {
        background-color: #339af0 !important;
    }

    /* Red Delete Button */
    div.stFormSubmitButton > button:has-text("Delete") {
        background-color: #ff3333 !important;
        color: white !important;
        font-weight: 700 !important;
    }
    div.stFormSubmitButton > button:has-text("Delete"):hover {
        background-color: #e02828 !important;
    }

</style>
""", unsafe_allow_html=True)


# --- 2. TIME GATE & DYNAMIC DATES ---
tz = pytz.timezone("America/Toronto")
now = datetime.now(tz)
effective_now = now - timedelta(hours=20)
effective_monday = effective_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=effective_now.weekday())

thurs_dt = effective_monday + timedelta(days=3, hours=19)
circuit_dt = effective_monday + timedelta(days=4, hours=17) 
fri_dt = effective_monday + timedelta(days=4, hours=18)

def format_date(d, time_str):
    suffix = 'th' if 11 <= d.day <= 13 else {1:'st', 2:'nd', 3:'rd'}.get(d.day % 10, 'th')
    return f"{d.strftime('%A, %B')} {d.day}{suffix} {time_str}"

thurs_str = format_date(thurs_dt, "7:00 PM - 8:00 PM [Pool]")
circuit_str = format_date(circuit_dt, "5:00 PM - 6:00 PM [Circuit]")
fri_str = format_date(fri_dt, "6:00 PM - 7:00 PM [Pool]")

TIMESLOTS = {thurs_str: thurs_dt, circuit_str: circuit_dt, fri_str: fri_dt}

is_open = False
if now.weekday() == 0 and now.hour >= 20: 
    is_open = True
elif 1 <= now.weekday() <= 4:
    if now.weekday() == 4 and now.hour >= 19: 
        is_open = False
    else:
        is_open = True

# --- 3. SUPABASE CONNECTION & CACHING ---
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

@st.cache_data(ttl=60)
def load_roster():
    res = supabase.table("roster").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["Name", "True Side", "Gender"])

@st.cache_data(ttl=60)
def load_live_data():
    signups = supabase.table("signups").select("*").execute()
    waitlist = supabase.table("waitlist").select("*").execute()
    df_s = pd.DataFrame(signups.data) if signups.data else pd.DataFrame(columns=["id", "Timestamp", "Practice Date", "Name", "Status"])
    df_w = pd.DataFrame(waitlist.data) if waitlist.data else pd.DataFrame(columns=["id", "Timestamp", "Practice Date", "Name", "Side", "Status"])
    return df_s, df_w

def log_action(action, details):
    supabase.table("audit_log").insert({"Action": action, "Details": details}).execute()

@st.cache_data(ttl=60)
def load_audit_log():
    res = supabase.table("audit_log").select("*").order("Timestamp", desc=True).execute()
    df_audit = pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "Timestamp", "Action", "Details"])
    
    if not df_audit.empty:
        df_audit['Timestamp'] = pd.to_datetime(df_audit['Timestamp']).dt.tz_convert('America/Toronto').dt.strftime('%b %d, %Y - %I:%M %p')
        
    return df_audit

def get_week_label(date_str):
    match = re.search(r', ([A-Za-z]+ \d+)', date_str)
    if match:
        try:
            # Extract the month and day
            extracted_date = match.group(1)
            parsed_month = datetime.strptime(extracted_date.split()[0], "%B").month
            
            # If we are in early 2027 looking at late 2026, subtract a year
            target_year = now.year
            if now.month <= 3 and parsed_month >= 10:
                target_year -= 1
                
            dt = datetime.strptime(f"{extracted_date} {target_year}", "%B %d %Y")
            monday = dt - timedelta(days=dt.weekday())
            return f"Week of {monday.strftime('%B %-d, %Y')}"
        except:
            pass
    return date_str

df_roster = load_roster()
df_signups, df_waitlist = load_live_data()

if 'Gender' not in df_roster.columns:
    df_roster['Gender'] = 'Unknown'
else:
    df_roster['Gender'] = df_roster['Gender'].replace(r'^\s*$', 'Unknown', regex=True).fillna('Unknown')
    df_roster['Gender'] = df_roster['Gender'].replace({'Male': 'Open', 'Female': 'Women', 'M': 'Open', 'F': 'Women'})

historical_dates = []
historical_weeks = {}

if not df_signups.empty:
    all_dates = df_signups['Practice Date'].unique().tolist()
    historical_dates = [d for d in all_dates if d not in TIMESLOTS.keys()]
    historical_dates.reverse() 

    for d in historical_dates:
        w_label = get_week_label(d)
        if w_label not in historical_weeks:
            historical_weeks[w_label] = []
        historical_weeks[w_label].append(d)
# --- 4. SESSION STATE & SIDEBAR ROUTING ---
if 'page' not in st.session_state:
    st.session_state.page = "Sign Up"
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False

with st.sidebar:
    st.header("Navigation")

    # --- Quick UI Upgrade: Live Activity Pill ---
    active_count = len(df_signups[df_signups['Status'].isin(['Active', 'Attended'])]) if not df_signups.empty else 0
    st.markdown(f"""
    <div style="background: rgba(255, 51, 51, 0.08); border: 1px solid rgba(255, 51, 51, 0.2); border-radius: 8px; padding: 8px 12px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 0.8rem; font-weight: 600; color: #a0a0a5; text-transform: uppercase; letter-spacing: 0.5px;">Active Signups</span>
        <span style="background-color: #ff3333; color: white; font-weight: 800; font-size: 0.75rem; padding: 2px 8px; border-radius: 12px; box-shadow: 0 0 8px rgba(255,51,51,0.4);">{active_count}</span>
    </div>
    """, unsafe_allow_html=True)


    if st.button("Sign Up Portal", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.page = "Sign Up"
        st.rerun()
    if st.button("Current Lineups", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.current_user = None  
        st.session_state.page = "Lineups"
        st.rerun()
    if st.button("Analytics Dashboard", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.current_user = None  
        st.session_state.page = "Analytics"
        st.rerun()
    if st.button("Team Resources", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.current_user = None  
        st.session_state.page = "Resources"
        st.rerun()
    if st.button("Admin Dashboard", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.current_user = None  
        st.session_state.page = "Admin"
        st.rerun()

    st.markdown("""
    <div style="margin-top: 40px; padding: 12px; background: rgba(0, 230, 118, 0.05); border: 1px solid rgba(0, 230, 118, 0.2); border-radius: 10px; display: flex; align-items: center; gap: 10px;">
        <div style="width: 8px; height: 8px; background-color: #00e676; border-radius: 50%; box-shadow: 0 0 8px #00e676; animation: pulseGlow 2s infinite;"></div>
        <div style="font-size: 0.85rem; font-weight: 600; color: #00e676; letter-spacing: 0.5px;">DATABASE SYNCD</div>
    </div>
    """, unsafe_allow_html=True)

def render_card_header(ts_string):
    match = re.match(r"(.*?)\s+(\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M)\s*\[(.*?)\]", ts_string)
    
    if match:
        date_val = match.group(1)
        time_val = match.group(2)
        type_val = match.group(3).upper()
        
        # Explicitly check each unique timeslot to prevent overlapping rule conditions
        tier_tag = ""
        if "[Circuit]" in ts_string:
            tier_tag = '<div style="display: inline-block; background-color: rgba(77, 171, 247, 0.15); border: 1px solid rgba(77, 171, 247, 0.4); color: #4dabf7; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; margin-left: 6px;">For All</div>'
        elif "7:00 PM" in time_val and "Thursday" in date_val:
            tier_tag = '<div style="display: inline-block; background-color: rgba(255, 122, 122, 0.15); border: 1px solid rgba(255, 122, 122, 0.4); color: #ff7a7a; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; margin-left: 6px;">Intermediate / Advanced</div>'
        elif "6:00 PM" in time_val and "Friday" in date_val:
            tier_tag = '<div style="display: inline-block; background-color: rgba(0, 230, 118, 0.15); border: 1px solid rgba(0, 230, 118, 0.4); color: #00e676; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; margin-left: 6px;">Beginner-Friendly / Back-To-Basics</div>'

        st.markdown(f"""
        <div style="margin-bottom: 15px;">
            <div>
                <div style="display: inline-block; background-color: rgba(255, 51, 51, 0.15); border: 1px solid rgba(255, 51, 51, 0.5); box-shadow: 0 0 12px rgba(255, 51, 51, 0.3); color: #ff7a7a; padding: 4px 14px; border-radius: 20px; font-weight: 800; font-size: 0.85rem; letter-spacing: 1.5px; margin-bottom: 8px;">{type_val}</div>
                {tier_tag}
            </div>
            <div style="color: #ffffff; font-weight: 600; font-size: 1.1rem; margin-top: 4px;">{date_val}</div>
            <div style="color: #a0a0a5; font-size: 0.95rem; margin-top: 2px;">{time_val}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"#### {ts_string}")

def render_roster_card(ts_str, status_filter=['Active', 'Attended']):
    is_circuit = "[Circuit]" in ts_str
    
    if not df_signups.empty:
        ts_active = df_signups[(df_signups['Practice Date'] == ts_str) & (df_signups['Status'].isin(status_filter))]
        
        if is_circuit:
            # For Circuit: Just grab all signed-up names directly, no side separation needed
            attendees = ts_active['Name'].tolist()
            total_count = len(attendees)
            pct = min((total_count / 24) * 100, 100)
            empty_state_html = "<span style='color: #4a4d55; font-style: italic;'>Spots Available</span>"
            
            st.markdown(f"""
            <div class='roster-card'>
                <div class='roster-title'>Total Circuit Signups ({total_count}/24)</div>
                <div style="width: 100%; background-color: #2b2d31; border-radius: 4px; height: 6px; margin-top: -4px; margin-bottom: 12px;">
                    <div style="width: {pct}%; background-color: #ff3333; height: 100%; border-radius: 4px; transition: width 0.5s ease;"></div>
                </div>
                <div class='paddler-list'>{"<br>".join(attendees) if attendees else empty_state_html}</div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # For Pool: Keep the side-balanced Left (16) vs Right (16) layout
            merged = pd.merge(ts_active, df_roster, on="Name", how="left")
            lefts = merged[merged['True Side'] == 'Left']['Name'].tolist()
            rights = merged[merged['True Side'] == 'Right']['Name'].tolist()
            ambis = merged[merged['True Side'].isin(['Unknown', 'Ambidextrous'])]['Name'].tolist()
            
            for name in ambis:
                if len(lefts) <= len(rights):
                    lefts.append(name + " (A)")
                else:
                    rights.append(name + " (A)")
                    
            left_pct = min((len(lefts) / 16) * 100, 100)
            right_pct = min((len(rights) / 16) * 100, 100)
            empty_state_html = "<span style='color: #4a4d55; font-style: italic;'>Seats Available</span>"
            
            st.markdown(f"""
            <div class='roster-card'>
                <div style='display: flex; justify-content: space-between;'>
                    <div style='width: 48%;'>
                        <div class='roster-title'>Left ({len(lefts)}/16)</div>
                        <div style="width: 100%; background-color: #2b2d31; border-radius: 4px; height: 6px; margin-top: -4px; margin-bottom: 12px;">
                            <div style="width: {left_pct}%; background-color: #ff3333; height: 100%; border-radius: 4px; transition: width 0.5s ease;"></div>
                        </div>
                        <div class='paddler-list'>{"<br>".join(lefts) if lefts else empty_state_html}</div>
                    </div>
                    <div style='width: 48%;'>
                        <div class='roster-title'>Right ({len(rights)}/16)</div>
                        <div style="width: 100%; background-color: #2b2d31; border-radius: 4px; height: 6px; margin-top: -4px; margin-bottom: 12px;">
                            <div style="width: {right_pct}%; background-color: #ff3333; height: 100%; border-radius: 4px; transition: width 0.5s ease;"></div>
                        </div>
                        <div class='paddler-list'>{"<br>".join(rights) if rights else empty_state_html}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Fallback for empty state
        if is_circuit:
            st.markdown("""
            <div class='roster-card'>
                <div class='roster-title'>Total Circuit Signups (0/24)</div>
                <div class='paddler-list'><span style='color: #4a4d55; font-style: italic;'>Spots Available</span></div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='roster-card'>
                <div style='display: flex; justify-content: space-between;'>
                    <div style='width: 48%;'><div class='roster-title'>Left (0/16)</div><div class='paddler-list'>Seats Available</div></div>
                    <div style='width: 48%;'><div class='roster-title'>Right (0/16)</div><div class='paddler-list'>Seats Available</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    if not df_waitlist.empty and 'Active' in status_filter: 
        wl = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
        wl_names = wl['Name'].tolist()
        if wl_names:
            st.markdown("**Waitlist:**")
            st.markdown(f"<div class='paddler-list'>" + "<br>".join([f"{i+1}. {n}" for i, n in enumerate(wl_names)]) + "</div>", unsafe_allow_html=True)

# --- 5. PAGE 1: CURRENT LINEUPS ---
if st.session_state.page == "Lineups":
    st.markdown('<h1 class="main-title">Team Lineups</h1>', unsafe_allow_html=True)
    st.divider()
    
    current_week_label = f"📅 Week of {effective_monday.strftime('%B %-d')} (Current Week)"
    with st.expander(current_week_label, expanded=True):
        c1, c2, c3 = st.columns(3)
        cols = [c1, c2, c3]
        for idx, (ts_str, ts_dt) in enumerate(TIMESLOTS.items()):
            with cols[idx]:
                render_card_header(ts_str) # Replaces the messy markdown
                render_roster_card(ts_str, ['Active', 'Attended'])
            
    if historical_weeks:
        st.divider()
        st.markdown("### Historical Lineups")
        for week_label, dates in historical_weeks.items():
            with st.expander(f"📅 {week_label}", expanded=False):
                cols = st.columns(len(dates) if len(dates) > 0 else 1)
                for idx, past_date in enumerate(dates):
                    with cols[idx]:
                        render_card_header(past_date) # Replaces the messy markdown
                        render_roster_card(past_date, ['Active', 'Attended'])

# --- 6. PAGE 2: ANALYTICS DASHBOARD ---
elif st.session_state.page == "Analytics":
    st.markdown('<h1 class="main-title">Team Analytics</h1>', unsafe_allow_html=True)
    st.divider()
    
    active_signups = df_signups[df_signups['Status'].isin(['Active', 'Attended'])] if not df_signups.empty else pd.DataFrame()
    
    # 1. Calculate the total number of weeks dynamically
    all_dates = df_signups['Practice Date'].unique().tolist() if not df_signups.empty else []
    pool_dates = [d for d in all_dates if '[Pool]' in d]
    circuit_dates = [d for d in all_dates if '[Circuit]' in d]
    
    num_pool_weeks = len(set(get_week_label(d) for d in pool_dates))
    num_circuit_weeks = len(set(get_week_label(d) for d in circuit_dates))
    
    pool_counts = pd.DataFrame(columns=['Name', 'Pool Practices'])
    circuit_counts = pd.DataFrame(columns=['Name', 'Circuit Practices'])
    practice_counts = pd.DataFrame(columns=['Practice Date', 'Paddlers'])
    
    if not active_signups.empty:
        # 2. Split active signups into Pool vs Circuit
        pool_signups = active_signups[active_signups['Practice Date'].str.contains('[Pool]', regex=False)]
        circuit_signups = active_signups[active_signups['Practice Date'].str.contains('[Circuit]', regex=False)]
        
        pool_counts = pool_signups['Name'].value_counts().reset_index()
        pool_counts.columns = ['Name', 'Pool Practices']
        
        circuit_counts = circuit_signups['Name'].value_counts().reset_index()
        circuit_counts.columns = ['Name', 'Circuit Practices']
        
        practice_counts = active_signups.groupby('Practice Date').size().reset_index(name='Paddlers')
        
    # 3. Merge counts with the Master Roster
    analytics_df = df_roster.copy()
    analytics_df = pd.merge(analytics_df, pool_counts, on='Name', how='left')
    analytics_df = pd.merge(analytics_df, circuit_counts, on='Name', how='left')
    
    analytics_df['Pool Practices'] = analytics_df['Pool Practices'].fillna(0).astype(int)
    analytics_df['Circuit Practices'] = analytics_df['Circuit Practices'].fillna(0).astype(int)

    analytics_df = analytics_df.sort_values(by="Name", ascending=True).reset_index(drop=True)

    # 4. Calculate Independent Attendance Rates (Allows >100% via Walk-ins)
    if num_pool_weeks > 0:
        analytics_df['Pool Attendance Rate'] = ((analytics_df['Pool Practices'] / num_pool_weeks) * 100).round(1).astype(str) + '%'
    else:
        analytics_df['Pool Attendance Rate'] = '0%'
        
    if num_circuit_weeks > 0:
        analytics_df['Circuit Attendance Rate'] = ((analytics_df['Circuit Practices'] / num_circuit_weeks) * 100).round(1).astype(str) + '%'
    else:
        analytics_df['Circuit Attendance Rate'] = '0%'

    # 5. Reorganize Columns for the Master Database display
    display_cols = ['Name', 'Membership', 'True Side', 'Gender', 'Pool Practices', 'Pool Attendance Rate', 'Circuit Practices', 'Circuit Attendance Rate']
    extra_cols = [c for c in analytics_df.columns if c not in display_cols]
    analytics_df = analytics_df[display_cols + extra_cols]

    tab1, tab2, tab3 = st.tabs(["📊 Master Database", "🧩 Team Composition", "📈 Attendance Trends"])
    
    with tab1:
        st.markdown("### Interactive Master Database")

        # --- 1. Glassmorphic KPI Summary Cards ---
        st.markdown(f"""
        <div style="display: flex; gap: 20px; margin-bottom: 25px;">
            <div style="flex: 1; background-color: rgba(22, 24, 28, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 12px; border: 1px solid rgba(43, 45, 49, 0.8); border-left: 4px solid #ff3333; animation: fadeSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
                <div style="color: #a0a0a5; font-weight: 600; font-size: 0.9rem; text-transform: uppercase;">Total Active Roster</div>
                <div style="font-family: 'Teko', sans-serif; font-size: 3rem; font-weight: 800; color: white; line-height: 1.1;">{len(df_roster)}</div>
            </div>
            <div style="flex: 1; background-color: rgba(22, 24, 28, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 12px; border: 1px solid rgba(43, 45, 49, 0.8); border-left: 4px solid #6c6f78; animation: fadeSlideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
                <div style="color: #a0a0a5; font-weight: 600; font-size: 0.9rem; text-transform: uppercase;">Total Practices Logged</div>
                <div style="font-family: 'Teko', sans-serif; font-size: 3rem; font-weight: 800; color: white; line-height: 1.1;">{len(active_signups)}</div>
            </div>
            <div style="flex: 1; background-color: rgba(22, 24, 28, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 12px; border: 1px solid rgba(43, 45, 49, 0.8); border-left: 4px solid #ff7a7a; animation: fadeSlideUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;">
                <div style="color: #a0a0a5; font-weight: 600; font-size: 0.9rem; text-transform: uppercase;">Waitlist Demand</div>
                <div style="font-family: 'Teko', sans-serif; font-size: 3rem; font-weight: 800; color: white; line-height: 1.1;">{len(df_waitlist)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


        c1, c2 = st.columns(2)
        with c1: side_filter = st.multiselect("Filter by Side", analytics_df['True Side'].unique())
        with c2: gender_filter = st.multiselect("Filter by Gender", analytics_df['Gender'].unique())
            
        filtered_df = analytics_df.copy()
        if side_filter: filtered_df = filtered_df[filtered_df['True Side'].isin(side_filter)]
        if gender_filter: filtered_df = filtered_df[filtered_df['Gender'].isin(gender_filter)]
        
        # --- 2. Styled Pandas Dataframe with Interactive Hover ---
        styled_df = filtered_df.style.set_properties(**{
            'background-color': '#16181c',
            'color': '#a0a0a5',
            'border-color': '#2b2d31'
        }).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#0e1117'), ('color', '#ffffff'), ('border-color', '#2b2d31')]},
            {'selector': 'tr:hover td', 'props': [('background-color', 'rgba(255, 51, 51, 0.1) !important'), ('color', '#ffffff !important')]}
        ])
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### Overall Composition")
        c1, c2, c3 = st.columns(3)
        
        # Modern Donut Chart Function
        def render_modern_donut(data_series, category_title, color_range):
            df_chart = data_series.reset_index()
            df_chart.columns = [category_title, 'Count']
            
            chart = alt.Chart(df_chart).mark_arc(
                innerRadius=65, 
                cornerRadius=6, 
                stroke="#16181c", # Matches card background for negative space gaps
                strokeWidth=3
            ).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(
                    field=category_title, 
                    type="nominal", 
                    scale=alt.Scale(
                        domain=df_chart[category_title].tolist(),
                        range=color_range
                    ),
                    legend=alt.Legend(title=category_title, titleColor="#ffffff", labelColor="#a0a0a5", orient="bottom")
                ),
                tooltip=[category_title, 'Count']
            ).properties(height=320).configure_view(strokeWidth=0)
            
            return chart

        # Aesthetic Color Palettes
        side_colors = ["#ff3333", "#ff7a7a", "#6c6f78", "#2b2d31"]
        gender_colors = ["#ff3333", "#8b8d91", "#3a3d45"]
        mem_colors = ["#ff3333", "#ff7a7a", "#ff9e9e", "#6c6f78", "#2b2d31"]

        with c1:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Side Distribution</h4>", unsafe_allow_html=True)
            st.altair_chart(render_modern_donut(analytics_df['True Side'].value_counts(), 'Side', side_colors), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Gender Distribution</h4>", unsafe_allow_html=True)
            st.altair_chart(render_modern_donut(analytics_df['Gender'].value_counts(), 'Gender', gender_colors), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Membership Tiers</h4>", unsafe_allow_html=True)
            st.altair_chart(render_modern_donut(analytics_df['Membership'].value_counts(), 'Membership', mem_colors), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        st.markdown("### Gender & Side Breakdown")
        c3, c4 = st.columns(2)
        side_categories = ['Left', 'Right', 'Ambidextrous', 'Unknown']
        
        with c3:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Open Roster</h4>", unsafe_allow_html=True)
            open_df = analytics_df[analytics_df['Gender'] == 'Open']
            open_dist = open_df['True Side'].value_counts().reindex(side_categories, fill_value=0)
            st.altair_chart(render_modern_donut(open_dist, 'Side', side_colors), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c4:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Women Roster</h4>", unsafe_allow_html=True)
            women_df = analytics_df[analytics_df['Gender'] == 'Women']
            women_dist = women_df['True Side'].value_counts().reindex(side_categories, fill_value=0)
            st.altair_chart(render_modern_donut(women_dist, 'Side', side_colors), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        

    with tab3:
        st.markdown("### Historical Practice Turnout")
        
        if not active_signups.empty:
            def get_session_type(d_str):
                if "Thursday" in d_str: return "Thursday Pool"
                elif "[Circuit]" in d_str: return "Friday Circuit"
                elif "Friday" in d_str and "[Pool]" in d_str: return "Friday Pool"
                return "Other"
            
            trend_df = active_signups.copy()
            trend_df['Session'] = trend_df['Practice Date'].apply(get_session_type)
            
            valid_sessions = ["Thursday Pool", "Friday Circuit", "Friday Pool"]
            sessions_available = [s for s in valid_sessions if s in trend_df['Session'].values]
            
            selected_sessions = st.multiselect("Filter by Session", sessions_available, default=sessions_available)
            
            if selected_sessions:
                filtered_trend = trend_df[trend_df['Session'].isin(selected_sessions)]
                
                if not filtered_trend.empty:
                    chart_data = filtered_trend.groupby(['Practice Date', 'Session']).size().reset_index(name='Paddlers')
                    
                    # Added interpolate='monotone' for smooth, organic curves instead of sharp angles
                    chart = alt.Chart(chart_data).mark_line(point=True, strokeWidth=3, interpolate='monotone').encode(
                        x=alt.X('Practice Date:N', sort=None, axis=alt.Axis(labelAngle=-45, labelColor='#a0a0a5')),
                        y=alt.Y('Paddlers:Q', axis=alt.Axis(labelColor='#a0a0a5', gridColor='#2b2d31')),
                        color=alt.Color('Session:N', scale=alt.Scale(
                            domain=valid_sessions, 
                            range=["#ff3333", "#6c6f78", "#ff7a7a"]
                        )),
                        tooltip=['Session', 'Practice Date', 'Paddlers']
                    ).properties(height=350).configure_view(strokeWidth=0).configure_legend(
                        titleColor='#ffffff', labelColor='#a0a0a5', orient='top'
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No data available for the selected sessions.")
            else:
                st.warning("Please select at least one session to view trends.")
        else:
            st.markdown("<div class='app-banner'>Not enough data yet. Complete a few practices to see trends!</div>", unsafe_allow_html=True)

# --- NEW PAGE: TEAM RESOURCES ---
elif st.session_state.page == "Resources":
    st.markdown('<h1 class="main-title">Team Resources</h1>', unsafe_allow_html=True)
    st.divider()
    
    # 1. Executive Members Popover (Centered and reduced width)
    pop_c1, pop_c2, pop_c3 = st.columns([1, 2, 1])
    with pop_c2:
        with st.popover("2026-2027 Executive Members", use_container_width=True):
            st.markdown("### DBZ Executive Team")
            st.markdown("""
            * **President:** Wei Heng Gao
            * **Co-President:** David Namgung
            * **VP Internal:** Catherine Zhu, Fangrui Xu
            * **VP External:** Felicia Xie, Rui Zhu, Evelyn Liu
            * **VP Events:** William Kallianiotis, Cassandra Duong
            * **VP Social:** Lina Zheng, Lea Tian, Chelsea Zhang
            * **VP Finance:** Andy Li
            * **VP Logistics:** Avery Kim
            * **VP Fitness:** Orlando Qiu, Ceres Brunet, Houwen Yao, Kia Takhsha, Jennifer Tram Su
            """)
            st.markdown("### DBZ Coaching Staff")
            st.markdown("""
            * **Carmen Sweetoo**
            * **Feng Yang Chen**
            """)
        
    st.markdown("<br>", unsafe_allow_html=True)

    # --- NEW: Mandatory Waiver Box (Centered and slightly constrained) ---
    w_c1, w_c2, w_c3 = st.columns([1, 4, 1])
    with w_c2:
        with st.container(border=True):
            st.markdown(
                "<h4 style='display: inline-block; color: #ff3333; background-color: rgba(255, 51, 51, 0.1); padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(255, 51, 51, 0.4); box-shadow: 0 0 10px rgba(255, 51, 51, 0.15); margin-bottom: 8px;'>📝 MANDATORY Team Waiver</h4>", 
                unsafe_allow_html=True
            )
            st.caption("Please ensure you have filled out the official team waiver for the current season before attending any practices.")
            st.link_button("Fill out Google Form Waiver", "https://docs.google.com/forms/d/e/1FAIpQLSdVb6vBQDv0YqJ8weO52RpT-ekvMumnIMSLVga2SLYBYlcukA/viewform?usp=publish-editor", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.divider()
    
    # 2. Resource Card Grid (Changed from 2 columns to 3 columns)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("#### ℹ️ Fall 2026 Information Session")
            st.caption("Missed the Information Session?")
            st.link_button("Open Slides", "https://canva.link/bj2ock01gq6bp59", use_container_width=True)
            
        with st.container(border=True):
            st.markdown("#### 🩹 Injury Prevention Guide")
            st.caption("Prevent injuries during the year.")
            st.link_button("Read Guidelines", "https://docs.google.com/document/d/1VjugbUaSLyP1ChlYMlROkeLu9mJ1FXuyizIRI8bc8-A/edit?usp=sharing", use_container_width=True)
            
        with st.container(border=True):
            st.markdown("#### 🏆 Competition Preparation")
            st.caption("Preparation docs ahead of any competitions")
            st.link_button("View Checklists", "https://docs.google.com/document/d/1P-CBhKYLZ1EYMQgBo90BJFmbPkWR780hu3OnCRb_qAM/edit?usp=sharing", use_container_width=True)

    with col2:
        with st.container(border=True):
            st.markdown("#### 🚇 Transit Guide")
            st.caption("How to get to Canal Fitness via Bus and Metro")
            st.link_button("View Route Map", "https://docs.google.com/document/d/1ip7_Wmi4wuVdmcIbPUp993xwF7i3KOuwKcSp0Wl_yx8/edit?usp=sharing", use_container_width=True)
            
        with st.container(border=True):
            st.markdown("#### 🐉 Dragon Boat 101")
            st.caption("A guide stating the different teams in Montreal, competitions and our club.")
            st.link_button("Read Guide", "https://docs.google.com/document/d/1aECu-CS_SJqLzacokfgaGeppBZmYdOYQyNL_TyNtCtk/edit?usp=sharing", use_container_width=True)
            
        with st.container(border=True):
            st.markdown("#### 🎥 YouTube Channel")
            st.caption("Check out our races!")
            st.link_button("Watch Videos", "https://www.youtube.com/@mcgilldragonboatz", use_container_width=True)

    with col3:
        with st.container(border=True):
            st.markdown("#### ⏱️ DBZ Racing History")
            st.caption("List of DBZ Races with the times and rankings")
            st.link_button("View Rankings", "https://docs.google.com/spreadsheets/d/1I4GCgein1PvvQIoD1g4VcViRa6WTIgu1HAwT-JJtNV8/edit?usp=sharing", use_container_width=True)
            
        with st.container(border=True):
            st.markdown("#### 📜 DBZ Management History")
            st.caption("Documented history of our club.")
            st.link_button("Read History", "https://docs.google.com/document/d/1OmqWDTVmkPXhYEDlX2H2jxcSyBEvUNy4hFscLRg6ah0/edit?usp=sharing", use_container_width=True)

    st.divider()
    st.info("Additional resources and forms will be populated here as the season progresses.")
# --- 7. PAGE 3: ADMIN DASHBOARD (FRAGMENTED) ---
elif st.session_state.page == "Admin":
    if not st.session_state.admin_authenticated:
        st.markdown('<h1 class="main-title">Admin Login</h1>', unsafe_allow_html=True)
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("Enter Admin Password", type="password")
            if st.button("Access Dashboard", use_container_width=True):
                if pwd == "DBZ2026":
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect Password")
    else:
        st.markdown('<h1 class="main-title">Admin Dashboard</h1>', unsafe_allow_html=True)
        st.divider()
        
        admin_tab1, admin_tab2, admin_tab3, admin_tab4, admin_tab5 = st.tabs(["✅ Confirm Attendance", "🚨 No-Show Log", "📜 Audit Log", "👥 Manage Roster", "💳 Waivers & Payments"])
        
        @st.fragment
        def render_admin_form(ts_string):
            ts_active = df_signups[(df_signups['Practice Date'] == ts_string) & (df_signups['Status'] != 'Cancelled')] if not df_signups.empty else pd.DataFrame()
            
            checkbox_states = {}
            if not ts_active.empty:
                # Sort the active signups alphabetically by name
                ts_active = ts_active.sort_values(by="Name")
                
                for i, row in ts_active.iterrows():
                    col1, col2 = st.columns([8, 1])
                    with col1:
                        is_checked = row['Status'] in ['Active', 'Attended']
                        checkbox_states[row['id']] = st.checkbox(f"{row['Name']} (Current: {row['Status']})", value=is_checked, key=f"chk_{row['id']}_{ts_string}")
                    with col2:
                        if st.button("❌", key=f"rem_{row['id']}_{ts_string}", help=f"Remove {row['Name']} from this session"):
                            # 1. Cancel the user's active status
                            supabase.table("signups").update({"Status": "Cancelled"}).eq("id", row['id']).execute()
                            log_action("Admin Forcibly Removed Paddler", f"{row['Name']} was removed from {ts_string}")
                            
                            # 2. Trigger automatic waitlist promotion to fill the empty seat
                            user_data = df_roster[df_roster['Name'] == row['Name']]
                            if not user_data.empty:
                                user_side = user_data.iloc[0].get('True Side', 'Unknown')
                                eff_side = 'Left' if user_side in ['Unknown', 'Ambidextrous'] else user_side
                                
                                if not df_waitlist.empty:
                                    pending = df_waitlist[(df_waitlist['Practice Date'] == ts_string) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
                                    for idx, w_row in pending.iterrows():
                                        if w_row['Side'] in [eff_side, 'Unknown', 'Ambidextrous'] or "[Circuit]" in ts_string:
                                            supabase.table("waitlist").update({"Status": "Promoted"}).eq("id", int(w_row['id'])).execute()
                                            supabase.table("signups").insert({"Practice Date": ts_string, "Name": w_row['Name'], "Status": "Active"}).execute()
                                            log_action("Waitlist Promotion", f"{w_row['Name']} automatically promoted to Active for {ts_string} after admin removal")
                                            break
                                            
                            load_live_data.clear()
                            load_audit_log.clear()
                            st.rerun()
            else:
                st.info("No records pending confirmation.")
            
            st.markdown("---")
            # Inline Walk-In Feature
            all_names = df_roster['Name'].tolist() if not df_roster.empty else []
            current_names = ts_active['Name'].tolist() if not ts_active.empty else []
            
            # Sort the available walk-in dropdown names alphabetically 
            available_names = sorted([n for n in all_names if n not in current_names])
            walkin_name = st.selectbox("➕ Add Walk-In (Optional)", available_names, index=None, placeholder="Select a name to append to today's list...", key=f"walkin_{ts_string}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # The submit button now operates outside a form, reading the dynamic checkbox states
            if st.button("Submit Attendance & Walk-Ins", use_container_width=True, key=f"sub_{ts_string}"):
                updates_made = False
                for record_id, is_present in checkbox_states.items():
                    new_status = "Attended" if is_present else "No-Show"
                    supabase.table("signups").update({"Status": new_status}).eq("id", record_id).execute()
                    updates_made = True
                    
                if walkin_name:
                    supabase.table("signups").insert({"Practice Date": ts_string, "Name": walkin_name, "Status": "Attended"}).execute()
                    log_action("Walk-In Added", f"{walkin_name} manually added to {ts_string}")
                    updates_made = True
                    
                if updates_made:
                    log_action("Attendance Submitted", f"Bulk update processed for {ts_string}")
                    load_live_data.clear()
                    load_audit_log.clear()
                    st.toast(f"Records updated for {ts_string.split(',')[0]}.", icon="🐉")
                    st.rerun()
        
            with st.popover(f"🗑️ Delete {ts_string.split(',')[0]} Data", use_container_width=True):
                st.error("Permanently delete all records for this date?")
                if st.button("Confirm Delete", key=f"del_{ts_string}"):
                    supabase.table("signups").delete().eq("Practice Date", ts_string).execute()
                    supabase.table("waitlist").delete().eq("Practice Date", ts_string).execute()
                    log_action("Practice Deleted", f"All data wiped for {ts_string}")
                    load_live_data.clear()
                    load_audit_log.clear()
                    st.rerun()

        with admin_tab1:
            current_week_label = f"📅 Week of {effective_monday.strftime('%B %-d')} (Current Week)"
            with st.expander(current_week_label, expanded=True):
                c1, c2, c3 = st.columns(3)
                cols = [c1, c2, c3]
                for idx, (ts_str, ts_dt) in enumerate(TIMESLOTS.items()):
                    with cols[idx]:
                        render_card_header(ts_str) # Replaces the messy markdown
                        render_admin_form(ts_str)
            
            if historical_weeks:
                st.divider()
                st.markdown("### Edit Past Attendance")
                for week_label, dates in historical_weeks.items():
                    with st.expander(f"⚙️ Manage {week_label}", expanded=False):
                        cols = st.columns(len(dates) if len(dates) > 0 else 1)
                        for idx, past_date in enumerate(dates):
                            with cols[idx]:
                                render_card_header(past_date) # Replaces the messy markdown
                                render_admin_form(past_date)

        with admin_tab2:
            st.markdown("### No-Show Tracking")
            no_shows_df = df_signups[df_signups['Status'] == 'No-Show'] if not df_signups.empty else pd.DataFrame()
            if no_shows_df.empty:
                st.markdown("<div class='app-banner app-banner-success'>🎉 Amazing! Zero no-shows recorded so far.</div>", unsafe_allow_html=True)
            else:
                c1, c2 = st.columns([1, 2.5])
                with c1:
                    offenders = no_shows_df['Name'].value_counts().reset_index()
                    offenders.columns = ['Name', 'Missed Practices']
                    # Sort offenders alphabetically or by most missed practices
                    offenders = offenders.sort_values(by="Name", ascending=True)
                    st.dataframe(offenders, use_container_width=True, hide_index=True)
                with c2:
                    enriched_no_shows = pd.merge(no_shows_df, df_roster, on="Name", how="left")
                    log_display = enriched_no_shows[['Practice Date', 'Name', 'True Side', 'Gender', 'Membership']].sort_values(by='Name', ascending=True)
                    st.dataframe(log_display, use_container_width=True, hide_index=True)
                    
        with admin_tab3:
            st.markdown("### System Audit Log")
            st.caption("Scroll through the table to view all historical modifications.")
            df_audit = load_audit_log()
            if not df_audit.empty:
                # Streamlit's st.dataframe natively supports infinite virtual scrolling and pagination for large datasets
                st.dataframe(df_audit[['Timestamp', 'Action', 'Details']], use_container_width=True, hide_index=True, height=500)
            else:
                st.markdown("<div class='app-banner'>No system actions logged yet.</div>", unsafe_allow_html=True)

        with admin_tab4:
            st.markdown("### Manage Roster")
            st.markdown("<br>", unsafe_allow_html=True)

            col_add, col_edit = st.columns(2, gap="large")

            # --- LEFT COLUMN: ADD NEW PADDLER ---
            with col_add:
                with st.container(border=True):
                    st.markdown("#### ➕ Add New Paddler")
                    
                    new_name = st.text_input("Full Name (Must be unique)", key="new_paddler_name")
                    new_gender = st.selectbox("Gender", ["Open", "Women", "Unknown"], index=2, key="new_paddler_gender")
                    new_side = st.selectbox("True Side", ["Left", "Right", "Ambidextrous", "Unknown"], index=3, key="new_paddler_side")
                    new_mem = st.selectbox("Membership Tier", [
                        "Fall ONLY (without circuit)", 
                        "BOTH semesters (with circuit)", 
                        "Winter ONLY (without circuit)", 
                        "BOTH semesters (without circuit)",
                        "Unknown"
                    ], index=4, key="new_paddler_mem")
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Custom styled Green button using HTML wrapper
                    st.markdown("""
                    <style>
                        div.add-btn button {
                            background-color: #00e676 !important;
                            color: #0e1117 !important;
                            font-weight: 700 !important;
                        }
                        div.add-btn button:hover {
                            background-color: #00c853 !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="add-btn">', unsafe_allow_html=True)
                    if st.button("Add to Roster", use_container_width=True, key="btn_add_roster"):
                        if new_name.strip() == "":
                            st.error("Please enter a valid name.")
                        else:
                            existing_names = df_roster['Name'].str.lower().tolist() if not df_roster.empty else []
                            if new_name.strip().lower() in existing_names:
                                st.error(f"❌ {new_name} is already in the roster.")
                            else:
                                supabase.table("roster").insert({
                                    "Name": new_name.strip(),
                                    "True Side": new_side,
                                    "Gender": new_gender,
                                    "Membership": new_mem
                                }).execute()
                                
                                log_action("Roster Addition", f"{new_name} was added to the database.")
                                load_roster.clear()
                                load_audit_log.clear()
                                st.toast(f"{new_name} added to roster!", icon="✅")
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

            # --- RIGHT COLUMN: EDIT OR REMOVE PADDLER ---
            with col_edit:
                with st.container(border=True):
                    st.markdown("#### ✏️ Edit or Remove Paddler")
                    
                    all_roster_names = sorted(df_roster['Name'].tolist()) if not df_roster.empty else []
                    edit_name = st.selectbox("Search / Select Paddler", all_roster_names, index=None, placeholder="Type a name to search...", key="edit_paddler_search")
                    
                    if edit_name:
                        user_data = df_roster[df_roster['Name'] == edit_name].iloc[0]
                        
                        upd_name = st.text_input("Full Name", value=user_data['Name'], key="upd_paddler_name")
                        
                        genders = ["Open", "Women", "Unknown"]
                        curr_gender = user_data['Gender'] if user_data['Gender'] in genders else "Unknown"
                        upd_gender = st.selectbox("Gender", genders, index=genders.index(curr_gender), key="upd_paddler_gender")
                        
                        sides = ["Left", "Right", "Ambidextrous", "Unknown"]
                        curr_side = user_data.get('True Side', 'Unknown')
                        curr_side = curr_side if curr_side in sides else "Unknown"
                        upd_side = st.selectbox("True Side", sides, index=sides.index(curr_side), key="upd_paddler_side")
                        
                        mems = [
                            "Fall ONLY (without circuit)", 
                            "BOTH semesters (with circuit)", 
                            "Winter ONLY (without circuit)", 
                            "BOTH semesters (without circuit)",
                            "Unknown"
                        ]
                        curr_mem = user_data.get('Membership', 'Unknown')
                        curr_mem = curr_mem if curr_mem in mems else "Unknown"
                        upd_mem = st.selectbox("Membership Tier", mems, index=mems.index(curr_mem), key="upd_paddler_mem")
                            
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Inject custom styles for Blue Save and Red Delete buttons
                        st.markdown("""
                        <style>
                            div.save-btn button {
                                background-color: #4dabf7 !important;
                                color: #0e1117 !important;
                                font-weight: 700 !important;
                            }
                            div.save-btn button:hover {
                                background-color: #339af0 !important;
                            }
                            div.del-btn button {
                                background-color: #ff3333 !important;
                                color: white !important;
                                font-weight: 700 !important;
                            }
                            div.del-btn button:hover {
                                background-color: #e02828 !important;
                            }
                        </style>
                        """, unsafe_allow_html=True)

                        b_col1, b_col2 = st.columns(2)
                        with b_col1:
                            st.markdown('<div class="save-btn">', unsafe_allow_html=True)
                            save_clicked = st.button("💾 Save Changes", use_container_width=True, key="btn_save_roster")
                            st.markdown('</div>', unsafe_allow_html=True)
                            
                        with b_col2:
                            st.markdown('<div class="del-btn">', unsafe_allow_html=True)
                            delete_clicked = st.button("🗑️ Delete", use_container_width=True, key="btn_delete_roster")
                            st.markdown('</div>', unsafe_allow_html=True)

                        if save_clicked:
                            if upd_name.strip() == "":
                                st.error("Name cannot be blank.")
                            else:
                                supabase.table("roster").update({
                                    "Name": upd_name.strip(),
                                    "True Side": upd_side,
                                    "Gender": upd_gender,
                                    "Membership": upd_mem
                                }).eq("Name", edit_name).execute()
                                
                                if upd_name.strip() != edit_name:
                                    supabase.table("signups").update({"Name": upd_name.strip()}).eq("Name", edit_name).execute()
                                    supabase.table("waitlist").update({"Name": upd_name.strip()}).eq("Name", edit_name).execute()
                                
                                log_action("Roster Updated", f"Admin updated profile for {edit_name}")
                                load_roster.clear()
                                load_live_data.clear()
                                load_audit_log.clear()
                                st.toast(f"Profile updated for {upd_name.strip()}", icon="💾")
                                st.rerun()

                        if delete_clicked:
                            supabase.table("roster").delete().eq("Name", edit_name).execute()
                            supabase.table("signups").delete().eq("Name", edit_name).execute()
                            supabase.table("waitlist").delete().eq("Name", edit_name).execute()
                            
                            log_action("Roster Removal", f"{edit_name} was permanently removed from the system.")
                            load_roster.clear()
                            load_live_data.clear()
                            load_audit_log.clear()
                            st.toast(f"{edit_name} removed from roster.", icon="🗑️")
                            st.rerun()
                    else:
                        st.info("Select a paddler above to edit details or delete.")
        
        
        with admin_tab5:
            st.markdown("### Financial & Waiver Tracking")
            st.markdown("Check the boxes for completed waivers and use the dropdowns to track payments. Click Save when finished.")
            
            # Ensure columns exist in the dataframe to prevent errors before Supabase is updated
            if 'Waiver' not in df_roster.columns: df_roster['Waiver'] = False
            if 'Payment' not in df_roster.columns: df_roster['Payment'] = 'Unpaid'
            
            # --- NEW: Dashboard Circular Progress Trackers ---
            total_members = len(df_roster) if not df_roster.empty else 1
            waivers_done = len(df_roster[df_roster['Waiver'] == True])
            fully_paid = len(df_roster[df_roster['Payment'] == 'Fully Paid'])
            
            waiver_pct = int((waivers_done / total_members) * 100) if not df_roster.empty else 0
            payment_pct = int((fully_paid / total_members) * 100) if not df_roster.empty else 0
            
            st.markdown(f"""
            <div style="display: flex; justify-content: space-evenly; background-color: rgba(22, 24, 28, 0.65); backdrop-filter: blur(12px); padding: 30px; border-radius: 16px; border: 1px solid rgba(43, 45, 49, 0.8); margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <div style="text-align: center;">
                    <div style="width: 130px; height: 130px; border-radius: 50%; background: conic-gradient(#00e676 {waiver_pct}%, #2b2d31 0); display: flex; align-items: center; justify-content: center; margin: 0 auto; box-shadow: 0 0 20px rgba(0, 230, 118, 0.15);">
                        <div style="width: 104px; height: 104px; border-radius: 50%; background-color: #16181c; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 2rem; font-weight: 800; color: #e0e0e0;">{waiver_pct}%</span>
                        </div>
                    </div>
                    <div style="margin-top: 15px; font-weight: 600; color: #a0a0a5; font-size: 1.1rem; letter-spacing: 0.5px;">Waivers Signed</div>
                </div>
                <div style="text-align: center;">
                    <div style="width: 130px; height: 130px; border-radius: 50%; background: conic-gradient(#00e676 {payment_pct}%, #2b2d31 0); display: flex; align-items: center; justify-content: center; margin: 0 auto; box-shadow: 0 0 20px rgba(0, 230, 118, 0.15);">
                        <div style="width: 104px; height: 104px; border-radius: 50%; background-color: #16181c; display: flex; align-items: center; justify-content: center;">
                            <span style="font-size: 2rem; font-weight: 800; color: #e0e0e0;">{payment_pct}%</span>
                        </div>
                    </div>
                    <div style="margin-top: 15px; font-weight: 600; color: #a0a0a5; font-size: 1.1rem; letter-spacing: 0.5px;">Fully Paid</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
                
            # Filter and reorder the display columns
            display_df = df_roster[['Name', 'True Side', 'Gender', 'Membership', 'Waiver', 'Payment']]
            
            # Render an interactive, editable table
            edited_roster = st.data_editor(
                display_df,
                column_config={
                    "Waiver": st.column_config.CheckboxColumn("Waiver Completed", default=False),
                    "Payment": st.column_config.SelectboxColumn("Payment Status", options=["Unpaid", "Partially Paid", "Fully Paid"], required=True),
                    "Name": st.column_config.TextColumn("Name", disabled=True),
                    "True Side": st.column_config.TextColumn("True Side", disabled=True),
                    "Gender": st.column_config.TextColumn("Gender", disabled=True),
                    "Membership": st.column_config.TextColumn("Membership", disabled=True)
                },
                use_container_width=True,
                hide_index=True,
                key="financial_editor",
                height=500
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("💾 Save Payment & Waiver Updates", use_container_width=True):
                updates_made = False
                
                # Compare the edited table with the original database to find what changed
                for idx, row in edited_roster.iterrows():
                    orig_row = display_df.iloc[idx]
                    
                    if row['Waiver'] != orig_row['Waiver'] or row['Payment'] != orig_row['Payment']:
                        supabase.table("roster").update({
                            "Waiver": bool(row['Waiver']),
                            "Payment": str(row['Payment'])
                        }).eq("Name", row['Name']).execute()
                        updates_made = True
                
                if updates_made:
                    log_action("Financials Updated", "Admin modified roster payment/waiver statuses")
                    load_roster.clear()
                    load_audit_log.clear()
                    st.toast("Financials saved successfully.", icon="💰")
                    st.rerun()
                else:
                    st.info("No changes detected.")

# --- 8. PAGE 4: MAIN SIGN UP (FRAGMENTED) ---
elif st.session_state.page == "Sign Up":
    st.markdown('<h1 class="main-title">McGill Dragon Boat Z</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Indoors Attendance 2026-2027</p>', unsafe_allow_html=True)

    # 1. Moved instructions OUTSIDE the if/else block so they always appear
    st.markdown("""<div class="instructions">Welcome to the sign-up portal. Please select your name below and choose your preferred timeslot. To ensure everyone gets water time, attendance is strictly limited to <strong>one pool practice per week</strong>. If your schedule changes, simply log back in and cancel your spot to instantly free it up for a teammate. You can view the live attendee list in the sidebar at any time.<br>
    <br>Each pool session is capped at <strong>32 paddlers</strong> to maintain an even split of 16 Lefts and 16 Rights. If you paddle on both sides or do not have a set preference yet, the system will automatically allocate your seat to keep the boat balanced.<br>
    <br>If a practice reaches capacity, you will be added to a side-specific waitlist. Whenever a cancellation occurs, the system automatically promotes the next person in line based on a first-come, first-served order. You can also cancel your waitlist position directly from this portal.</div>""", unsafe_allow_html=True)
    st.divider()

    if not is_open:
        # Wraps the alert in a centered column layout matching the Admin page
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            # 2. Replaced native st.info with a custom centered glassmorphic alert
            st.markdown("""
            <div style="text-align: center; background-color: rgba(255, 51, 51, 0.1); padding: 15px 20px; border-radius: 12px; border: 1px solid rgba(255, 51, 51, 0.4); box-shadow: 0 4px 15px rgba(255, 51, 51, 0.15);">
                <div style="font-size: 1.2rem; font-weight: 800; color: #ff3333; letter-spacing: 0.5px;">🔒 REGISTRATION CLOSED</div>
                <div style="color: #e0e0e0; font-weight: 600; margin-top: 4px;">Sign-ups open every Monday at 8:00 PM.</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # --- NEW: User Login Flow ---
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None

        if not st.session_state.current_user:
            login_c1, login_c2, login_c3 = st.columns([1, 3, 1])
            with login_c2:
                with st.container(border=True):
                    name_list = df_roster['Name'].tolist() if not df_roster.empty else []
                    selected_name = st.selectbox("Select your Full Name", options=name_list, index=None, placeholder="Start typing your name here...")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if selected_name:
                        if st.button("Access Portal", use_container_width=True):
                            st.session_state.current_user = selected_name
                            st.rerun()
        else:
            user_name = st.session_state.current_user
            
            # Centered and sized down to match the ID card and selection containers
            acc_c1, acc_c2, acc_c3 = st.columns([1, 3, 1])
            with acc_c2:
                col1, col2 = st.columns([3, 1], vertical_alignment="center")
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(0, 230, 118, 0.08); border: 1px solid rgba(0, 230, 118, 0.3); padding: 8px 14px; border-radius: 8px; color: #00e676; font-size: 0.9rem;">
                        ✅ Access granted for <strong>{user_name}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("Switch User", use_container_width=True, key="switch_user_btn"):
                        st.session_state.current_user = None
                        st.rerun()
        
            @st.fragment
            def render_signup_portal(user_name):
                
                user_data = df_roster[df_roster['Name'] == user_name].iloc[0]
                user_side = user_data.get('True Side', 'Unknown')
                user_membership = str(user_data.get('Membership', 'Unknown')).strip()
                user_eff_side = 'Left' if user_side in ['Unknown', 'Ambidextrous'] else user_side
                
                # Unified Verified Paddler Card Container, Sized Down and Centered
                id_c1, id_c2, id_c3 = st.columns([1, 3, 1])
                with id_c2:
                    with st.container(border=True):
                        card_col1, card_col2 = st.columns([3, 1], vertical_alignment="center")
                        with card_col1:
                            st.markdown(f"""
                            <div style="padding: 2px;">
                                <div style="color: #ff7a7a; font-size: 0.75rem; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 1px;">Verified Paddler</div>
                                <div style="font-family: 'Teko', sans-serif; font-size: 2.2rem; font-weight: 800; color: white; line-height: 1.0; margin-bottom: 2px;">{user_name}</div>
                                <div style="color: #a0a0a5; font-size: 0.9rem;"><strong>Tier:</strong> {user_membership} &nbsp;&bull;&nbsp; <strong>Side:</strong> <span style="color: #ffffff; font-weight: 600;">{user_side}</span></div>
                            </div>
                            """, unsafe_allow_html=True)
                        with card_col2:
                            with st.popover("🔄 Update", use_container_width=True):
                                new_side = st.radio("Select your True Side:", ["Left", "Right", "Ambidextrous", "Unknown"], index=["Left", "Right", "Ambidextrous", "Unknown"].index(user_side) if user_side in ["Left", "Right", "Ambidextrous", "Unknown"] else 3)
                                if st.button("Save", use_container_width=True):
                                    supabase.table("roster").update({"True Side": new_side}).eq("Name", user_name).execute()
                                    log_action("Side Updated", f"{user_name} updated their true side to {new_side}")
                                    load_roster.clear()
                                    st.rerun()
                st.divider()
                
                for ts_str in TIMESLOTS.keys():
                    day_name = ts_str.split(',')[0] + (" (Circuit)" if "[Circuit]" in ts_str else "")
                    
                    active_record = df_signups[(df_signups['Practice Date'] == ts_str) & (df_signups['Name'] == user_name) & (df_signups['Status'].isin(['Active', 'Attended']))] if not df_signups.empty else pd.DataFrame()
                    wl_record = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Name'] == user_name) & (df_waitlist['Status'] == 'Waiting')] if not df_waitlist.empty else pd.DataFrame()
                        
                    if not active_record.empty:
                        act_c1, act_c2, act_c3 = st.columns([1, 3, 1])
                        with act_c2:
                            col_a, col_b = st.columns([3, 1], vertical_alignment="center")
                            with col_a:
                                st.markdown(f"""
                                <div style="background: rgba(0, 230, 118, 0.08); border: 1px solid rgba(0, 230, 118, 0.3); padding: 8px 14px; border-radius: 8px; color: #00e676; font-size: 0.9rem;">
                                    ✅ Signed up for <strong>{day_name}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                            with col_b:
                                if st.button(f"🚨 Cancel {day_name} Attendance", key=f"cancel_att_{ts_str}", use_container_width=True):
                                    record_id = int(active_record.iloc[0]['id'])
                                    supabase.table("signups").update({"Status": "Cancelled"}).eq("id", record_id).execute()
                                    log_action("Attendance Cancelled", f"{user_name} cancelled their spot for {day_name}")
                                    
                                    if not df_waitlist.empty:
                                        pending = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
                                        for idx, row in pending.iterrows():
                                            if row['Side'] in [user_eff_side, 'Unknown', 'Ambidextrous'] or "[Circuit]" in ts_str:
                                                supabase.table("waitlist").update({"Status": "Promoted"}).eq("id", int(row['id'])).execute()
                                                supabase.table("signups").insert({"Practice Date": ts_str, "Name": row['Name'], "Status": "Active"}).execute()
                                                log_action("Waitlist Promotion", f"{row['Name']} was automatically promoted to Active for {day_name}")
                                                break
                                                
                                    load_live_data.clear()
                                    load_audit_log.clear()
                                    st.rerun()
                            
                    elif not wl_record.empty:
                        pending_all = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
                        pos = pending_all['Name'].tolist().index(user_name) + 1
                        st.warning(f"⏳ You are **#{pos}** on the waitlist for **{day_name}**.")
                        if st.button(f"🚨 Cancel {day_name} Waitlist", key=f"cancel_wl_{ts_str}"):
                            record_id = int(wl_record.iloc[0]['id'])
                            supabase.table("waitlist").update({"Status": "Cancelled"}).eq("id", record_id).execute()
                            log_action("Waitlist Cancelled", f"{user_name} left the waitlist for {day_name}")
                            
                            load_live_data.clear()
                            load_audit_log.clear()
                            st.rerun()
                            
                st.divider()
                
                available_timeslots = [ts for ts in TIMESLOTS.keys() if (df_signups.empty or df_signups[(df_signups['Practice Date'] == ts) & (df_signups['Name'] == user_name) & (df_signups['Status'].isin(['Active', 'Attended']))].empty) and (df_waitlist.empty or df_waitlist[(df_waitlist['Practice Date'] == ts) & (df_waitlist['Name'] == user_name) & (df_waitlist['Status'] == 'Waiting')].empty)]                
                if available_timeslots:
                    st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 20px;'>SIGN-UP FOR PRACTICE</h3>", unsafe_allow_html=True)
                    
                    # --- Compact, Centered Rule Notice (Yellow Container) ---
                    nc1, nc2, nc3 = st.columns([1, 3, 1])
                    with nc2:
                        st.markdown("""
                        <div style="background: rgba(255, 193, 7, 0.08); border: 1px solid rgba(255, 193, 7, 0.3); border-left: 3px solid #ffc107; padding: 8px 14px; border-radius: 8px; margin-bottom: 15px; font-size: 0.85rem; color: #e0e0e0; text-align: center;">
                            ⚠️ Limit: <strong style="color: #ffc107;">1 pool session AND 1 circuit spot</strong> per week.
                        </div>
                        """, unsafe_allow_html=True)

                    if "selected_timeslot" not in st.session_state:
                        st.session_state.selected_timeslot = available_timeslots[0]

                    sc1, sc2, sc3 = st.columns([1, 3, 1])
                    with sc2:
                        options_map = {}
                        for ts in available_timeslots:
                            if "[Circuit]" in ts:
                                # For All Circuit (Blue)
                                tag = '<div style="font-size: 0.75rem; font-weight: 800; color: #4dabf7; letter-spacing: 1px;">FOR ALL</div>'
                            elif "Thursday" in ts and "7:00 PM" in ts:
                                # Intermediate / Advanced (Soft Red)
                                tag = '<div style="font-size: 0.75rem; font-weight: 800; color: #ff7a7a; letter-spacing: 1px;">INTERMEDIATE / ADVANCED</div>'
                            elif "Friday" in ts and "6:00 PM" in ts:
                                # Beginner / Back-To-Basics (Green)
                                tag = '<div style="font-size: 0.75rem; font-weight: 800; color: #00e676; letter-spacing: 1px;">BEGINNER-FRIENDLY / BACK-TO-BASICS</div>'
                            else:
                                tag = '<div style="font-size: 0.75rem; font-weight: 800; color: #a0a0a5; letter-spacing: 1px;">SESSION</div>'
                            
                            options_map[ts] = tag
                        selected_ts = st.session_state.selected_timeslot
                        
                        for ts in available_timeslots:
                            tag_html = options_map[ts]
                            is_selected = (st.session_state.selected_timeslot == ts)
                            
                            with st.container(border=True):
                                col_a, col_b = st.columns([4, 1], vertical_alignment="center")
                                with col_a:
                                    st.markdown(f"""
                                    <div style="font-weight: 700; color: white; font-size: 1.05rem; margin-bottom: 3px;">{ts.upper()}</div>
                                    {tag_html}
                                    """, unsafe_allow_html=True)
                                with col_b:
                                    if st.button("Select", key=f"select_{ts}", use_container_width=True):
                                        st.session_state.selected_timeslot = ts
                                        st.rerun()

                        timeslot = st.session_state.selected_timeslot
                        target_dt = TIMESLOTS[timeslot]
                    
                    is_circuit = "[Circuit]" in timeslot
                    is_pool = "[Pool]" in timeslot
                    
                    active_all = df_signups[(df_signups['Name'] == user_name) & (df_signups['Status'].isin(['Active', 'Attended']))] if not df_signups.empty else pd.DataFrame()
                    current_week_active = [ts for ts in (active_all['Practice Date'].tolist() if not active_all.empty else []) if ts in TIMESLOTS.keys()]
                    
                    active_pool_count = len([ts for ts in current_week_active if "[Pool]" in ts])
                    
                    can_signup = True
                    
                    if is_circuit and user_membership != 'BOTH semesters (with circuit)':
                        can_signup = False
                        st.error("❌ Your current membership tier does not include Circuit Training.")
                    
                    elif is_pool and active_pool_count >= 1:
                        can_signup = False
                        
                        # Centered column wrapper matching selection cards and rule notices
                        warn_c1, warn_c2, warn_c3 = st.columns([1, 3, 1])
                        with warn_c2:
                            st.markdown("""
                            <div style="background: rgba(255, 51, 51, 0.05); border: 1px solid rgba(255, 51, 51, 0.3); border-left: 3px solid #ff3333; padding: 8px 14px; border-radius: 8px; margin-bottom: 15px; font-size: 0.85rem; color: #ff7a7a; text-align: center;">
                                🔒 <strong>Limit Reached:</strong> 1 pool session max per week (Circuit sign-up still available).
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if can_signup:
                        ts_active = df_signups[(df_signups['Practice Date'] == timeslot) & (df_signups['Status'].isin(['Active', 'Attended']))] if not df_signups.empty else pd.DataFrame()
                        merged = pd.merge(ts_active, df_roster, on="Name", how="left") if not ts_active.empty else pd.DataFrame()
                        
                        # Count strict sides and unallocated ambis
                        current_left = len(merged[merged['True Side'] == 'Left']) if not merged.empty else 0
                        current_right = len(merged[merged['True Side'] == 'Right']) if not merged.empty else 0
                        ambis = len(merged[merged['True Side'].isin(['Unknown', 'Ambidextrous'])]) if not merged.empty else 0
                        
                        # Mathematically distribute existing ambis
                        for _ in range(ambis):
                            if current_left <= current_right:
                                current_left += 1
                            else:
                                current_right += 1
                                
                        # Dynamically route the user checking out
                        if user_side in ['Unknown', 'Ambidextrous']:
                            eff_side = 'Left' if current_left <= current_right else 'Right'
                        else:
                            eff_side = user_side
                            
                        boat_full = (is_circuit and len(ts_active) >=24) or \
                                    (is_pool and len(ts_active) >= 32) or \
                                    (is_pool and eff_side == 'Left' and current_left >= 16) or \
                                    (is_pool and eff_side == 'Right' and current_right >= 16)
                            
                        # Centered column layout to constrain the confirmation button width
                        b_c1, b_c2, b_c3 = st.columns([1, 2, 1])
                        with b_c2:
                            confirm_clicked = st.button("Confirm Attendance", use_container_width=True)

                        if confirm_clicked:
                            if boat_full:
                                supabase.table("waitlist").insert({"Practice Date": timeslot, "Name": user_name, "Side": user_side, "Status": "Waiting"}).execute()
                                log_action("Joined Waitlist", f"{user_name} joined the waitlist for {timeslot}")
                                st.warning(f"The session is full. You have been added to the waitlist!")
                            else:
                                # Try to grab the seat. The database is the ultimate referee.
                                try:
                                    supabase.table("signups").insert({"Practice Date": timeslot, "Name": user_name, "Status": "Active"}).execute()
                                    log_action("Signup Confirmed", f"{user_name} registered for {timeslot}")
                                    st.balloons()
                                except Exception as e:
                                    # If the Supabase trigger rejects it because of a race condition
                                    if 'BOAT_FULL' in str(e):
                                        supabase.table("waitlist").insert({"Practice Date": timeslot, "Name": user_name, "Side": user_side, "Status": "Waiting"}).execute()
                                        log_action("Joined Waitlist (Race Condition)", f"{user_name} was rerouted to waitlist for {timeslot}")
                                        st.warning("Someone just grabbed the very last seat a millisecond before you! You have been automatically placed on the waitlist instead.")
                                    else:
                                        st.error(f"A database error occurred: {e}")
                                
                            load_live_data.clear()
                            load_audit_log.clear()
                            st.rerun()
                else:
                    st.info("You are currently signed up or waitlisted for all available practices this week.")

            render_signup_portal(user_name)