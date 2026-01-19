import json
import datetime
from google import genai
import streamlit as st

class CoachBrain:
    def __init__(self, db):
        self.db = db
        # Use the secret key
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            api_key = "ERR_NO_KEY"
            
        self.client = genai.Client(api_key=api_key)

    def process_input(self, user_text):
        """
        1. Analyzes intent.
        2. Executes tool (Database Log).
        3. Generates AI response (Personality).
        """
        
        # --- STEP 1: TOOL EXECUTION (The "Hands") ---
        # We check keywords to do the work, but we DON'T return text yet.
        system_update = ""
        
        text_lower = user_text.lower()
        
        # LOGGING WORKOUTS
        if "pull up" in text_lower or "dip" in text_lower or "push up" in text_lower:
            # Simple number extraction (improved)
            import re
            numbers = re.findall(r'\d+', user_text)
            if numbers:
                val = float(numbers[0])
                # Guess the exercise type
                if "pull" in text_lower: metric = "Pullups"
                elif "dip" in text_lower: metric = "Dips"
                elif "push" in text_lower: metric = "Pushups"
                else: metric = "Workout"
                
                self.db.log_metric(metric, val)
                system_update = f"[System Note: I have successfully logged {val} {metric} into the database.]"

        # LOGGING FOOD
        elif "ate" in text_lower or "drink" in text_lower or "eggs" in text_lower:
            self.db.log_food(user_text)
            system_update = f"[System Note: I have logged this food entry: '{user_text}' into the 'food_logs' tab.]"
            
        # LOGGING WEIGHT
        elif "weigh" in text_lower or "kg" in text_lower:
            import re
            numbers = re.findall(r'\d+\.?\d*', user_text)
            if numbers:
                val = float(numbers[0])
                self.db.log_metric("Weight", val)
                system_update = f"[System Note: I logged their weight as {val}kg.]"

        # --- STEP 2: AI GENERATION (The "Voice") ---
        # Now we send the User's text + Our System Note to Gemini
        
        context = self.db.get_progress() # Get stats for context
        now = datetime.datetime.now().strftime("%H:%M")
        
        prompt = f"""
        You are a high-performance discipline coach.
        
        CONTEXT:
        - Time: {now}
        - Recent Stats: {context}
        - SYSTEM UPDATE: {system_update} (This is what you just did in the backend)
        
        USER SAID: "{user_text}"
        
        YOUR GOAL:
        Reply to the user naturally. 
        - If the System Update says you logged something, confirm it casually (e.g., "Got it, 7 eggs logged. That's good protein.").
        - Do NOT say "System Note" or "I have logged". Be human.
        - If the user asks a question (like "Where did you log it?"), answer truthfully based on the System Update.
        - Keep it short (1-2 sentences).
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash', # Or gemini-1.5-flash
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"⚠️ Brain Freeze: {e}"