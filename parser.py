import re

class SmartParser:
    def parse_command(self, text):
        text = text.lower()
        commands = []

        # --- LOGIC 1: WORKOUTS ---
        # Patterns: "15 pullups", "20 dips", "did 3 dsa questions"
        # Regex explanation: Look for a number (\d+) followed by a word
        workout_patterns = {
            "pullups": "Pullups",
            "pull ups": "Pullups",
            "dips": "Dips",
            "pushups": "Pushups",
            "dsa": "DSA Problems",
            "problems": "DSA Problems",
            "apps": "Job Apps"
        }

        for keyword, goal_name in workout_patterns.items():
            if keyword in text:
                # Find the number near the keyword
                match = re.search(r'(\d+)\s*' + keyword, text)
                if match:
                    val = float(match.group(1))
                    commands.append({"action": "log_metric", "goal": goal_name, "value": val})
                # Handle "did dsa" without number (assume 1)
                elif "did" in text and keyword in text:
                     commands.append({"action": "log_metric", "goal": goal_name, "value": 1})

        # --- LOGIC 2: MEALS ---
        # Patterns: "ate 2 eggs", "had salad"
        if "ate" in text or "had" in text or "mess" in text:
            # Everything after "ate/had" is considered the food
            # This is a simple heuristic
            food_match = re.search(r'(ate|had|consumed)\s+(.*)', text)
            if food_match:
                food_item = food_match.group(2)
                commands.append({
                    "action": "log_food", 
                    "meal": "Snack/Meal", # Generic meal type for quick logs
                    "desc": "Quick Log", 
                    "item": food_item
                })

        # --- LOGIC 3: BOOLEANS ---
        if "plyo" in text and ("done" in text or "did" in text):
             commands.append({"action": "log_metric", "goal": "Plyometrics", "value": 1.0})

        return commands