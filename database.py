import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pandas as pd

class CoachDB:
    def __init__(self):
        # Authenticate using Streamlit Secrets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # We create a credentials dict from the secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Fix private key formatting if necessary
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        self.client = gspread.authorize(creds)
        
        # Open the Sheet
        try:
            self.sheet = self.client.open("super_coach_db")
        except:
            st.error("❌ Could not find 'super_coach_db' in Google Sheets. Did you share it with the service account email?")
            st.stop()

        # Connect to Tabs
        self.ws_goals = self.sheet.worksheet("goals")
        self.ws_entries = self.sheet.worksheet("daily_entries")
        self.ws_food = self.sheet.worksheet("food_logs")
        self.ws_chat = self.sheet.worksheet("chat_history")
        self.ws_schedule = self.sheet.worksheet("schedule")

    # --- SCHEDULE METHODS ---
    def create_schedule(self, tasks):
        # tasks = [("08:00", "Wake Up"), ...]
        today = datetime.date.today().isoformat()
        
        # 1. Get all records
        all_rows = self.ws_schedule.get_all_records()
        
        # 2. Delete old rows for today (This is slow in Sheets, so we just append and filter later, 
        #    OR we clear the sheet if you only care about today. Let's append but mark old as 'ARCHIVED'?)
        #    Actually, simplest for a personal app: Clear the schedule tab daily or keep history?
        #    Let's KEEP history but only fetch today's.
        
        # Prepare rows
        new_rows = []
        for time_slot, task in tasks:
            new_rows.append([today, time_slot, task, "PENDING"])
            
        self.ws_schedule.append_rows(new_rows)

    def get_current_mission(self):
        today = datetime.date.today().isoformat()
        records = self.ws_schedule.get_all_records()
        
        # Filter for Today + Pending
        # We assume the records are dictionaries: {'date': '...', 'status': '...'}
        for i, row in enumerate(records):
            if str(row['date']) == today and row['status'] == "PENDING":
                # Return (row_index_in_sheet, time, task)
                # Sheet rows start at 2 (1 is header). i is 0-indexed from records.
                # So actual row number is i + 2
                return (i + 2, row['time_slot'], row['task'])
        return None

    def mark_mission_done(self, row_id):
        # Update column D (Status) to DONE
        self.ws_schedule.update_cell(row_id, 4, "DONE")
        
    def get_full_schedule(self):
        today = datetime.date.today().isoformat()
        records = self.ws_schedule.get_all_records()
        
        # Filter for today
        todays_plan = []
        for row in records:
            if str(row['date']) == today:
                todays_plan.append((row['time_slot'], row['task'], row['status']))
        
        # Sort by time
        todays_plan.sort(key=lambda x: x[0])
        return todays_plan

    # --- LOGGING METHODS ---
    def log_metric(self, name, value, rpe=None):
        today = datetime.date.today().isoformat()
        # Append row: date, goal_name, value, rpe
        self.ws_entries.append_row([today, name, value, rpe if rpe else ""])

    def log_food(self, content):
        today = datetime.date.today().isoformat()
        now = datetime.datetime.now().strftime("%H:%M")
        self.ws_food.append_row([today, now, content])

    def log_chat(self, sender, message):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ws_chat.append_row([now, sender, message])
        
    def get_chat_history(self, limit=20):
        # Get all values
        all_values = self.ws_chat.get_all_values()
        # Skip header, get last 'limit' rows
        if len(all_values) < 2: return []
        
        data = all_values[1:] # Remove header
        recent = data[-limit:] # Last N
        
        # Format: [(sender, msg), ...]
        return [(r[1], r[2]) for r in recent]

    def get_progress(self):
        today = datetime.date.today().isoformat()
        
        # 1. Get Goals
        goals = self.ws_goals.get_all_records()
        
        # 2. Get Today's Entries
        entries = self.ws_entries.get_all_records()
        
        # --- DEBUG PRINT (This will show up in your terminal logs) ---
        if entries:
            print(f"DEBUG: Found keys in first row: {entries[0].keys()}")
        # ------------------------------------------------------------

        # 3. Aggregate
        progress = []
        for g in goals:
            g_name = g['name']
            total = 0
            last_rpe = None
            
            for e in entries:
                # Normalize keys: strip spaces and lowercase them just for checking
                # (This fixes 'Value', 'value ', 'Goal Name', etc.)
                row = {k.lower().strip(): v for k, v in e.items()}
                
                # Check date
                row_date = str(row.get('date', ''))
                row_goal = row.get('goal_name', '')
                
                if row_date == today and row_goal == g_name:
                    try:
                        # Safer fetch: defaults to 0 if empty or missing
                        val = row.get('value', 0)
                        total += float(val) if val != "" else 0.0
                        
                        if row.get('rpe'): 
                            last_rpe = row.get('rpe')
                    except ValueError:
                        continue # Skip bad numbers
            
            progress.append((g_name, g['target'], g['unit'], total, last_rpe))
            
        return progress

    # --- DASHBOARD METHODS ---
    def get_metric_history(self, goal_name):
        records = self.ws_entries.get_all_records()
        # Filter
        data = []
        for r in records:
            if r['goal_name'] == goal_name:
                data.append((r['date'], float(r['value'])))
        return data

    def get_all_goal_names(self):
        goals = self.ws_goals.get_all_records()
        return [g['name'] for g in goals]

    def get_consistency_data(self):
        records = self.ws_entries.get_all_records()
        # Count entries per date
        counts = {}
        for r in records:
            d = r['date']
            counts[d] = counts.get(d, 0) + 1
        return list(counts.items())
    
    def is_weight_logged_today(self):
        """Checks if 'Weight' has been logged for the current date."""
        today = datetime.date.today().isoformat()
        try:
            # efficient way: get all records and check in python
            entries = self.ws_entries.get_all_records()
            for e in entries:
                if str(e['date']) == today and e['goal_name'] == "Weight":
                    return True
        except:
            return False # Safety fallback
        return False

    def get_raw_history(self):
        """Returns all log entries for the history page."""
        return self.ws_entries.get_all_records()