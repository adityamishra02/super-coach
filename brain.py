import google.generativeai as genai
import streamlit as st
import time
import datetime

class CoachBrain:
    def __init__(self, db):
        self.db = db
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            st.error("⚠️ API Key missing.")
            return

        # Configure the STABLE library
        genai.configure(api_key=api_key)

    def process_input(self, user_text):
        # --- STEP 1: LOGGING (Same as before) ---
        system_update = ""
        text_lower = user_text.lower()
        
        # (Paste your existing logging logic here: Pullups, Food, Weight...)
        if "pull up" in text_lower or "dip" in text_lower:
             # ... your code ...
             pass 

        # --- STEP 2: AI RESPONSE (Stable Version) ---
        context = self.db.get_progress()
        now = datetime.datetime.now().strftime("%H:%M")
        
        prompt = f"""
        You are a discipline coach.
        CONTEXT: {now} | {context}
        SYSTEM UPDATE: {system_update}
        USER SAID: "{user_text}"
        """
        
        # RETRY LOOP
        model = genai.GenerativeModel('gemini-1.5-flash') # This name 100% works here
        
        for attempt in range(3):
            try:
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                time.sleep(2)
                continue
        
        return "⚠️ Coach is offline (Connection Error)."