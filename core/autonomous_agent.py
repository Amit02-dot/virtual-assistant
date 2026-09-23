import time
import json
import threading
from tools.browser_agent import BrowserAgent

class AutonomousAgent:
    def __init__(self, gemini_client, speak_func):
        self.gemini_client = gemini_client
        self.speak = speak_func
        self.browser = BrowserAgent()
        self.state = "IDLE" # IDLE, EXECUTING, WAITING_FOR_USER, PAUSED, COMPLETED, CANCELLED
        self.goal = ""
        self.history = []
        self.execution_thread = None

    def is_running(self):
        return self.state in ["EXECUTING", "WAITING_FOR_USER", "PAUSED"]

    def cancel(self):
        self.state = "CANCELLED"
        self.speak("Autonomous task cancelled.")

    def pause(self):
        if self.state == "EXECUTING":
            self.state = "PAUSED"
            self.speak("Task paused.")

    def resume(self):
        if self.state == "PAUSED" or self.state == "WAITING_FOR_USER":
            self.state = "EXECUTING"
            self.speak("Resuming autonomous task.")

    def start_task(self, goal):
        if self.is_running():
            self.speak("An autonomous task is already running.")
            return

        self.goal = goal
        self.history = []
        self.state = "EXECUTING"
        self.speak("Starting autonomous task. I will begin execution now.")
        
        self.execution_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.execution_thread.start()

    def _get_next_action(self):
        # Build prompt
        system_prompt = f"""You are JARVIS, an autonomous browser and computer agent.
Your overarching goal is: {self.goal}

You are in a ReAct loop. Based on the current state, what is the next step?
Return ONLY a valid JSON object with the following fields:
- "thought": A brief explanation of your reasoning.
- "action": The action to perform. Valid actions: "navigate", "click", "type", "wait_for_user", "complete", "read"
- "target": The URL (for navigate) or CSS Selector (for click/type).
- "value": The text to type (if action is "type").
- "speak": A natural, conversational spoken update to give the user (e.g., "LeetCode is open.", "I'm testing the solution."). Leave empty if no major milestone is reached.

Browser State:
Current URL: {self.browser.get_url()}
Page Text Summary (First 10000 chars): {self.browser.get_page_summary()}

Recent History:
{json.dumps(self.history[-5:], indent=2)}
"""
        
        try:
            response = self.gemini_client.chats.create(model="gemini-3.6-flash").send_message(system_prompt)
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            return json.loads(text.strip())
        except Exception as e:
            print(f"Agent Loop Error: {e}")
            return {"action": "error", "thought": str(e)}

    def _run_loop(self):
        while self.state == "EXECUTING":
            action_data = self._get_next_action()
            action = action_data.get("action", "")
            thought = action_data.get("thought", "")
            target = action_data.get("target", "")
            value = action_data.get("value", "")
            speak_text = action_data.get("speak", "")

            print(f"[AGENT] Thought: {thought}")
            print(f"[AGENT] Action: {action} on {target}")

            if speak_text:
                self.speak(speak_text)

            success = False
            if action == "navigate":
                success = self.browser.navigate(target)
            elif action == "click":
                success = self.browser.click(target)
            elif action == "type":
                success = self.browser.type_text(target, value)
            elif action == "read":
                success = True
            elif action == "wait_for_user":
                self.state = "WAITING_FOR_USER"
                self.speak("I need your input to continue. Please tell me to resume when you are ready.")
                while self.state == "WAITING_FOR_USER":
                    time.sleep(1)
                continue
            elif action == "complete":
                self.state = "COMPLETED"
                self.speak("Autonomous task completed.")
                self.browser.stop()
                break
            else:
                success = False
                print(f"[AGENT] Unknown action: {action}")

            self.history.append({
                "action": action,
                "target": target,
                "value": value,
                "success": success
            })
            
            # Rate limit the loop
            time.sleep(2)
            
        if self.state == "CANCELLED":
            self.browser.stop()
