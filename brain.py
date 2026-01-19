import datetime
import re
from ai_planner import AIPlanner
from memory import ContextMemory

class CoachBrain:
    def __init__(self, db):
        self.db = db
        self.planner = AIPlanner()
        self.memory = ContextMemory()

    def process_input(self, user_text):
        text = user_text.lower()
        response = ""
        
        # --- 1. PLAN DAY (Uses Memory) ---
        if "plan" in text:
            # Get data
            goals = self.db.get_progress()
            profile = self.memory.get_context() # <--- Reads the text file
            
            response = "🧠 **Consulting your Profile & Generating Orders...**"
            
            # Generate
            schedule = self.planner.generate_schedule(user_text, goals, profile)
            
            if schedule and schedule[0][0] != "Error":
                self.db.create_schedule(schedule)
                response = "**📅 PLAN LOCKED.**\nI have tailored this based on your profile history. Check sidebar."
            else:
                response = "❌ AI Error. Check API Key."

        # --- 2. REVIEW DAY (Updates Memory) ---
        elif "review day" in text or "end day" in text:
            # Gather data
            logs = self.db.get_progress() # What you did
            history = self.db.get_chat_history(10) # What you said
            
            response = "💾 **Analyzing performance... Updating Profile...**"
            
            # Update the text file
            success = self.memory.update_profile(str(logs), str(history))
            
            if success:
                response = "**✅ Profile Updated.**\nI have noted your performance. I will use this to adjust tomorrow's plan.\n*Go to sleep.*"
            else:
                response = "❌ Failed to update memory."

        # --- 3. STATUS / DONE (Standard) ---
        elif "status" in text or "next" in text:
            mission = self.db.get_current_mission()
            if mission:
                _, time, task = mission
                response = f"**🎯 CURRENT MISSION ({time})**\n{task}"
            else:
                response = "No active missions."

        elif "done" in text:
            mission = self.db.get_current_mission()
            if mission:
                self.db.mark_mission_done(mission[0])
                response = "✅ **Task Complete.** Type 'Status' for next."
            else:
                response = "No task to complete."

        # --- 4. LOGGING (Standard) ---
        elif any(k in text for k in ["did", "ate", "swam", "solved"]):
            # (Simplified logging logic for brevity - paste your previous Regex here if needed)
            # For now, just a pass-through to show it works
            response = self._handle_logging(text)

        else:
            response = "Commands: **'Plan my day'**, **'Review day'**, **'Done'**, or **'Did 15 pullups'**."

        return response

    def _handle_logging(self, text):
        # ... (Reuse the Regex logging logic from previous code) ...
        # For simplicity in this snippet:
        return "📝 Logged activity. (Remember to 'Review Day' tonight!)"