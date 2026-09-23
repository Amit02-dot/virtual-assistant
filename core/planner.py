import json

def generate_plan(user_request, gemini_client, model="gemini-3.6-flash"):
    system_prompt = """You are the Task Planning core of JARVIS. 
Your job is to break down the user's complex request into a sequential list of atomic, executable actions.
You must output ONLY a valid JSON array of action objects. Do NOT include markdown blocks, backticks, or any other text.
Available actions:
1. {"action": "open_app", "target": "app_name"}
2. {"action": "open_website", "target": "url_or_site_name"}
3. {"action": "run_terminal_command", "target": "command_string"}
4. {"action": "close_app", "target": "app_name"}

Example Request: "Prepare my coding environment"
Example Output:
[
    {"action": "open_app", "target": "vs code"},
    {"action": "open_website", "target": "github"},
    {"action": "run_terminal_command", "target": "echo Environment ready"}
]
"""
    try:
        response = gemini_client.chats.create(model="gemini-3.6-flash").send_message(f"{system_prompt}\n\nUser Request: {user_request}")
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split('\n')
            if len(lines) > 1:
                text = '\n'.join(lines[1:])
        if text.endswith("```"):
            text = '\n'.join(text.split('\n')[:-1])
        
        plan_json = json.loads(text.strip())
        return plan_json
    except Exception as e:
        print(f"Planner Error: {e}")
        return None

def format_plan_for_speech(plan_json):
    if not plan_json or not isinstance(plan_json, list):
        return "I could not generate a valid plan for this request."
    
    summary = f"I have prepared a plan with {len(plan_json)} steps. "
    for i, step in enumerate(plan_json):
        action = step.get("action", "")
        target = step.get("target", "")
        
        if action == "open_app":
            summary += f"Step {i+1}: Open {target}. "
        elif action == "open_website":
            summary += f"Step {i+1}: Open website {target}. "
        elif action == "run_terminal_command":
            summary += f"Step {i+1}: Run command {target}. "
        elif action == "close_app":
            summary += f"Step {i+1}: Close {target}. "
        else:
            summary += f"Step {i+1}: Perform {action} on {target}. "
            
    summary += "Do you approve this plan? Say yes to proceed, or no to cancel."
    return summary
