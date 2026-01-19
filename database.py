import sqlite3
import datetime

class CoachDB:
    def __init__(self, db_name="super_coach.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        # 1. GOALS
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS goals
                             (name TEXT PRIMARY KEY, target REAL, unit TEXT, category TEXT)''')
        
        # 2. DAILY LOGS
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS daily_entries
                             (date TEXT, goal_name TEXT, value REAL, rpe INTEGER, 
                              PRIMARY KEY (date, goal_name))''')

        # 3. FOOD LOGS
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS food_logs
                             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                              date TEXT, time TEXT, content TEXT)''')
        
        # 4. CHAT HISTORY
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history
                             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                              timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                              sender TEXT, message TEXT)''')

        # 5. SCHEDULE
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS schedule
                             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                              date TEXT, 
                              time_slot TEXT, 
                              task TEXT, 
                              status TEXT)''')

        # Seed Defaults
        self.cursor.execute("SELECT count(*) FROM goals")
        if self.cursor.fetchone()[0] == 0:
            defaults = [
                ("Pullups", 15, "reps", "Athleticism"),
                ("Dips", 20, "reps", "Athleticism"),
                ("DSA", 3, "problems", "Career"),
                ("Job Apps", 5, "apps", "Career"),
                ("Sleep", 8, "hours", "Recovery")
            ]
            self.cursor.executemany("INSERT INTO goals VALUES (?,?,?,?)", defaults)
            self.conn.commit()

    # --- METHODS ---
    def create_schedule(self, tasks):
        today = datetime.date.today().isoformat()
        self.cursor.execute("DELETE FROM schedule WHERE date = ?", (today,))
        for time_slot, task in tasks:
            self.cursor.execute("INSERT INTO schedule (date, time_slot, task, status) VALUES (?,?,?,?)", 
                                (today, time_slot, task, "PENDING"))
        self.conn.commit()

    def get_current_mission(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute("SELECT id, time_slot, task FROM schedule WHERE date = ? AND status = 'PENDING' ORDER BY time_slot ASC LIMIT 1", (today,))
        return self.cursor.fetchone()

    def mark_mission_done(self, task_id):
        self.cursor.execute("UPDATE schedule SET status = 'DONE' WHERE id = ?", (task_id,))
        self.conn.commit()
        
    def get_full_schedule(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute("SELECT time_slot, task, status FROM schedule WHERE date = ? ORDER BY time_slot ASC", (today,))
        return self.cursor.fetchall()

    def log_metric(self, name, value, rpe=None):
        today = datetime.date.today().isoformat()
        self.cursor.execute("INSERT OR REPLACE INTO daily_entries (date, goal_name, value, rpe) VALUES (?,?,?,?)", 
                            (today, name, value, rpe))
        self.conn.commit()

    def log_food(self, content):
        today = datetime.date.today().isoformat()
        now = datetime.datetime.now().strftime("%H:%M")
        self.cursor.execute("INSERT INTO food_logs (date, time, content) VALUES (?,?,?)", (today, now, content))
        self.conn.commit()

    def log_chat(self, sender, message):
        self.cursor.execute("INSERT INTO chat_history (sender, message) VALUES (?,?)", (sender, message))
        self.conn.commit()
        
    def get_chat_history(self, limit=50):
        self.cursor.execute("SELECT sender, message FROM chat_history ORDER BY id DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()[::-1]

    def get_progress(self):
        today = datetime.date.today().isoformat()
        query = '''
            SELECT g.name, g.target, g.unit, COALESCE(d.value, 0), d.rpe
            FROM goals g
            LEFT JOIN daily_entries d ON g.name = d.goal_name AND d.date = ?
        '''
        self.cursor.execute(query, (today,))
        return self.cursor.fetchall()
    
    def get_metric_history(self, goal_name):
        # Returns [('2023-10-01', 12), ('2023-10-02', 13)...]
        self.cursor.execute('''SELECT date, value FROM daily_entries 
                             WHERE goal_name = ? ORDER BY date ASC''', (goal_name,))
        return self.cursor.fetchall()

    def get_all_goal_names(self):
        # Returns list of all goals ever logged or tracked
        self.cursor.execute("SELECT DISTINCT name FROM goals")
        return [row[0] for row in self.cursor.fetchall()]

    def get_consistency_data(self):
        # Returns count of tasks completed per day: [('2023-10-01', 5), ...]
        self.cursor.execute('''SELECT date, COUNT(*) FROM daily_entries 
                             GROUP BY date ORDER BY date ASC''')
        return self.cursor.fetchall()