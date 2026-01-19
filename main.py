import streamlit as st
import pandas as pd
import altair as alt
import time
from database import CoachDB
from brain import CoachBrain

# --- CONFIG ---
st.set_page_config(page_title="Aditya's HQ", page_icon="⚡", layout="wide")
db = CoachDB()
brain = CoachBrain(db)

# CSS
st.markdown("""
<style>
    /* Make the Progress Bar Green */
    .stProgress > div > div > div > div { background-color: #00FF00; }
    
    /* Fix Chat Bubbles: Light Background + BLACK Text */
    .stChatMessage { 
        background-color: #f0f2f6; 
        border-radius: 10px; 
        padding: 10px; 
        color: black !important; /* Forces text to be black */
    }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
with st.sidebar:
    st.title("⚡ SUPER COACH")
    mode = st.radio("Mode", ["🤖 Commander", "📊 Dashboard"])
    st.divider()

# ==========================================
# MODE 1: COMMANDER (Chat & Daily Plan)
# ==========================================
if mode == "🤖 Commander":
    # (This is your existing Chat/Schedule code)
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
            pct = min(value / target, 1.0)
            st.write(f"**{name}**")
            st.progress(pct)
            st.caption(f"{int(value)}/{int(target)} {unit}")

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
        
        with st.spinner("Processing..."):
            time.sleep(0.3)
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
        db.log_chat("assistant", response)
        st.rerun()

# ==========================================
# MODE 2: DASHBOARD (Visuals)
# ==========================================
elif mode == "📊 Dashboard":
    st.title("📊 Performance Analytics")

    # 1. CONSISTENCY HEATMAP (The "Green Dots")
    st.subheader("🔥 Consistency Streak")
    
    cons_data = db.get_consistency_data()
    if cons_data:
        df_cons = pd.DataFrame(cons_data, columns=['date', 'count'])
        df_cons['date'] = pd.to_datetime(df_cons['date'])
        
        # Create a GitHub-style Heatmap using Altair
        heatmap = alt.Chart(df_cons).mark_rect().encode(
            x=alt.X('date:O', timeUnit='yearmonthdate', title='Date'),
            y=alt.Y('count:Q', title='Tasks Completed'),
            color=alt.Color('count:Q', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['date', 'count']
        ).properties(width=700, height=150)
        
        st.altair_chart(heatmap, use_container_width=True)
    else:
        st.info("No data yet. Start logging tasks to see your streak!")

    st.divider()

    # 2. PROGRESS CHARTS (Line Charts)
    st.subheader("📈 Metric Trends")
    
    # Dropdown to select metric
    all_goals = db.get_all_goal_names()
    metric = st.selectbox("Select Metric to View:", all_goals, index=0 if all_goals else None)
    
    if metric:
        history = db.get_metric_history(metric)
        if history:
            df_hist = pd.DataFrame(history, columns=['date', 'value'])
            df_hist['date'] = pd.to_datetime(df_hist['date'])
            
            # Interactive Line Chart
            chart = alt.Chart(df_hist).mark_line(point=True).encode(
                x='date:T',
                y=alt.Y('value:Q', title=metric),
                tooltip=['date', 'value']
            ).properties(height=400)
            
            st.altair_chart(chart, use_container_width=True)
            
            # Simple Stat
            avg_val = df_hist['value'].mean()
            max_val = df_hist['value'].max()
            st.caption(f"**Stats for {metric}:** Max: {max_val} | Average: {avg_val:.1f}")
            
        else:
            st.warning(f"No history found for {metric}. Log some data first!")