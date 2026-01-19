import os
from google import genai
import streamlit as st

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # Fallback for safety (or error message)
    st.error("❌ API Key missing! Set it in .streamlit/secrets.toml or Streamlit Cloud Secrets.")
    st.stop()

client = genai.Client(api_key=API_KEY)

class ContextMemory:
    def __init__(self, filename="user_profile.md"):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("# ADITYA'S PROFILE\n**Status:** Active\n")

    def get_context(self):
        with open(self.filename, "r") as f:
            return f.read()

    def update_profile(self, daily_logs, chat_summary):
        current_profile = self.get_context()
        
        prompt = f"""
        You are the Super Coach. Rewrite the student profile based on today's logs.
        OLD PROFILE: {current_profile}
        LOGS: {daily_logs}
        CHAT: {chat_summary}
        TASK: Update the profile (Markdown). Note weaknesses or consistency streaks.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-3-flash-preview',  # <--- UPDATED HERE
                contents=prompt
            )
            
            new_content = response.text.replace("```markdown", "").replace("```", "").strip()
            with open(self.filename, "w") as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"Memory Update Error: {e}")
            return False