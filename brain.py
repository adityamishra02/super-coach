import google.generativeai as genai
import streamlit as st
import time
import datetime
import pytz # <--- NEW: For India Time
import re

class CoachBrain:
    def __init__(self, db):
        self.db = db
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
            genai.configure(api_key=api_key)
        except Exception as e:
            st.error(f"⚠️ API Key Error: {e}")

    def get_ist_time(self):
        """Returns current time in India."""
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))
        return ist_now

    def get_working_model(self):
        # (Keep your existing auto-discovery code from the previous step)
        try:
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            priority_order = ['flash', 'pro', 'gemini-1.5', 'gemini-1.0']
            for keyword in priority_order:
                for model_name in available_models:
                    if keyword in model_name and 'vision' not in model_name:
                        return model_name
            if available_models: return available_models[0]
            return None
        except: return None

    def process_input(self, user_text):
        system_update = ""
        text_lower = user_text.lower()
        
        # --- 1. LOGGING (Keep existing) ---
        if any(w in text_lower for w in ["pull up", "dip", "push up", "workout"]):
            numbers = re.findall(r'\d+', user_text)
            if numbers:
                val = float(numbers[0])
                metric = "Pullups" if "pull" in text_lower else "Dips" if "dip" in text_lower else "Workout"
                self.db.log_metric(metric, val)
                system_update = f"[Logged {val} {metric}]"

        elif "weigh" in text_lower or "kg" in text_lower:
            numbers = re.findall(r'\d+\.?\d*', user_text)
            if numbers:
                val = float(numbers[0])
                self.db.log_metric("Weight", val)
                system_update = f"[Logged {val}kg]"

        # --- 2. PLANNING AGENT (NEW!) ---
        # If user asks to "plan", we generate AND save.
        elif "plan" in text_lower or "schedule" in text_lower:
            
            # A. Get the AI to generate a strict format
            ist_now = self.get_ist_time().strftime("%H:%M")
            prompt = f"""
            You are a Scheduler. The user wants a plan for tomorrow/today.
            Current Time (IST): {ist_now}.
            
            TASK: Create a realistic schedule based on the user's request: "{user_text}".
            
            CRITICAL OUTPUT FORMAT:
            You MUST output the plan EXACTLY like this (pipe separated):
            08:00|Wake Up
            09:00|Deep Work
            18:00|Gym
            
            Do not add conversational filler. Just the list.
            """
            
            model_name = self.get_working_model()
            if not model_name: return "⚠️ API Error: No model found."
            
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            raw_plan = response.text
            
            # B. Parse the AI's output
            new_schedule = []
            lines = raw_plan.strip().split('\n')
            for line in lines:
                if "|" in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        time_slot = parts[0].strip()
                        task = parts[1].strip()
                        new_schedule.append((time_slot, task))
            
            # C. Save to Database
            if new_schedule:
                self.db.create_schedule(new_schedule)
                return f"✅ **Plan Saved to Database!** check the sidebar.\n\n" + raw_plan
            else:
                return "⚠️ I tried to plan, but I couldn't format it correctly. Try again?"

        # --- 3. STANDARD CHAT (Fallback) ---
        # ... (Rest of your code remains the same)
        try:
            context = self.db.get_progress()
        except: context = "No data."
            
        ist_now = self.get_ist_time().strftime("%H:%M") # Use IST here too!
        
        prompt = f"""
        You are a discipline coach.
        CONTEXT: Time (IST): {ist_now} | Stats: {context}
        SYSTEM UPDATE: {system_update}
        USER SAID: "{user_text}"
        """
        
        # (Use your existing fallback logic here for generate_content)
        model_name = self.get_working_model()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text