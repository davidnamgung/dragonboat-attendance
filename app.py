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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    [data-testid="stAppViewContainer"] { background-color: #0e1117; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #16181c; border-right: 1px solid #2b2d31; }
    .main-title { text-align: center; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 4rem; background: -webkit-linear-gradient(45deg, #ff3333, #ff7a7a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px; padding-bottom: 0px; letter-spacing: -1.5px; }
    .sub-title { text-align: center; font-family: 'Inter', sans-serif; font-weight: 600; font-size: 1.8rem; color: #8b8d91; margin-top: -5px; margin-bottom: 30px; letter-spacing: -0.5px; }
    .instructions { text-align: center; font-family: 'Inter', sans-serif; font-size: 1.1rem; color: #a0a0a5; max-width: 850px; margin: 0 auto; line-height: 1.6; background: #16181c; padding: 20px; border-radius: 12px; border: 1px solid #2b2d31; }
    .stSelectbox label { font-family: 'Inter', sans-serif !important; font-size: 1.4rem !important; font-weight: 600; color: #ffffff !important; text-align: center; }
    div[data-baseweb="select"] > div { background-color: #1a1c23 !important; border-radius: 12px !important; border: 1px solid #3a3d45 !important; }
    .stButton>button { background-color: #ff3333 !important; color: white !important; height: 3.2rem; font-size: 1.1rem; font-weight: 600; font-family: 'Inter', sans-serif; border-radius: 12px; border: None; width: 100%; transition: all 0.3s ease; box-shadow: 0 4px 6px rgba(255, 51, 51, 0.2); }
    .stButton>button:hover { background-color: #ff4d4d !important; transform: translateY(-2px); box-shadow: 0 6px 12px rgba(255, 51, 51, 0.3); }
    .roster-card { background-color: #16181c; padding: 20px; border-radius: 16px; border: 1px solid #2b2d31; border-top: 4px solid #ff3333; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2); }
    .roster-title { color: #ffffff; font-weight: 600; font-family: 'Inter', sans-serif; font-size: 1.2rem; margin-bottom: 12px; border-bottom: 1px solid #2b2d31; padding-bottom: 8px; }
    .paddler-list { font-family: 'Inter', sans-serif; font-size: 1.05rem; line-height: 1.6; color: #a0a0a5; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #16181c; border-radius: 8px; border: 1px solid #2b2d31; padding: 10px 20px; font-weight: 600; font-family: 'Inter', sans-serif; color: #8b8d91; }
    .stTabs [aria-selected="true"] { background-color: #ff3333 !important; color: white !important; border-color: #ff3333 !important; }
    @media (max-width: 768px) { .main-title { font-size: 2.5rem; letter-spacing: -1px; } .sub-title { font-size: 1.4rem; } .instructions { font-size: 1rem; padding: 15px; text-align: left; } .stSelectbox label { font-size: 1.2rem !important; } .stTabs [data-baseweb="tab-list"] { display: flex; flex-direction: column; gap: 8px; } }
</style>
""", unsafe_allow_html=True)

# --- 2. TIME GATE & DYNAMIC DATES ---
tz = pytz.timezone("America/Toronto")
now = datetime.now(tz)
effective_now = now - timedelta(hours=20)
effective_monday = effective_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=effective_now.weekday())

thurs_dt = effective_monday + timedelta(days=3, hours=19)
circuit_dt = effective_monday + timedelta(days=4, hours=17) # Friday 5 PM
fri_dt = effective_monday + timedelta(days=4, hours=18)

def format_date(d, time_str):
    suffix = 'th' if 11 <= d.day <= 13 else {1:'st', 2:'nd', 3:'rd'}.get(d.day % 10, 'th')
    return f"{d.strftime('%A, %B')} {d.day}{suffix} {time_str}"

thurs_str = format_date(thurs_dt, "7:00 PM - 8:00 PM [Pool]")
circuit_str = format_date(circuit_dt, "5:00 PM - 6:00 PM [Circuit]")
fri_str = format_date(fri_dt, "6:00 PM - 7:00 PM [Pool]")

TIMESLOTS = {thurs_str: thurs_dt, circuit_str: circuit_dt, fri_str: fri_dt}

# MAIN BUTTON
is_open = True
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
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["id", "Timestamp", "Action", "Details"])

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
    
    def get_week_label(date_str):
        match = re.search(r', ([A-Za-z]+ \d+)', date_str)
        if match:
            try:
                dt = datetime.strptime(f"{match.group(1)} {now.year}", "%B %d %Y")
                monday = dt - timedelta(days=dt.weekday())
                return f"Week of {monday.strftime('%B %-d')}"
            except:
                pass
        return date_str

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

def render_card_header(ts_string):
    # This extracts: Group 1 (Date), Group 2 (Time Range), Group 3 (Type)
    match = re.match(r"(.*?)\s+(\d{1,2}:\d{2}\s*[AP]M\s*-\s*\d{1,2}:\d{2}\s*[AP]M)\s*\[(.*?)\]", ts_string)
    
    if match:
        date_val = match.group(1)
        time_val = match.group(2)
        type_val = match.group(3).upper() # Capitalizes POOL or CIRCUIT
        
        st.markdown(f"""
        <div style="margin-bottom: 15px;">
            <div style="color: #ff3333; font-weight: 800; font-size: 1.3rem; letter-spacing: 1.5px;">{type_val}</div>
            <div style="color: #ffffff; font-weight: 600; font-size: 1.1rem; margin-top: 4px;">{date_val}</div>
            <div style="color: #a0a0a5; font-size: 0.95rem; margin-top: 2px;">{time_val}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Fallback just in case
        st.markdown(f"#### {ts_string}")

def render_roster_card(ts_str, status_filter=['Active', 'Attended']):
    if not df_signups.empty:
        ts_active = df_signups[(df_signups['Practice Date'] == ts_str) & (df_signups['Status'].isin(status_filter))]
        merged = pd.merge(ts_active, df_roster, on="Name", how="left")
        lefts = merged[merged['True Side'] == 'Left']['Name'].tolist()
        rights = merged[merged['True Side'] == 'Right']['Name'].tolist()
        ambis = merged[merged['True Side'].isin(['Unknown', 'Ambidextrous'])]['Name'].tolist()
        
        # Dynamically distribute Ambi/Unknown paddlers to balance the visual list
        for name in ambis:
            if len(lefts) <= len(rights):
                lefts.append(name + " (A)")
            else:
                rights.append(name + " (A)")
    else:
        lefts, rights = [], []
        
    st.markdown(f"""
    <div class='roster-card'>
        <div style='display: flex; justify-content: space-between;'>
            <div style='width: 48%;'>
                <div class='roster-title'>Left ({len(lefts)}/16)</div>
                <div class='paddler-list'>{"<br>".join(lefts) if lefts else "-"}</div>
            </div>
            <div style='width: 48%;'>
                <div class='roster-title'>Right ({len(rights)}/16)</div>
                <div class='paddler-list'>{"<br>".join(rights) if rights else "-"}</div>
            </div>
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
    attendance_counts = pd.DataFrame(columns=['Name', 'Practices Attended'])
    total_practices_held = 0
    practice_counts = pd.DataFrame(columns=['Practice Date', 'Paddlers'])
    
    if not active_signups.empty:
        total_practices_held = active_signups['Practice Date'].nunique()
        attendance_counts = active_signups['Name'].value_counts().reset_index()
        attendance_counts.columns = ['Name', 'Practices Attended']
        practice_counts = active_signups.groupby('Practice Date').size().reset_index(name='Paddlers')
        
    analytics_df = pd.merge(df_roster, attendance_counts, on='Name', how='left')
    analytics_df['Practices Attended'] = analytics_df['Practices Attended'].fillna(0).astype(int)
    
    if total_practices_held > 0:
        analytics_df['Attendance Rate'] = ((analytics_df['Practices Attended'] / total_practices_held) * 100).round(1).astype(str) + '%'
    else:
        analytics_df['Attendance Rate'] = '0%'

    display_cols = ['Name', 'True Side', 'Gender', 'Practices Attended', 'Attendance Rate']
    extra_cols = [c for c in analytics_df.columns if c not in display_cols]
    analytics_df = analytics_df[display_cols + extra_cols]

    tab1, tab2, tab3 = st.tabs(["📊 Master Database", "🧩 Team Composition", "📈 Attendance Trends"])
    
    with tab1:
        st.markdown("### Interactive Master Database")
        c1, c2 = st.columns(2)
        with c1: side_filter = st.multiselect("Filter by Side", analytics_df['True Side'].unique())
        with c2: gender_filter = st.multiselect("Filter by Gender", analytics_df['Gender'].unique())
            
        filtered_df = analytics_df.copy()
        if side_filter: filtered_df = filtered_df[filtered_df['True Side'].isin(side_filter)]
        if gender_filter: filtered_df = filtered_df[filtered_df['Gender'].isin(gender_filter)]
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### Overall Composition")
        c1, c2 = st.columns(2)
        def render_modern_bar(data_series, x_title, color_hex):
            df_chart = data_series.reset_index()
            df_chart.columns = [x_title, 'Count']
            return alt.Chart(df_chart).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X(x_title, sort=None, axis=alt.Axis(labelAngle=0, labelColor='#a0a0a5')),
                y=alt.Y('Count', axis=alt.Axis(labelColor='#a0a0a5', gridColor='#2b2d31')),
                color=alt.value(color_hex),
                tooltip=[x_title, 'Count']
            ).properties(height=280).configure_view(strokeWidth=0)

        with c1:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Total Side Distribution</h4>", unsafe_allow_html=True)
            st.altair_chart(render_modern_bar(analytics_df['True Side'].value_counts(), 'Side', '#ff3333'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Total Gender Distribution</h4>", unsafe_allow_html=True)
            st.altair_chart(render_modern_bar(analytics_df['Gender'].value_counts(), 'Gender', '#a9a9a9'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Gender & Side Breakdown")
        c3, c4 = st.columns(2)
        side_categories = ['Left', 'Right', 'Ambidextrous', 'Unknown']
        
        with c3:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Open Roster</h4>", unsafe_allow_html=True)
            open_df = analytics_df[analytics_df['Gender'] == 'Open']
            open_dist = open_df['True Side'].value_counts().reindex(side_categories, fill_value=0)
            st.altair_chart(render_modern_bar(open_dist, 'Side', '#ff3333'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c4:
            st.markdown("<div class='roster-card'><h4 style='color:white;text-align:center;'>Women Roster</h4>", unsafe_allow_html=True)
            women_df = analytics_df[analytics_df['Gender'] == 'Women']
            women_dist = women_df['True Side'].value_counts().reindex(side_categories, fill_value=0)
            st.altair_chart(render_modern_bar(women_dist, 'Side', '#a9a9a9'), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("### Historical Practice Turnout")
        if not practice_counts.empty:
            chart = alt.Chart(practice_counts).mark_area(
                line={'color':'#ff3333'}, color=alt.Gradient(
                    gradient='linear', stops=[alt.GradientStop(color='#ff3333', offset=0), alt.GradientStop(color='rgba(255, 51, 51, 0)', offset=1)], x1=1, x2=1, y1=1, y2=0)
            ).encode(
                x=alt.X('Practice Date:N', sort=None, axis=alt.Axis(labelAngle=-45, labelColor='#a0a0a5')),
                y=alt.Y('Paddlers:Q', axis=alt.Axis(labelColor='#a0a0a5', gridColor='#2b2d31')),
                tooltip=['Practice Date', 'Paddlers']
            ).properties(height=350).configure_view(strokeWidth=0)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Not enough data yet. Complete a few practices to see trends!")

# --- NEW PAGE: TEAM RESOURCES ---
elif st.session_state.page == "Resources":
    st.markdown('<h1 class="main-title">Team Resources</h1>', unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📌 Important Links & Documents")
    st.markdown("<p style='color: #a0a0a5;'>Access the team handbook, technique references, and event calendars below.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    r_col1, r_col2, r_col3 = st.columns(3)
    
    with r_col1:
        st.link_button("📘 Team Handbook", "https://docs.google.com/document", use_container_width=True)
    with r_col2:
        st.link_button("🎥 Paddling Technique Playlist", "https://youtube.com", use_container_width=True)
    with r_col3:
        st.link_button("👕 Team Merch Store", "https://example.com/merch", use_container_width=True)
        
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
        
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["✅ Confirm Attendance", "🚨 No-Show Log", "📜 Audit Log", "👥 Manage Roster"])
        
        @st.fragment
        def render_admin_form(ts_string):
            ts_active = df_signups[(df_signups['Practice Date'] == ts_string) & (df_signups['Status'] != 'Cancelled')] if not df_signups.empty else pd.DataFrame()
            
            with st.form(key=f"att_form_{ts_string}"):
                checkbox_states = {}
                if not ts_active.empty:
                    # Sort the active signups alphabetically by name
                    ts_active = ts_active.sort_values(by="Name")
                    
                    for i, row in ts_active.iterrows():
                        is_checked = row['Status'] in ['Active', 'Attended']
                        checkbox_states[row['id']] = st.checkbox(f"{row['Name']} (Current: {row['Status']})", value=is_checked)
                else:
                    st.info("No records pending confirmation.")
                
                st.markdown("---")
                # Inline Walk-In Feature
                all_names = df_roster['Name'].tolist() if not df_roster.empty else []
                current_names = ts_active['Name'].tolist() if not ts_active.empty else []
                
                # Sort the available walk-in dropdown names alphabetically 
                available_names = sorted([n for n in all_names if n not in current_names])
                walkin_name = st.selectbox("➕ Add Walk-In (Optional)", available_names, index=None, placeholder="Select a name to append to today's list...")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Submit Attendance & Walk-Ins", use_container_width=True):
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
                        st.success(f"Records updated for {ts_string.split(',')[0]}.")
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
                st.success("🎉 Amazing! Zero no-shows recorded so far.")
            else:
                c1, c2 = st.columns([1, 2.5])
                with c1:
                    offenders = no_shows_df['Name'].value_counts().reset_index()
                    offenders.columns = ['Name', 'Missed Practices']
                    st.dataframe(offenders, use_container_width=True, hide_index=True)
                with c2:
                    # Merge to bring in Side, Gender, and Membership
                    enriched_no_shows = pd.merge(no_shows_df, df_roster, on="Name", how="left")
                    log_display = enriched_no_shows[['Practice Date', 'Name', 'True Side', 'Gender', 'Membership']].sort_values(by='Practice Date', ascending=False)
                    st.dataframe(log_display, use_container_width=True, hide_index=True)
        with admin_tab3:
            st.markdown("### System Audit Log")
            st.caption("Scroll through the table to view all historical modifications.")
            df_audit = load_audit_log()
            if not df_audit.empty:
                # Streamlit's st.dataframe natively supports infinite virtual scrolling and pagination for large datasets
                st.dataframe(df_audit[['Timestamp', 'Action', 'Details']], use_container_width=True, hide_index=True, height=500)
            else:
                st.info("No system actions logged yet.")

        with admin_tab4:
            st.markdown("### Add New Paddler")
            with st.form("add_member_form"):
                c1, c2 = st.columns(2)
                with c1:
                    new_name = st.text_input("Full Name (Must be unique)")
                    new_gender = st.selectbox("Gender", ["Open", "Women", "Unknown"], index=2)
                with c2:
                    new_side = st.selectbox("True Side", ["Left", "Right", "Ambidextrous", "Unknown"], index=3)
                    new_mem = st.selectbox("Membership Tier", [
                        "Fall ONLY (without circuit)", 
                        "BOTH semesters (with circuit)", 
                        "Winter ONLY (without circuit)", 
                        "BOTH semesters (without circuit)",
                        "Unknown"
                    ], index=4)
                    
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Add to Roster", use_container_width=True):
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
                            st.success(f"🎉 {new_name} has been added and can now access the sign-up portal!")
                            st.rerun()

            st.divider()
            
            st.markdown("### Remove Paddler")
            st.markdown("Select a paddler to permanently remove them from the active roster.")
            
            all_roster_names = sorted(df_roster['Name'].tolist()) if not df_roster.empty else []
            remove_name = st.selectbox("Select Paddler to Remove", all_roster_names, index=None, placeholder="Search for a name...")
            
            if remove_name:
                with st.popover(f"🗑️ Remove {remove_name}", use_container_width=True):
                    st.error(f"**Warning:** This will permanently delete **{remove_name}** from the roster database and instantly wipe out any active sign-ups or waitlist queue positions they currently hold. This cannot be undone.")
                    if st.button("Confirm Permanent Removal", key=f"confirm_remove_{remove_name}"):
                        # 1. Delete from main roster
                        supabase.table("roster").delete().eq("Name", remove_name).execute()
                        
                        # 2. Wipe their ghost records to prevent UI bugs
                        supabase.table("signups").delete().eq("Name", remove_name).execute()
                        supabase.table("waitlist").delete().eq("Name", remove_name).execute()
                        
                        log_action("Roster Removal", f"{remove_name} was permanently removed from the system.")
                        load_roster.clear()
                        load_live_data.clear()
                        load_audit_log.clear()
                        st.rerun()

# --- 8. PAGE 4: MAIN SIGN UP (FRAGMENTED) ---
elif st.session_state.page == "Sign Up":
    st.markdown('<h1 class="main-title">McGill Dragon Boat Z</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Indoors Attendance 2026-2027</p>', unsafe_allow_html=True)

    if not is_open:
        st.info("🔒 Registration is currently closed. Sign-ups open every Monday at 8:00 PM.")
    else:
        st.markdown("""<div class="instructions">Welcome to the sign-up portal. Please select your name below and choose your preferred timeslot. To ensure everyone gets water time, attendance is strictly limited to <strong>one pool practice per week</strong>. If your schedule changes, simply log back in and cancel your spot to instantly free it up for a teammate. You can view the live attendee list in the sidebar at any time.<br><br>Each pool session is capped at <strong>32 paddlers</strong> to maintain an even split of 16 Lefts and 16 Rights. If you paddle on both sides or do not have a set preference yet, the system will automatically allocate your seat to keep the boat balanced.<br><br>If a practice reaches capacity, you will be added to a side-specific waitlist. Whenever a cancellation occurs, the system automatically promotes the next person in line based on a first-come, first-served order. You can also cancel your waitlist position directly from this portal.</div>""", unsafe_allow_html=True)
        st.divider()
        
        # --- NEW: User Login Flow ---
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None

        if not st.session_state.current_user:
            name_list = df_roster['Name'].tolist() if not df_roster.empty else []
            selected_name = st.selectbox("Select your Full Name", options=name_list, index=None, placeholder="Start typing your name here...")
            
            if selected_name:
                if st.button("Access Portal", use_container_width=True):
                    st.session_state.current_user = selected_name
                    st.rerun()
        else:
            user_name = st.session_state.current_user
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.success(f"Access granted for **{user_name}**")
            with col2:
                if st.button("Switch User", use_container_width=True):
                    st.session_state.current_user = None
                    st.rerun()
        
            @st.fragment
            def render_signup_portal(user_name):
                st.divider()
                
                user_data = df_roster[df_roster['Name'] == user_name].iloc[0]
                user_side = user_data.get('True Side', 'Unknown')
                user_membership = str(user_data.get('Membership', 'Unknown')).strip()
                user_eff_side = 'Left' if user_side in ['Unknown', 'Ambidextrous'] else user_side
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### Welcome, **{user_name}**")
                    st.markdown(f"**Membership:** {user_membership} | **Current Side:** {user_side}")
                with col2:
                    with st.popover("🔄 Update Side", use_container_width=True):
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
                        st.success(f"✅ You are actively signed up for **{day_name}**.")
                        if st.button(f"🚨 Cancel {day_name} Attendance", key=f"cancel_att_{ts_str}"):
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
                    st.markdown("### Sign Up for a Practice")
                    timeslot = st.radio("Select Practice:", available_timeslots)
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
                        st.error("🔒 You are already signed up for a pool practice this week. Attendance is strictly limited to one pool session.")
                    
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
                            
                        boat_full = (is_circuit and len(ts_active) >= 30) or \
                                    (is_pool and len(ts_active) >= 32) or \
                                    (is_pool and eff_side == 'Left' and current_left >= 16) or \
                                    (is_pool and eff_side == 'Right' and current_right >= 16)
                            
                        if st.button("Confirm Attendance", use_container_width=True):
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