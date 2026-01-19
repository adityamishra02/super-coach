from google import genai
import json
import datetime
import streamlit as st

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # Fallback for safety (or error message)
    st.error("❌ API Key missing! Set it in .streamlit/secrets.toml or Streamlit Cloud Secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)

class AIPlanner:
    def generate_schedule(self, user_request, db_goals, user_profile):
        now = datetime.datetime.now().strftime("%H:%M")
        
        prompt = f"""
        You are a strict discipline coach.
        USER PROFILE: {user_profile}
        CURRENT STATUS: Time: {now}, Goals: {db_goals}
        REQUEST: "{user_request}"
        TASK: Create a strict JSON schedule.
        OUTPUT FORMAT: JSON only. Example: [["09:00", "DSA"], ["10:00", "Class"]]
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',  # <--- UPDATED HERE
                contents=prompt
            )
            
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"AI Planning Error: {e}")
            return [("Error", f"AI Failed: {e}")]