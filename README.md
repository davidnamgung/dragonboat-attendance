# 🐉 McGill Dragon Boat Z (DBZ) — Indoor Attendance & Team Management Portal

A full-stack, real-time sports logistics and attendance management web application built for **McGill Dragon Boat Z (2026–2027 Season)**[cite: 17]. Powered by **Streamlit** and **Supabase (PostgreSQL)**, this platform automates weekly practice registrations, enforces boat-balancing constraints, manages side-specific waitlists, and provides executive analytics and administrative controls[cite: 17].

---

## 🎯 The Problem It Solves

Managing indoor pool and circuit training for a large collegiate dragon boat roster presents several logistical bottlenecks:

* **Strict Boat Balancing:** Pool sessions are capped at **32 paddlers** and require an exact **16 Left / 16 Right** split to keep the setup balanced[cite: 17]. Traditional spreadsheets or static forms cannot dynamically route ambidextrous paddlers or block one side when full while keeping the other open[cite: 17].
* **Waitlist & Cancellation Bottlenecks:** When a paddler cancels last-minute, executives previously had to manually message waitlisted athletes matching that specific paddling side.
* **Membership & Quota Enforcement:** Paddlers have different membership tiers (e.g., with or without circuit access) and are restricted to **1 pool session and 1 circuit session per week** to guarantee fair water time across the club[cite: 17].
* **High-Traffic Race Conditions:** Sign-ups open simultaneously for the entire club every Monday at 8:00 PM EST, creating concurrent database writes for the final available seats[cite: 17].

---

## ⚙️ Core Architecture & Engineering Highlights

* **Automated Time-Gate Engine (`pytz`):** Registration automatically unlocks on Mondays at 8:00 PM (`America/Toronto`) and locks on Fridays at 7:00 PM, dynamically rolling over target session dates each week using an effective Monday anchor[cite: 17].
* **Algorithmic Seat & Side Balancing:** Evaluates strict Left and Right headcounts first, mathematically distributes existing `Ambidextrous` / `Unknown` paddlers to the lighter side, and dynamically routes incoming sign-ups to maintain an even 16/16 pool split (or 24-spot general cap for Circuit)[cite: 17].
* **Automated Waitlist Promotion:** Canceling an active spot (via user portal or admin removal) triggers an immediate scan of the `waitlist` table ordered by timestamp, automatically promoting the first eligible paddler whose paddling side matches the vacated seat[cite: 17].
* **Database-Level Concurrency Protection:** Interfaces with Supabase PostgreSQL triggers (`BOAT_FULL` exception handling) to catch millisecond race conditions during peak registration, seamlessly rerouting overflow users to the waitlist[cite: 17].
* **Custom Glassmorphic UI:** Features custom CSS animations, responsive typography (`clamp()`), adjacent sibling CSS hooks for isolated Streamlit widget styling, and partial page reruns (`@st.fragment`) for lag-free interactions[cite: 17].

---

## 🖥️ Application Modules & Sub-Tabs

### 1. Sign-Up Portal (`Sign Up`)
The primary athlete-facing interface[cite: 17].
* **Dynamic Deadline Banner:** Displays a database-driven global announcement above the portal until the configured deadline timestamp expires, automatically reverting to a default notice afterward[cite: 17].
* **Verified Paddler ID Card:** Displays the logged-in athlete's Membership Tier and True Side, featuring an inline popover to update their paddling side in real time[cite: 17].
* **Rule & Quota Validation:** Blocks circuit registration for non-circuit membership tiers and prevents signing up for a second pool session in the same week[cite: 17].
* **One-Click Cancellation:** Allows users to view their active registrations or current numerical waitlist position (`#1`, `#2`, etc.) and cancel with instant waitlist backfill[cite: 17].

### 2. Current Lineups (`Lineups`)
A live, public-facing view of weekly boat rosters[cite: 17].
* **Weekly Curriculum Teaser:** Dynamically calculates the current training week (anchored to the 8-week fall curriculum starting October 12, 2026) and displays the coaching focus banner above the session cards[cite: 17].
* **Real-Time Progress Bars:** Visualizes capacity for Thursday Pool (7:00–8:00 PM, Intermediate/Advanced), Friday Pool (6:00–7:00 PM, Beginner-Friendly), and Friday Circuit (7:00–8:00 PM, For All) alongside ordered waitlist queues[cite: 17].
* **Historical Lineups Archive:** Groups past practice dates by week inside collapsible expanders, preserving the specific training theme and final attendance roster for each historical week[cite: 17].

### 3. Analytics Dashboard (`Analytics`)
Provides executive insights into club engagement and demographics across three sub-tabs[cite: 17]:
* **📊 Master Database:** Displays glassmorphic KPI summary cards (*Total Active Roster*, *Total Practices Logged*, *Waitlist Demand*) and an interactive, multi-filterable dataframe tracking each paddler's independent Pool and Circuit attendance counts and attendance rates[cite: 17].
* **🧩 Team Composition:** Renders interactive Altair donut charts breaking down the club by **Side Distribution** (Left, Right, Ambidextrous, Unknown), **Gender Distribution** (Open, Women), **Membership Tiers**, and side splits within Open and Women categories[cite: 17].
* **📈 Attendance Trends:** Plots a multi-series, monotone-interpolated Altair line chart tracking historical turnout across Thursday Pool, Friday Pool, and Friday Circuit sessions over time[cite: 17].

### 4. Team Resources (`Resources`)
A centralized hub for club documentation and governance[cite: 17]:
* **Executive & Coaching Directory:** A centered popover listing the 2026–2027 Executive Team and Coaching Staff[cite: 17].
* **Mandatory Team Waiver:** Highlighted direct link to the season waiver form[cite: 17].
* **Resource Grid:** Quick-access cards linking to Fall Info Session slides, Injury Prevention Guidelines, Competition Checklists, Canal Fitness Transit Guides, Dragon Boat 101, Race Rankings, Club History, and the team YouTube channel[cite: 17].

### 5. Admin Dashboard (`Admin`)
A password-protected (`st.session_state.admin_authenticated`) executive control center divided into six sub-tabs[cite: 17]:
* **✅ Confirm Attendance:** Allows coaches/admins to check off attended paddlers, mark no-shows, forcibly remove active sign-ups (triggering automatic waitlist promotion), append last-minute **Walk-Ins**, or wipe practice data for a specific date[cite: 17].
* **🚨 No-Show Log:** Aggregates missed practices per paddler into an offender leaderboard alongside an enriched log detailing the date, side, gender, and membership tier of every recorded no-show[cite: 17].
* **📜 Audit Log:** A chronological, timezone-adjusted system ledger tracking all user and admin mutations (sign-ups, cancellations, waitlist promotions, walk-ins, roster edits, and financial updates)[cite: 17].
* **👥 Manage Roster:** Full CRUD interface to add new unique paddlers or search, edit, and permanently delete existing profiles (cascading updates across `roster`, `signups`, and `waitlist` tables)[cite: 17].
* **💳 Waivers & Payments:** Features circular CSS conic-gradient progress rings tracking club-wide waiver and payment completion percentages, paired with an interactive `st.data_editor` grid to batch-update statuses[cite: 17].
* **📢 Announcements:** A live CMS form allowing admins to write custom HTML/Markdown global reminders and set expiration dates/times without modifying source code[cite: 17].

---

## 🛠️ Tech Stack

* **Frontend & Framework:** Streamlit (Python), Custom HTML5/CSS3[cite: 17]
* **Backend & Database:** Supabase (PostgreSQL, PostgREST API)[cite: 17]
* **Data Manipulation & Visualization:** Pandas, Altair[cite: 17]
* **Time & Concurrency Management:** `pytz`, Streamlit Fragments (`@st.fragment`), Caching (`@st.cache_data`, `@st.cache_resource`)[cite: 17]