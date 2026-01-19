import time
from google import genai
from google.genai import types
import streamlit as st

class CoachBrain:
    def __init__(self, db):
        self.db = db
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except:
            api_key = None
            
        if not api_key:
            st.error("⚠️ API Key missing. Please check secrets.")
            
        self.client = genai.Client(api_key=api_key)

    def process_input(self, user_text):
        # --- STEP 1: TOOL EXECUTION (The "Hands") ---
        # (Your logging logic remains exactly the same here)
        system_update = ""
        text_lower = user_text.lower()
        
        # ... [Keep your existing logging logic for 'pull up', 'ate', 'weigh' etc.] ...
        # (I am omitting the logging block to keep this snippet clean, paste your logic back here)
        
        # --- STEP 2: HYBRID AI GENERATION (The "Voice") ---
        context = self.db.get_progress()
        import datetime
        now = datetime.datetime.now().strftime("%H:%M")
        
        prompt = f"""
        You are a high-performance discipline coach.
        CONTEXT: Time: {now} | Stats: {context}
        SYSTEM UPDATE: {system_update}
        USER SAID: "{user_text}"
        
        GOAL: Reply naturally. Short, punchy, like a trainer.
        """
        
        # === THE HYBRID ENGINE ===
        # Priority 1: Try the Smart/New Model (Gemini 2.0)
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', 
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            # If 2.0 fails (Limit 0, Overloaded, etc.), we catch it silently.
            # print(f"Gemini 2.0 failed: {e}") # Uncomment for debugging
            
            # Priority 2: Fallback to the Workhorse (Gemini 1.5)
            try:
                response = self.client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
                return response.text + " (v1.5)" # Optional: Mark it so you know which one replied
            except Exception as e2:
                return f"⚠️ System Failure: Both brains are down. {e2}"