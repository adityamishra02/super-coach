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

    def get_working_model(self):
        """
        Auto-discovers a valid model for this API key.
        """
        try:
            # 1. Ask Google what is available
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            
            # 2. Sort them to prefer "Flash" or "Pro" (Faster/Cheaper)
            # We look for specific keywords and return the first match
            priority_order = ['flash', 'pro', 'gemini-1.5', 'gemini-1.0']
            
            for keyword in priority_order:
                for model_name in available_models:
                    if keyword in model_name and 'vision' not in model_name:
                        return model_name
            
            # 3. Fallback: Just take the first one found
            if available_models:
                return available_models[0]
                
            return None
        except Exception as e:
            return None

    def process_input(self, user_text):
        # --- LOGGING (Keep your existing logic) ---
        system_update = ""
        text_lower = user_text.lower()
        
        # [Paste your LOGGING logic here: Pullups, Food, Weight...]
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

        elif any(w in text_lower for w in ["ate", "drink", "eggs", "chicken", "meal"]):
            self.db.log_food(user_text)
            system_update = f"[System Note: I logged food entry: '{user_text}'.]"

        elif "weigh" in text_lower or "kg" in text_lower:
            numbers = re.findall(r'\d+\.?\d*', user_text)
            if numbers:
                val = float(numbers[0])
                self.db.log_metric("Weight", val)
                system_update = f"[System Note: I logged weight as {val}kg.]"

        # --- AI RESPONSE (Auto-Discovery Mode) ---
        try:
            context = self.db.get_progress()
        except:
            context = "No data yet."
            
        now = datetime.datetime.now().strftime("%H:%M")
        
        # FIND A MODEL
        model_name = self.get_working_model()
        if not model_name:
            return "⚠️ CRITICAL: No models available for this API Key. Please check Google AI Studio."
            
        # PROMPT
        prompt = f"""
        You are a discipline coach.
        CONTEXT: {now} | {context}
        SYSTEM UPDATE: {system_update}
        USER SAID: "{user_text}"
        """
        
        try:
            # Use the discovered model
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # We append the model name so you know which one worked
            return f"{response.text} \n\n*(Brain: {model_name})*"
        except Exception as e:
            return f"⚠️ Error with {model_name}: {e}"