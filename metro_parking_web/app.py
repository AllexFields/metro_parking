"""
app.py — Ahmedabad Metro Parking Management System
Streamlit Web Application

Run locally:  streamlit run app.py
Deploy:       Push to GitHub → connect on share.streamlit.io
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from core.models  import Vehicle, ParkingLot, RATE_TWO_WHEELER, RATE_FOUR_WHEELER
from core.storage import save_session, load_sessions, daily_summary, search_vehicle_history
from core.charts  import (capacity_donut, hourly_traffic, daily_revenue_trend,
                           vehicle_type_split, revenue_by_type,
                           duration_histogram, slot_heatmap)

# ─────────────────────────────────────────────────────────────────────────────
# Page config  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Metro Parking — Ahmedabad",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  /* Metric cards */
  [data-testid="metric-container"] {
      background: #1E293B;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 16px;
  }
  /* Success / error boxes */
  .stAlert { border-radius: 10px; }
  /* Sidebar nav */
  .css-1d391kg { padding-top: 1rem; }
  /* Hide footer */
  footer { visibility: hidden; }
  /* Slot badge */
  .slot-badge {
      display:inline-block; padding:4px 10px;
      border-radius:6px; font-weight:600; font-size:13px; margin:2px;
  }
  .slot-free     { background:#064E3B; color:#6EE7B7; }
  .slot-occupied { background:#450A0A; color:#FCA5A5; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Station Configuration (edit here to change station)
# ─────────────────────────────────────────────────────────────────────────────

STATION_NAME       = "Kalupur Metro Station"
TWO_WHEELER_SLOTS  = 20
FOUR_WHEELER_SLOTS = 10
OPERATOR_PIN       = "1234"

# ─────────────────────────────────────────────────────────────────────────────
# Session State — keeps ParkingLot alive across reruns
# ─────────────────────────────────────────────────────────────────────────────

if "lot" not in st.session_state:
    st.session_state.lot = ParkingLot(STATION_NAME, TWO_WHEELER_SLOTS, FOUR_WHEELER_SLOTS)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "last_action" not in st.session_state:
    st.session_state.last_action = None

lot: ParkingLot = st.session_state.lot

# ─────────────────────────────────────────────────────────────────────────────
# Login Gate
# ─────────────────────────────────────────────────────────────────────────────

def login_page():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🚇 Metro Parking System")
        st.markdown(f"**{STATION_NAME}** · GMRC")
        st.markdown("---")
        pin = st.text_input("Operator PIN", type="password", placeholder="Enter PIN")
        if st.button("Login →", use_container_width=True, type="primary"):
            if pin == OPERATOR_PIN:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Incorrect PIN. Try again.")
        st.caption("Default PIN: 1234  |  Change in app.py → OPERATOR_PIN")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar Navigation
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🚇 Metro Parking")
    st.caption(STATION_NAME)
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "🚗 Park Vehicle", "🚪 Vehicle Exit",
         "🗺️ Slot Map", "🔍 Search Vehicle",
         "📊 Analytics", "📋 Session History"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Live capacity mini-view in sidebar
    cap = lot.capacity_summary()
    for vtype, label in (("2W", "Two-Wheeler"), ("4W", "Four-Wheeler")):
        d = cap[vtype]
        pct = int(d["occupied"] / d["total"] * 100) if d["total"] else 0
        st.caption(f"{label}: {d['free']} free / {d['total']}")
        st.progress(pct / 100)

    st.markdown("---")
    if st.button("🔒 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def page_header(icon, title, subtitle=""):
    st.markdown(f"## {icon} {title}")
    if subtitle:
        st.caption(subtitle)
    st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Dashboard
# ─────────────────────────────────────────────────────────────────────────────

if page == "🏠 Dashboard":
    page_header("🏠", "Dashboard", f"{STATION_NAME}  ·  {datetime.now().strftime('%d %b %Y, %H:%M')}")

    df      = load_sessions()
    today   = daily_summary(df)
    cap     = lot.capacity_summary()
    overstay = list(lot.overstay_alerts())

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Today's Revenue", f"₹{today['total_revenue']}", help="Total fee collected today")
    k2.metric("Sessions Today",  today["total_sessions"])
    k3.metric("2W Free Slots",   cap["2W"]["free"],
              delta=f"{cap['2W']['free']} of {cap['2W']['total']}")
    k4.metric("4W Free Slots",   cap["4W"]["free"],
              delta=f"{cap['4W']['free']} of {cap['4W']['total']}")
    k5.metric("⚠ Overstays",     len(overstay),
              delta_color="inverse" if overstay else "normal")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Donut + Recent sessions ───────────────────────────────────────────────
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("**Two-Wheeler Capacity**")
        st.plotly_chart(
            capacity_donut(cap["2W"]["occupied"], cap["2W"]["free"], "2W Slots"),
            use_container_width=True, config={"displayModeBar": False},
        )
    with d2:
        st.markdown("**Four-Wheeler Capacity**")
        st.plotly_chart(
            capacity_donut(cap["4W"]["occupied"], cap["4W"]["free"], "4W Slots"),
            use_container_width=True, config={"displayModeBar": False},
        )
    with d3:
        st.markdown("**Vehicle Mix (All Time)**")
        st.plotly_chart(
            vehicle_type_split(df),
            use_container_width=True, config={"displayModeBar": False},
        )

    # ── Currently parked ─────────────────────────────────────────────────────
    st.markdown("### Currently Parked")
    parked = lot.all_slots_as_list()
    parked_now = [s for s in parked if s["Status"] != "🟢 Free"]
    if parked_now:
        st.dataframe(
            pd.DataFrame(parked_now)[["Slot ID","Type","Vehicle","Entry Time","Duration(h)","Est. Fee (₹)"]],
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("No vehicles currently parked.")

    # ── Overstay alert box ────────────────────────────────────────────────────
    if overstay:
        st.markdown("### ⚠️ Overstay Alerts")
        for v, sid, hrs in overstay:
            st.warning(f"**{v.number}** · Slot {sid} · Parked {hrs} hours — exceeds 12h limit")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Park Vehicle
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🚗 Park Vehicle":
    page_header("🚗", "Park a Vehicle", "Register a new vehicle and assign a slot")

    cap = lot.capacity_summary()

    col1, col2 = st.columns([1, 1])
    with col1:
        with st.form("park_form"):
            st.markdown("#### Vehicle Details")
            number = st.text_input("Number Plate", placeholder="GJ01AB1234").upper()
            vtype  = st.radio(
                "Vehicle Type",
                ["2W — Two-Wheeler  (₹10/hr)", "4W — Four-Wheeler  (₹20/hr)"],
            )
            vtype_code = "2W" if vtype.startswith("2W") else "4W"
            submitted  = st.form_submit_button("✅ Assign Slot & Park", type="primary", use_container_width=True)

        if submitted:
            if not number:
                st.error("Please enter a number plate.")
            elif lot.find_vehicle(number):
                st.warning(f"**{number}** is already parked in this lot.")
            elif lot.is_full(vtype_code):
                st.error(f"No {vtype_code} slots available. Lot is full.")
            else:
                try:
                    vehicle = Vehicle(number, vtype_code)
                    slot    = lot.park_vehicle(vehicle)
                    st.success(f"✅ **{number}** parked at slot **{slot.slot_id}**")
                    st.info(f"Entry time: {vehicle.entry_time.strftime('%H:%M:%S  %d %b %Y')}  |  Rate: ₹{vehicle.hourly_rate()}/hr")
                    st.session_state.last_action = f"Parked {number} → {slot.slot_id}"
                except ValueError as e:
                    st.error(str(e))

    with col2:
        st.markdown("#### Slot Availability")
        for vt, label in (("2W", "Two-Wheeler"), ("4W", "Four-Wheeler")):
            d   = cap[vt]
            pct = int(d["occupied"] / d["total"] * 100) if d["total"] else 0
            st.markdown(f"**{label}**")
            st.progress(pct / 100, text=f"{d['occupied']} occupied · {d['free']} free · {d['total']} total")

        st.markdown("#### Available Slots")
        for vt in ("2W", "4W"):
            slots = lot.available_slots(vt)
            if slots:
                badges = " ".join(
                    f'<span class="slot-badge slot-free">{s.slot_id}</span>'
                    for s in slots[:12]
                )
                st.markdown(f"**{vt}:** " + badges, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Vehicle Exit
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🚪 Vehicle Exit":
    page_header("🚪", "Vehicle Exit", "Process exit and collect parking fee")

    col1, col2 = st.columns([1, 1])
    with col1:
        number = st.text_input("Vehicle Number Plate", placeholder="GJ01AB1234").upper()
        if number:
            slot = lot.find_vehicle(number)
            if not slot:
                st.error(f"**{number}** is not currently parked here.")
            else:
                v        = slot.vehicle
                fee      = v.compute_fee()
                duration = round(v.duration_hours(), 2)

                st.markdown("#### Exit Summary")
                r1, r2 = st.columns(2)
                r1.metric("Vehicle",     v.number)
                r2.metric("Slot",        slot.slot_id)
                r1.metric("Duration",    f"{duration} hrs")
                r2.metric("Fee Due",     f"₹{fee}")

                if v.is_overstay():
                    st.warning(f"⚠️ Overstay: Vehicle has been parked for {duration} hours (limit: 12h)")

                if st.button(f"✅ Confirm Exit & Collect ₹{fee}", type="primary", use_container_width=True):
                    exit_time = datetime.now()
                    vehicle_out, slot_out, final_fee = lot.exit_vehicle(number)
                    save_session(vehicle_out, slot_out.slot_id, lot.station_name, exit_time, final_fee)
                    st.success(f"✅ **{number}** exited. Slot **{slot_out.slot_id}** is now free.")
                    st.balloons()
                    st.session_state.last_action = f"Exited {number} | ₹{final_fee} collected"

    with col2:
        st.markdown("#### All Currently Parked Vehicles")
        occupied = lot.occupied_slots()
        if occupied:
            data = [{
                "Number Plate": s.vehicle.number,
                "Type"        : s.vehicle.TYPES[s.vehicle.vehicle_type],
                "Slot"        : s.slot_id,
                "Duration (h)": round(s.vehicle.duration_hours(), 2),
                "Est. Fee"    : f"₹{s.vehicle.compute_fee()}",
            } for s in occupied]
            selected = st.dataframe(
                pd.DataFrame(data), use_container_width=True, hide_index=True,
            )
        else:
            st.info("No vehicles currently parked.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Slot Map
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🗺️ Slot Map":
    page_header("🗺️", "Live Slot Map", "Real-time view of all parking slots")

    st.markdown("🟢 = Free &nbsp;&nbsp;&nbsp; 🔴 = Occupied")
    st.markdown("---")

    for vtype, label in (("2W", "Two-Wheeler Slots"), ("4W", "Four-Wheeler Slots")):
        st.markdown(f"#### {label}")
        slots     = [s for s in lot.slots.values() if s.slot_type == vtype]
        per_row   = 5
        # Build rows of 5
        for i in range(0, len(slots), per_row):
            cols = st.columns(per_row)
            for j, slot in enumerate(slots[i:i+per_row]):
                with cols[j]:
                    if slot.is_empty:
                        st.markdown(
                            f'<div class="slot-badge slot-free" style="width:100%;text-align:center">'
                            f'🟢 {slot.slot_id}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div class="slot-badge slot-occupied" style="width:100%;text-align:center">'
                            f'🔴 {slot.slot_id}<br>'
                            f'<small>{slot.vehicle.number}</small></div>',
                            unsafe_allow_html=True,
                        )
        st.markdown("<br>", unsafe_allow_html=True)

    # Heatmap chart
    st.markdown("#### Slot Heatmap")
    st.plotly_chart(
        slot_heatmap(lot.all_slots_as_list()),
        use_container_width=True, config={"displayModeBar": False},
    )

    if st.button("🔄 Refresh"):
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Search Vehicle
# ─────────────────────────────────────────────────────────────────────────────

elif page == "🔍 Search Vehicle":
    page_header("🔍", "Search Vehicle", "Look up any vehicle — current or historical")

    number = st.text_input("Enter Number Plate", placeholder="GJ01AB1234").upper()

    if number:
        # Current status
        slot = lot.find_vehicle(number)
        if slot:
            v = slot.vehicle
            st.success(f"✅ **{number}** is currently parked")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Slot",        slot.slot_id)
            c2.metric("Type",        v.TYPES[v.vehicle_type])
            c3.metric("Duration",    f"{round(v.duration_hours(), 2)} hrs")
            c4.metric("Est. Fee",    f"₹{v.compute_fee()}")
            if v.is_overstay():
                st.warning("⚠️ This vehicle has exceeded the 12-hour overstay limit!")
        else:
            st.info(f"**{number}** is not currently parked in this lot.")

        # History
        df      = load_sessions()
        history = search_vehicle_history(df, number)
        if not history.empty:
            st.markdown("#### Visit History")
            total_visits = len(history)
            total_spent  = history["fee"].sum()
            h1, h2, h3 = st.columns(3)
            h1.metric("Total Visits",  total_visits)
            h2.metric("Total Spent",   f"₹{round(total_spent, 2)}")
            h3.metric("Avg Duration",  f"{round(history['duration_hrs'].mean(), 2)} hrs")

            st.dataframe(
                history[["entry_time", "exit_time", "slot_id", "duration_hrs", "fee"]]
                .rename(columns={
                    "entry_time"  : "Entry",
                    "exit_time"   : "Exit",
                    "slot_id"     : "Slot",
                    "duration_hrs": "Duration (h)",
                    "fee"         : "Fee (₹)",
                }),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("No past sessions found for this vehicle.")


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Analytics
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📊 Analytics":
    page_header("📊", "Analytics", "Revenue trends, traffic patterns, and insights")

    df = load_sessions()

    if df.empty:
        st.info("No session data yet. Park and exit some vehicles to see analytics.")
        st.stop()

    # Date filter
    st.markdown("#### Filters")
    if "date" in df.columns and not df.empty:
        all_dates = sorted(df["date"].unique(), reverse=True)
        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            filter_mode = st.selectbox("View", ["All Time", "Today", "Custom Date"])
        if filter_mode == "Today":
            filtered_df = df[df["date"] == datetime.now().date()]
        elif filter_mode == "Custom Date" and all_dates:
            with col_f2:
                chosen = st.selectbox("Pick date", all_dates)
            filtered_df = df[df["date"] == chosen]
        else:
            filtered_df = df
    else:
        filtered_df = df

    st.markdown("---")

    # Summary metrics
    today_s = daily_summary(df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Sessions",    len(filtered_df))
    m2.metric("Total Revenue",     f"₹{round(filtered_df['fee'].sum(), 2)}")
    m3.metric("Avg Duration",      f"{round(filtered_df['duration_hrs'].mean(), 2)} hrs")
    m4.metric("Avg Fee / Session", f"₹{round(filtered_df['fee'].mean(), 2)}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row 1
    ch1, ch2 = st.columns(2)
    with ch1:
        st.plotly_chart(daily_revenue_trend(filtered_df), use_container_width=True)
    with ch2:
        st.plotly_chart(hourly_traffic(filtered_df), use_container_width=True)

    # Charts row 2
    ch3, ch4 = st.columns(2)
    with ch3:
        st.plotly_chart(revenue_by_type(filtered_df), use_container_width=True)
    with ch4:
        st.plotly_chart(duration_histogram(filtered_df), use_container_width=True)

    # Download button
    st.markdown("---")
    st.markdown("#### Export Data")
    csv = filtered_df.drop(columns=["date", "hour"], errors="ignore").to_csv(index=False)
    st.download_button(
        label     = "⬇️ Download CSV",
        data      = csv,
        file_name = f"metro_parking_{datetime.now().strftime('%Y%m%d')}.csv",
        mime      = "text/csv",
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: Session History
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📋 Session History":
    page_header("📋", "Session History", "All completed parking sessions")

    df = load_sessions()
    if df.empty:
        st.info("No sessions recorded yet.")
        st.stop()

    # Filters
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        vtype_filter = st.multiselect("Vehicle Type", ["2W", "4W"], default=["2W", "4W"])
    with col_b:
        station_filter = st.multiselect("Station", df["station"].unique().tolist(),
                                        default=df["station"].unique().tolist())

    filtered = df[
        (df["vehicle_type"].isin(vtype_filter)) &
        (df["station"].isin(station_filter))
    ].copy()

    st.caption(f"Showing {len(filtered)} of {len(df)} sessions")

    display_cols = {
        "vehicle_number": "Number Plate",
        "vehicle_type"  : "Type",
        "slot_id"       : "Slot",
        "station"       : "Station",
        "entry_time"    : "Entry",
        "exit_time"     : "Exit",
        "duration_hrs"  : "Duration (h)",
        "fee"           : "Fee (₹)",
    }
    filtered_display = filtered[list(display_cols.keys())].rename(columns=display_cols)
    filtered_display = filtered_display.sort_values("Exit", ascending=False)

    st.dataframe(filtered_display, use_container_width=True, hide_index=True)

    # Last action toast
    if st.session_state.last_action:
        st.toast(st.session_state.last_action, icon="✅")
        st.session_state.last_action = None
