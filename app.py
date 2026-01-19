import streamlit as st
import pandas as pd
from coach_db import SuperCoachDB

# Initialize Database
db = SuperCoachDB()

# Page Setup
st.set_page_config(page_title="Aditya's Super Coach", page_icon="⚡", layout="centered")

# --- HEADER ---
st.title("⚡ Aditya's Super Coach")
st.caption(f"Date: {pd.Timestamp.now().strftime('%A, %B %d, %Y')}")

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Coach Settings")
    
    with st.expander("➕ Add New Goal"):
        new_cat = st.selectbox("Category", ["Athleticism", "Career", "Lifestyle"])
        new_goal = st.text_input("Goal Name (e.g., 'Running')")
        new_target = st.number_input("Target", min_value=1.0, value=10.0)
        new_unit = st.text_input("Unit (e.g., 'km')")
        
        if st.button("Add Goal"):
            if new_goal:
                if db.add_new_goal(new_goal, new_target, new_unit, new_cat):
                    st.success(f"Added {new_goal}!")
                    st.rerun()
                else:
                    st.error("Goal already exists!")

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["🔥 Daily Grind", "🥗 Mess Auditor"])

# === TAB 1: THE DASHBOARD ===
with tab1:
    # Fetch Data
    progress_data = db.get_todays_progress()
    
    # Organize data by Category
    categories = {}
    for cat, name, target, unit, current in progress_data:
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((name, target, unit, current))
    
    # Render Dashboard
    if not categories:
        st.info("No goals set yet. Use the sidebar to add one!")
    
    for category, goals in categories.items():
        st.subheader(f"{'🛡️' if category=='Athleticism' else '🚀'} {category}")
        
        # Grid Layout
        col1, col2 = st.columns(2)
        
        for i, (name, target, unit, current) in enumerate(goals):
            percent = min(current / target, 1.0)
            
            # Alternate columns
            with col1 if i % 2 == 0 else col2:
                # Card Styling
                with st.container(border=True):
                    st.write(f"**{name}**")
                    
                    # LOGIC: Boolean vs Numeric
                    if unit in ["bool", "session"]:
                        # It's a Checkbox Goal (Plyo, Eat Clean)
                        is_done = (current >= 1.0)
                        if is_done:
                            st.success("✅ COMPLETE")
                        else:
                            st.warning("⚠️ PENDING")
                        
                        if st.button(f"Mark Done" if not is_done else "Undo", key=f"btn_{name}"):
                            db.update_log(name, 1.0 if not is_done else 0.0)
                            st.rerun()
                    
                    else:
                        # It's a Numeric Goal (Pullups, DSA)
                        st.progress(percent)
                        
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            st.caption(f"{int(current)} / {int(target)} {unit}")
                        with c2:
                            # Direct Number Input
                            new_val = st.number_input("Log", value=float(current), step=1.0, 
                                                    key=f"num_{name}", label_visibility="collapsed")
                            if new_val != current:
                                db.update_log(name, new_val)
                                st.rerun()

# === TAB 2: THE MESS AUDITOR ===
with tab2:
    st.header("🥗 Mess Auditor")
    st.info("Log what the mess served vs. what you actually ate. I will audit this later.")
    
    # Food Input Form
    with st.form("food_form", clear_on_submit=True):
        meal_type = st.selectbox("Meal", ["Breakfast", "Lunch", "Snacks", "Dinner"])
        menu_desc = st.text_area("Mess Menu (What was available?)", 
                               placeholder="e.g., Chola Bhatura, Rice, Dal...")
        my_choice = st.text_area("My Plate (What did you eat?)", 
                               placeholder="e.g., Only Chola, no Bhatura. 2 Eggs.")
        
        submitted = st.form_submit_button("Submit Meal")
        if submitted:
            db.log_meal(meal_type, menu_desc, my_choice)
            st.success("Meal Logged!")
            st.rerun()

    st.divider()
    
    # Food History Display
    st.subheader("Today's Logs")
    food_logs = db.get_todays_food()
    
    if food_logs:
        for m_type, ate, menu in food_logs:
            with st.expander(f"{m_type}: {ate}"):
                st.write(f"**Menu was:** {menu}")
                st.write(f"**You ate:** {ate}")
    else:
        st.caption("No meals logged today yet.")