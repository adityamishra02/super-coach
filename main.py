import streamlit as st
import pandas as pd
import altair as alt
import time
from database import CoachDB
from brain import CoachBrain

# --- CONFIG ---
st.set_page_config(page_title="Aditya's HQ", page_icon="⚡", layout="wide")

# CSS Styling
st.markdown("""
<style>
    .stProgress > div > div > div > div { background-color: #00FF00; }
    .stChatMessage { 
        background-color: #f0f2f6; 
        border-radius: 10px; 
        padding: 10px; 
        color: black !important; 
    }
    /* Morning Protocol Alert */
    div[data-testid="stNotification"] {
        border-left: 5px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
db = CoachDB()
brain = CoachBrain(db)

# ==========================================
# 🛑 MORNING PROTOCOL (THE GATEKEEPER)
# ==========================================
if not db.is_weight_logged_today():
    st.title("⚠️ Morning Protocol")
    st.error("You cannot access the dashboard until you log your weight.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        weight_input = st.number_input("Current Weight (kg)", min_value=50.0, max_value=120.0, step=0.1)
    
    if st.button("LOG WEIGHT & UNLOCK 🔓", type="primary"):
        with st.spinner("Logging..."):
            db.log_metric("Weight", weight_input)
            st.success("Weight logged. Unlocking system...")
            time.sleep(1)
            st.rerun()
            
    st.stop() # <--- This stops the rest of the app from loading!

# ==========================================
# 🚀 MAIN APP (Only loads if weight is logged)
# ==========================================

# --- NAVIGATION ---
with st.sidebar:
    st.title("⚡ SUPER COACH")
    mode = st.radio("Mode", ["🤖 Commander", "📊 Dashboard", "📜 History"])
    st.divider()

# MODE 1: COMMANDER (Chat)
if mode == "🤖 Commander":
    with st.sidebar:
        st.subheader("📅 Orders")
        schedule = db.get_full_schedule()
        if not schedule:
            st.info("No plan. Type 'Plan my day'.")
        else:
            for time_slot, task, status in schedule:
                if status == "DONE":
                    st.markdown(f"✅ ~~{time_slot} - {task}~~")
                elif status == "PENDING":
                    st.markdown(f"**⏳ {time_slot} - {task}** 👈")
                else:
                    st.write(f"{time_slot} - {task}")
        
        st.divider()
        st.subheader("📊 Today's Stats")
        stats = db.get_progress()
        for name, target, unit, value, rpe in stats:
            pct = min(value / target, 1.0) if target > 0 else 0
            st.write(f"**{name}**")
            st.progress(pct)
            st.caption(f"{float(value)}/{int(target)} {unit}")

    # Chat Interface
    st.header("🤖 Coach Uplink")
    if "messages" not in st.session_state:
        st.session_state.messages = []
        history = db.get_chat_history(10)
        for sender, msg in history:
            st.session_state.messages.append({"role": sender, "content": msg})

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Enter command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        db.log_chat("user", prompt)

        response = brain.process_input(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
        db.log_chat("assistant", response)
        st.rerun()

# MODE 2: DASHBOARD
elif mode == "📊 Dashboard":
    st.title("📊 Performance Analytics")
    
    # Consistency Heatmap
    st.subheader("🔥 Consistency Streak")
    cons_data = db.get_consistency_data()
    if cons_data:
        df_cons = pd.DataFrame(cons_data, columns=['date', 'count'])
        df_cons['date'] = pd.to_datetime(df_cons['date'])
        heatmap = alt.Chart(df_cons).mark_rect().encode(
            x=alt.X('date:O', timeUnit='yearmonthdate', title='Date'),
            y=alt.Y('count:Q', title='Tasks'),
            color=alt.Color('count:Q', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['date', 'count']
        ).properties(width=700, height=150)
        st.altair_chart(heatmap, use_container_width=True)

    st.divider()
    
    # Metric Trends
    st.subheader("📈 Metric Trends")
    all_goals = db.get_all_goal_names()
    metric = st.selectbox("Select Metric:", all_goals)
    if metric:
        history = db.get_metric_history(metric)
        if history:
            df_hist = pd.DataFrame(history, columns=['date', 'value'])
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            chart = alt.Chart(df_hist).mark_line(point=True).encode(
                x='date:T', y='value:Q', tooltip=['date', 'value']
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

# MODE 3: HISTORY
elif mode == "📜 History":
    st.title("📜 Raw Logbook")
    
    raw_data = db.get_raw_history()
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        # Filter Options
        col1, col2 = st.columns(2)
        with col1:
            # Get unique goal names for the filter
            options = df['goal_name'].unique().tolist()
            selected_metrics = st.multiselect("Filter by Metric", options)
        
        # Apply Filter
        if selected_metrics:
            df = df[df['goal_name'].isin(selected_metrics)]
            
        # Sort by Date (Newest First)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(by='date', ascending=False)
            
            # Display Table
            st.dataframe(
                df, 
                use_container_width=True,
                column_config={
                    "date": st.column_config.DateColumn("Date", format="DD MMM YYYY"),
                    "value": st.column_config.NumberColumn("Value"),
                    "rpe": "RPE / Notes"
                },
                hide_index=True
            )
    else:
        st.info("No logs found yet.")