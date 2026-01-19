import google.generativeai as genai
import streamlit as st
import time
import datetime
import re

class CoachBrain:
    def __init__(self, db):
        self.db = db
        try:
            # Get API Key
            api_key = st.secrets["GEMINI_API_KEY"]
            # Configure the STABLE library
            genai.configure(api_key=api_key)
        except Exception as e:
            st.error(f"⚠️ API Key Error: {e}")

    def process_input(self, user_text):
        # --- STEP 1: LOGGING (The "Hands") ---
        system_update = ""
        text_lower = user_text.lower()
        
        # 1. WORKOUT LOGGING
        if any(w in text_lower for w in ["pull up", "dip", "push up", "workout"]):
            numbers = re.findall(r'\d+', user_text)
            if numbers:
                val = float(numbers[0])
                if "pull" in text_lower: metric = "Pullups"
                elif "dip" in text_lower: metric = "Dips"
                elif "push" in text_lower: metric = "Pushups"
                else: metric = "Workout"
                
                self.db.log_metric(metric, val)
                system_update = f"[System Note: I logged {val} {metric}.]"

        # 2. FOOD LOGGING
        elif any(w in text_lower for w in ["ate", "drink", "eggs", "chicken", "meal"]):
            self.db.log_food(user_text)
            system_update = f"[System Note: I logged food entry: '{user_text}'.]"
            
        # 3. WEIGHT LOGGING
        elif "weigh" in text_lower or "kg" in text_lower:
            numbers = re.findall(r'\d+\.?\d*', user_text)
            if numbers:
                val = float(numbers[0])
                self.db.log_metric("Weight", val)
                system_update = f"[System Note: I logged weight as {val}kg.]"

        # --- STEP 2: AI RESPONSE (The "Voice") ---
        # Get context
        try:
            context = self.db.get_progress()
        except:
            context = "No data yet."
            
        now = datetime.datetime.now().strftime("%H:%M")
        
        prompt = f"""
        You are a discipline coach.
        CONTEXT: {now} | {context}
        SYSTEM UPDATE: {system_update}
        USER SAID: "{user_text}"
        
        GOAL: Reply naturally to the user. If you see a SYSTEM UPDATE, confirm it briefly.
        """
        
        # USE THE STABLE MODEL
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Retry Logic for Robustness
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                time.sleep(1) # Wait 1 second before retrying
                continue
        
        return "⚠️ Signal Lost. I logged the data, but cannot reply right now."