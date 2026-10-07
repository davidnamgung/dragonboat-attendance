import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta
import pytz
import altair as alt

# --- 1. THEME & PAGE CONFIG ---
st.set_page_config(page_title="McGill Dragon Boat Z Attendance", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    [data-testid="stAppViewContainer"] {
        background-color: #0e1117; 
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #16181c;
        border-right: 1px solid #2b2d31;
    }
    
    .main-title {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 4rem;
        background: -webkit-linear-gradient(45deg, #ff3333, #ff7a7a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        padding-bottom: 0px;
        letter-spacing: -1.5px;
    }
    .sub-title {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 1.8rem;
        color: #8b8d91;
        margin-top: -5px;
        margin-bottom: 30px;
        letter-spacing: -0.5px;
    }
    .instructions {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #a0a0a5;
        max-width: 850px;
        margin: 0 auto;
        line-height: 1.6;
        background: #16181c;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2b2d31;
    }
    
    .stSelectbox label {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 600;
        color: #ffffff !important;
        text-align: center;
    }
    div[data-baseweb="select"] > div {
        background-color: #1a1c23 !important;
        border-radius: 12px !important;
        border: 1px solid #3a3d45 !important;
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
        box-shadow: 0 4px 6px rgba(255, 51, 51, 0.2);
    }
    .stButton>button:hover { 
        background-color: #ff4d4d !important; 
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 51, 51, 0.3);
    }
    
    .roster-card {
        background-color: #16181c;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #2b2d31;
        border-top: 4px solid #ff3333;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .roster-title {
        color: #ffffff;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        margin-bottom: 12px;
        border-bottom: 1px solid #2b2d31;
        padding-bottom: 8px;
    }
    .paddler-list {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        line-height: 1.6;
        color: #a0a0a5;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #16181c;
        border-radius: 8px;
        border: 1px solid #2b2d31;
        padding: 10px 20px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        color: #8b8d91;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff3333 !important;
        color: white !important;
        border-color: #ff3333 !important;
    }

    @media (max-width: 768px) {
        .main-title { font-size: 2.5rem; letter-spacing: -1px; }
        .sub-title { font-size: 1.4rem; }
        .instructions { font-size: 1rem; padding: 15px; text-align: left; }
        .stSelectbox label { font-size: 1.2rem !important; }
        .stTabs [data-baseweb="tab-list"] { display: flex; flex-direction: column; gap: 8px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. TIME GATE & DYNAMIC DATES ---
tz = pytz.timezone("America/Toronto")
now = datetime.now(tz)

# Offset time by 20 hours to force Monday before 8 PM to align with the previous week's logic
effective_now = now - timedelta(hours=20)
effective_monday = effective_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=effective_now.weekday())

thurs_dt = effective_monday + timedelta(days=3, hours=19)
fri_dt = effective_monday + timedelta(days=4, hours=18)

def format_date(d, time_str):
    suffix = 'th' if 11 <= d.day <= 13 else {1:'st', 2:'nd', 3:'rd'}.get(d.day % 10, 'th')
    return f"{d.strftime('%A, %B')} {d.day}{suffix} {time_str}"

thurs_str = format_date(thurs_dt, "7:00 PM - 8:00 PM")
fri_str = format_date(fri_dt, "6:00 PM - 7:00 PM")
TIMESLOTS = {thurs_str: thurs_dt, fri_str: fri_dt}

is_open = False
if now.weekday() == 0 and now.hour >= 20: 
    is_open = True
elif 1 <= now.weekday() <= 4:
    if now.weekday() == 4 and now.hour >= 19: 
        is_open = False
    else:
        is_open = True

# --- 3. DATABASE CONNECTION & CACHING ---
@st.cache_resource
def get_google_client():
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

client = get_google_client()
SHEET_ID = "1Ct8K5VzM3PcfJSbkok1InBRGr3yYnnjSp6VJU4OD8Og"
sheet = client.open_by_key(SHEET_ID)

roster_ws = sheet.worksheet("Roster")
signups_ws = sheet.worksheet("Signups")
waitlist_ws = sheet.worksheet("Waitlist")

@st.cache_data(ttl=600)
def load_roster():
    return pd.DataFrame(roster_ws.get_all_records())

@st.cache_data(ttl=30)
def load_live_data():
    return pd.DataFrame(signups_ws.get_all_records()), pd.DataFrame(waitlist_ws.get_all_records())

df_roster = load_roster()
df_signups, df_waitlist = load_live_data()

if 'Gender' not in df_roster.columns:
    df_roster['Gender'] = 'Unknown'
else:
    df_roster['Gender'] = df_roster['Gender'].replace(r'^\s*$', 'Unknown', regex=True).fillna('Unknown')
    df_roster['Gender'] = df_roster['Gender'].replace({'Male': 'Open', 'Female': 'Women', 'M': 'Open', 'F': 'Women'})

historical_dates = []
if not df_signups.empty:
    all_dates = df_signups['Practice Date'].unique().tolist()
    historical_dates = [d for d in all_dates if d not in TIMESLOTS.keys()]
    historical_dates.reverse() 

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
        st.session_state.page = "Lineups"
        st.rerun()
    if st.button("Analytics Dashboard", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.page = "Analytics"
        st.rerun()
    if st.button("Admin Dashboard", use_container_width=True):
        st.session_state.admin_authenticated = False
        st.session_state.page = "Admin"
        st.rerun()

def render_roster_card(ts_str, status_filter=['Active', 'Attended']):
    if not df_signups.empty:
        ts_active = df_signups[(df_signups['Practice Date'] == ts_str) & (df_signups['Status'].isin(status_filter))]
        merged = pd.merge(ts_active, df_roster, on="Name", how="left")
        lefts = merged[merged['True Side'].isin(['Left', 'Unknown', 'Ambidextrous'])]['Name'].tolist()
        rights = merged[merged['True Side'] == 'Right']['Name'].tolist()
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
    
    if not df_waitlist.empty and status_filter == ['Active']: 
        wl = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
        wl_names = wl['Name'].tolist()
        if wl_names:
            st.markdown("**Waitlist:**")
            st.markdown(f"<div class='paddler-list'>1. " + "<br>".join([f"{i+1}. {n}" for i, n in enumerate(wl_names)]) + "</div>", unsafe_allow_html=True)


# --- 5. PAGE 1: CURRENT LINEUPS ---
if st.session_state.page == "Lineups":
    st.markdown('<h1 class="main-title">Team Lineups</h1>', unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### This Week's Active Roster")
    col1, col2 = st.columns(2)
    for idx, (ts_str, ts_dt) in enumerate(TIMESLOTS.items()):
        target_col = col1 if idx == 0 else col2
        with target_col:
            st.markdown(f"#### {ts_str}")
            render_roster_card(ts_str, ['Active', 'Attended'])
            
    if historical_dates:
        st.divider()
        st.markdown("### Historical Lineups")
        for past_date in historical_dates:
            with st.expander(f"🚣‍♂️ {past_date}"):
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

# --- 7. PAGE 3: ADMIN DASHBOARD ---
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
        
        admin_tab1, admin_tab2 = st.tabs(["✅ Confirm Attendance", "🚨 No-Show Log"])
        
        def render_admin_form(ts_string, is_expander=False):
            if not df_signups.empty:
                ts_active = df_signups[(df_signups['Practice Date'] == ts_string) & (df_signups['Status'] != 'Cancelled')]
            else:
                ts_active = pd.DataFrame()
                
            if ts_active.empty:
                st.info("No records pending confirmation.")
            else:
                with st.form(key=f"att_form_{ts_string}"):
                    checkbox_states = {}
                    for i, row in ts_active.iterrows():
                        is_checked = row['Status'] in ['Active', 'Attended']
                        checkbox_states[i] = st.checkbox(f"{row['Name']} (Current: {row['Status']})", value=is_checked)
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Submit Attendance", use_container_width=True):
                        cells_to_update = []
                        for row_index_in_df, is_present in checkbox_states.items():
                            new_status = "Attended" if is_present else "No-Show"
                            actual_sheet_row = int(row_index_in_df) + 2 
                            cells_to_update.append(gspread.Cell(row=actual_sheet_row, col=4, value=new_status))
                            
                        if cells_to_update:
                            signups_ws.update_cells(cells_to_update)
                            
                        load_live_data.clear()
                        st.success(f"Records updated for {ts_string.split(',')[0]}.")
                        st.rerun()

        with admin_tab1:
            st.markdown("### Weekly Confirmation")
            st.caption("Uncheck the box for any paddler who did not show up. Submit to lock in the final roster.")
            
            col1, col2 = st.columns(2)
            for idx, (ts_str, ts_dt) in enumerate(TIMESLOTS.items()):
                target_col = col1 if idx == 0 else col2
                with target_col:
                    st.markdown(f"#### {ts_str.split(',')[0]} Practice")
                    render_admin_form(ts_str)
            
            if historical_dates:
                st.divider()
                st.markdown("### Edit Past Attendance")
                for past_date in historical_dates:
                    with st.expander(f"⚙️ Manage {past_date}"):
                        render_admin_form(past_date, is_expander=True)

        with admin_tab2:
            st.markdown("### No-Show Tracking")
            no_shows_df = df_signups[df_signups['Status'] == 'No-Show'] if not df_signups.empty else pd.DataFrame()
            
            if no_shows_df.empty:
                st.success("🎉 Amazing! Zero no-shows recorded so far.")
            else:
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown("**Repeat Offenders**")
                    offenders = no_shows_df['Name'].value_counts().reset_index()
                    offenders.columns = ['Name', 'Missed Practices']
                    st.dataframe(offenders, use_container_width=True, hide_index=True)
                    
                with c2:
                    st.markdown("**Complete Historical Log**")
                    log_display = no_shows_df[['Practice Date', 'Name']].sort_values(by='Practice Date', ascending=False)
                    st.dataframe(log_display, use_container_width=True, hide_index=True)

# --- 8. PAGE 4: MAIN SIGN UP ---
elif st.session_state.page == "Sign Up":
    st.markdown('<h1 class="main-title">McGill Dragon Boat Z</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Indoors Attendance 2026-2027</p>', unsafe_allow_html=True)

    if not is_open:
        st.info("🔒 Registration is currently closed. Sign-ups open every Monday at 8:00 PM.")
    else:
        st.markdown("""
        <div class="instructions">
            Welcome to the sign-up portal. Please select your name below and choose your preferred timeslot. To ensure everyone gets water time, attendance is strictly limited to <strong>one practice per week</strong>. If your schedule changes, simply log back in and cancel your spot to instantly free it up for a teammate. You can view the live attendee list in the sidebar at any time.
            <br><br>
            Each session is capped at <strong>32 paddlers</strong> to maintain an even split of 16 Lefts and 16 Rights. If you paddle on both sides or do not have a set preference yet, the system will automatically allocate your seat to keep the boat balanced. 
            <br><br>
            If a practice reaches capacity, you will be added to a side-specific waitlist. Whenever a cancellation occurs, the system automatically promotes the next person in line based on a first-come, first-served order. You can also cancel your waitlist position directly from this portal.
        </div>
        """, unsafe_allow_html=True)
    
        st.divider()
    
        name_list = df_roster['Name'].tolist() if not df_roster.empty else []
        user_name = st.selectbox("Select your Full Name", options=name_list, index=None, placeholder="Start typing your name here...")
    
        if user_name:
            st.divider()
            user_side = df_roster.loc[df_roster['Name'] == user_name, 'True Side'].values[0]
            user_eff_side = 'Left' if user_side in ['Unknown', 'Ambidextrous'] else user_side
            
            st.markdown(f"### Welcome, **{user_name}** | Side: **{user_side}**")
            
            for ts_str in TIMESLOTS.keys():
                day_name = ts_str.split(',')[0]
                
                active_record = pd.DataFrame()
                if not df_signups.empty:
                    active_record = df_signups[(df_signups['Practice Date'] == ts_str) & (df_signups['Name'] == user_name) & (df_signups['Status'].isin(['Active', 'Attended']))]
                    
                wl_record = pd.DataFrame()
                if not df_waitlist.empty:
                    wl_record = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Name'] == user_name) & (df_waitlist['Status'] == 'Waiting')]
                    
                if not active_record.empty:
                    st.success(f"✅ You are actively signed up for **{day_name}**.")
                    if st.button(f"🚨 Cancel {day_name} Attendance", key=f"cancel_att_{ts_str}"):
                        user_row_index = int(active_record.index[0]) + 2
                        signups_ws.update_cell(user_row_index, 4, "Cancelled")
                        
                        if not df_waitlist.empty:
                            pending = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
                            for idx, row in pending.iterrows():
                                pending_side = row['Side']
                                if pending_side == user_eff_side or pending_side in ['Unknown', 'Ambidextrous']:
                                    waitlist_ws.update_cell(int(row.name) + 2, 5, "Promoted")
                                    signups_ws.append_row([str(now), ts_str, row['Name'], "Active"])
                                    break
                                    
                        load_live_data.clear()
                        st.rerun()
                        
                elif not wl_record.empty:
                    pending_all = df_waitlist[(df_waitlist['Practice Date'] == ts_str) & (df_waitlist['Status'] == 'Waiting')].sort_values(by='Timestamp')
                    pos = pending_all['Name'].tolist().index(user_name) + 1
                    st.warning(f"⏳ You are **#{pos}** on the waitlist for **{day_name}**.")
                    if st.button(f"🚨 Cancel {day_name} Waitlist Position", key=f"cancel_wl_{ts_str}"):
                        user_wl_row_index = int(wl_record.index[0]) + 2
                        waitlist_ws.update_cell(user_wl_row_index, 5, "Cancelled")
                        
                        load_live_data.clear()
                        st.rerun()
                        
            st.divider()
            
            available_timeslots = []
            for ts in TIMESLOTS.keys():
                is_in_active = not df_signups.empty and not df_signups[(df_signups['Practice Date'] == ts) & (df_signups['Name'] == user_name) & (df_signups['Status'].isin(['Active', 'Attended']))].empty
                is_in_wl = not df_waitlist.empty and not df_waitlist[(df_waitlist['Practice Date'] == ts) & (df_waitlist['Name'] == user_name) & (df_waitlist['Status'] == 'Waiting')].empty
                
                if not is_in_active and not is_in_wl:
                    available_timeslots.append(ts)
                    
            if available_timeslots:
                st.markdown("### Sign Up for a Practice")
                timeslot = st.radio("Select Practice:", available_timeslots)
                target_dt = TIMESLOTS[timeslot] 
                
                active_all = df_signups[(df_signups['Name'] == user_name) & (df_signups['Status'].isin(['Active', 'Attended']))] if not df_signups.empty else pd.DataFrame()
                user_active_timeslots = active_all['Practice Date'].tolist() if not active_all.empty else []
                
                can_signup = True
                current_week_active = [ts for ts in user_active_timeslots if ts in TIMESLOTS.keys()]
                
                if len(current_week_active) >= 1:
                    cutoff_time = target_dt - timedelta(hours=2)
                    if now < cutoff_time:
                        can_signup = False
                        st.error("🔒 You are already signed up for a practice this week. You may only sign up for a second practice starting 2 hours before it begins.")
                        
                if can_signup:
                    if not df_signups.empty:
                        ts_active = df_signups[(df_signups['Practice Date'] == timeslot) & (df_signups['Status'].isin(['Active', 'Attended']))]
                        merged = pd.merge(ts_active, df_roster, on="Name", how="left")
                        left_count = len(merged[merged['True Side'].isin(['Left', 'Unknown', 'Ambidextrous'])])
                        right_count = len(merged[merged['True Side'] == 'Right'])
                        total_count = len(ts_active)
                    else:
                        left_count, right_count, total_count = 0, 0, 0
                        
                    boat_full = False
                    if total_count >= 32:
                        boat_full = True
                    elif user_eff_side == 'Left' and left_count >= 16:
                        boat_full = True
                    elif user_eff_side == 'Right' and right_count >= 16:
                        boat_full = True
                        
                    if st.button("Confirm Attendance", use_container_width=True):
                        if boat_full:
                            waitlist_ws.append_row([str(now), timeslot, user_name, user_side, "Waiting"])
                            st.warning(f"The {user_eff_side} side is full. You have been added to the waitlist!")
                        else:
                            signups_ws.append_row([str(now), timeslot, user_name, "Active"])
                            st.balloons()
                            
                        load_live_data.clear()
                        st.rerun()
            else:
                st.info("You are currently signed up or waitlisted for all available practices this week.")