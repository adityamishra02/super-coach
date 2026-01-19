import sqlite3
import datetime

class SuperCoachDB:
    def __init__(self, db_name="coach_memory.db"):
        # check_same_thread=False is needed for Streamlit
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        # 1. GOALS TABLE (With Category)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS goals
                             (name TEXT PRIMARY KEY, target REAL, unit TEXT, category TEXT)''')
        
        # 2. DAILY LOGS TABLE
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS daily_entries
                             (date TEXT, goal_name TEXT, value REAL, 
                              PRIMARY KEY (date, goal_name))''')

        # 3. FOOD LOGS TABLE (Mess Auditor)
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS food_logs
                             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                              date TEXT, 
                              meal_type TEXT, 
                              menu_description TEXT,
                              what_i_ate TEXT)''')
        
        # SEED DEFAULT GOALS (Only if table is empty)
        self.cursor.execute("SELECT count(*) FROM goals")
        if self.cursor.fetchone()[0] == 0:
            defaults = [
                # ATHLETICISM
                ("Pullups", 15, "reps", "Athleticism"),
                ("Dips", 20, "reps", "Athleticism"),
                ("Plyometrics", 1, "session", "Athleticism"), # 1 = Done
                ("Clean Eating", 1, "bool", "Athleticism"),   # 1 = Clean
                
                # CAREER
                ("DSA Problems", 3, "q's", "Career"),
                ("Job Apps", 5, "apps", "Career"),
                ("Deep Work", 4, "hours", "Career")
            ]
            self.cursor.executemany("INSERT INTO goals VALUES (?,?,?,?)", defaults)
            self.conn.commit()

    # --- GOAL TRACKING METHODS ---
    def get_todays_progress(self):
        today = datetime.date.today().isoformat()
        # Returns: (category, name, target, unit, current_value)
        query = '''
            SELECT g.category, g.name, g.target, g.unit, COALESCE(d.value, 0) as current
            FROM goals g
            LEFT JOIN daily_entries d ON g.name = d.goal_name AND d.date = ?
            ORDER BY g.category DESC, g.name ASC
        '''
        self.cursor.execute(query, (today,))
        return self.cursor.fetchall()

    def update_log(self, goal_name, value):
        today = datetime.date.today().isoformat()
        self.cursor.execute("INSERT OR REPLACE INTO daily_entries VALUES (?,?,?)", 
                            (today, goal_name, value))
        self.conn.commit()

    def add_new_goal(self, name, target, unit, category):
        try:
            self.cursor.execute("INSERT INTO goals VALUES (?,?,?,?)", (name, target, unit, category))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    # --- MESS AUDITOR METHODS ---
    def log_meal(self, meal_type, menu, ate):
        today = datetime.date.today().isoformat()
        self.cursor.execute("INSERT INTO food_logs (date, meal_type, menu_description, what_i_ate) VALUES (?,?,?,?)", 
                            (today, meal_type, menu, ate))
        self.conn.commit()

    def get_todays_food(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute("SELECT meal_type, what_i_ate, menu_description FROM food_logs WHERE date = ?", (today,))
        return self.cursor.fetchall()