import google.generativeai as genai
import streamlit as st
import time
import datetime
import re

class CoachBrain:
    def __init__(self, db):
        self.db = db
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
        except Exception as e:
            st.error(f"⚠️ API Key Error: {e}")

    def process_input(self, user_text):
        # --- LOGGING (Keep existing logic) ---
        system_update = ""
        text_lower = user_text.lower()
        
        # [Paste your LOGGING logic here: Pullups, Food, Weight...]
        if any(w in text_lower for w in ["pull up", "dip", "push up", "workout"]):
            # ... (Keep your regex logic)
            pass 

        # --- AI RESPONSE ---
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
        """
        
        # LIST OF MODELS TO TRY (Fallback Logic)
        models_to_try = ['gemini-1.5-flash', 'gemini-pro']
        
        last_error = ""
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                last_error = str(e)
                time.sleep(1)
                continue # Try next model
        
        # IF ALL FAIL, SHOW THE REAL ERROR
        return f"⚠️ DEBUG ERROR: {last_error}"