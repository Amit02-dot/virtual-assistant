import os
import json

MEMORY_DIR = "memory"
PREFERENCES_FILE = os.path.join(MEMORY_DIR, "preferences.json")
UPLOADS_DIR = os.path.join(MEMORY_DIR, "uploads")

os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

if not os.path.exists(PREFERENCES_FILE):
    with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def save_preference(key, value):
    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
        
    data[key] = value
    
    with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
def get_preferences_context():
    try:
        with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not data: return ""
            
            context = "User Preferences & Memory:\n"
            for k, v in data.items():
                context += f"- {k}: {v}\n"
            return context + "\n"
    except Exception:
        return ""

def get_rag_context():
    context = ""
    if os.path.exists(UPLOADS_DIR):
        for filename in os.listdir(UPLOADS_DIR):
            filepath = os.path.join(UPLOADS_DIR, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        # Basic chunking: if file is too large, we just take the first 5000 chars for safety
                        content = f.read()
                        if len(content) > 5000:
                            content = content[:5000] + "\n...[Content Truncated]..."
                        context += f"Document '{filename}':\n```\n{content}\n```\n\n"
                except Exception:
                    pass
    return context
