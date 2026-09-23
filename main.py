import speech_recognition as sr
import subprocess
import pyttsx3
import musicLibrary
import requests
from google import genai
from gtts import gTTS
import pygame
import os
import sys
import pyautogui
import psutil
import ctypes
import datetime
import socket
import shutil

# JARVIS 2.0 Core Modules
from core.security import request_permission, RiskLevel, request_plan_approval
import core.memory as jarvis_memory
import core.planner as planner
from core.autonomous_agent import AutonomousAgent
import tools.system_tools as sys_tools
import gui.dashboard as dashboard

# Volume control imports (Windows)
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Brightness control
import screen_brightness_control as sbc

# pip install pocketsphinx pyautogui psutil pycaw screen-brightness-control google-genai

recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapi = "33e83ddfe2b646c6a4e3cb9f93ae3eaa"

# Disable pyautogui fail-safe (mouse to corner won't crash)
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.3

CODING_MODE = False

def listen_for_confirmation():
    """Helper for security confirmation."""
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            return recognizer.recognize_google(audio, language="en-IN")
        except Exception:
            return ""

# ─────────────────────────────────────────────
#  SPEECH
# ─────────────────────────────────────────────
def speak(text):
    import time
    import random
    from gtts import gTTS
    
    print(f"Jarvis: {text}")
    filename = f"temp_{int(time.time())}_{random.randint(1000, 9999)}.mp3"
    
    try:
        tts = gTTS(text)
        tts.save(filename)
    
        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
    
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        try:
            pygame.mixer.quit()
            import time
            time.sleep(0.1)
            for _ in range(3):
                try:
                    if os.path.exists(filename):
                        os.remove(filename)
                    break
                except Exception:
                    time.sleep(0.2)
        except Exception:
            pass



# ─────────────────────────────────────────────
#  AI PROCESSING (Google Gemini - FREE)
# ─────────────────────────────────────────────
gemini_client = genai.Client(api_key="YOUR_API_KEY_HERE")
autonomous_agent = AutonomousAgent(gemini_client, speak)

CHAT_HISTORY = []

def aiProcess(command):
    global CHAT_HISTORY
    
    rag_context = jarvis_memory.get_rag_context()
    pref_context = jarvis_memory.get_preferences_context()
    
    system_prompt = "You are a virtual assistant named Jarvis skilled in general tasks like Alexa and Google Cloud. Give short responses please.\n"
    if pref_context:
        system_prompt += "\n" + pref_context
    if rag_context:
        system_prompt += "\nUse the following files as context to answer their questions:\n" + rag_context
        
    CHAT_HISTORY.append(f"User: {command}")
    
    if len(CHAT_HISTORY) > 6:
        CHAT_HISTORY = CHAT_HISTORY[-6:]
        
    history_str = "\n".join(CHAT_HISTORY)
    
    try:
        import time
        response = None
        for attempt in range(3):
            try:
                response = gemini_client.chats.create(model="gemini-3.6-flash").send_message(f"{system_prompt}\n\nConversation History:\n{history_str}\n\nJarvis:")
                break
            except Exception as api_e:
                if "503" in str(api_e) and attempt < 2:
                    time.sleep(2)
                    continue
                raise api_e
                
        CHAT_HISTORY.append(f"Jarvis: {response.text}")
        return response.text
    except Exception as e:
        print(f"AI Process Error: {e}")
        return "I am sorry, I am unable to connect to my AI core."


# ─────────────────────────────────────────────
#  HELPER: Open URL
# ─────────────────────────────────────────────
def open_url(url):
    """Open a URL using the default browser on Windows."""
    os.startfile(url)


# ─────────────────────────────────────────────
#  HELPERS MOVED TO tools/system_tools.py
# ─────────────────────────────────────────────
#  HELPER: Close App
# ─────────────────────────────────────────────
def close_app(app_name):
    """Close an application by its process name."""
    # Map friendly names to process names
    process_map = {
        "notepad": "notepad.exe",
        "calculator": "CalculatorApp.exe",
        "calc": "CalculatorApp.exe",
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",
        "brave": "brave.exe",
        "word": "WINWORD.EXE",
        "microsoft word": "WINWORD.EXE",
        "excel": "EXCEL.EXE",
        "microsoft excel": "EXCEL.EXE",
        "powerpoint": "POWERPNT.EXE",
        "microsoft powerpoint": "POWERPNT.EXE",
        "paint": "mspaint.exe",
        "vs code": "Code.exe",
        "visual studio code": "Code.exe",
        "vscode": "Code.exe",
        "spotify": "Spotify.exe",
        "discord": "Discord.exe",
        "telegram": "Telegram.exe",
        "vlc": "vlc.exe",
        "task manager": "Taskmgr.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "whatsapp": "WhatsApp.exe",
        "zoom": "Zoom.exe",
        "teams": "Teams.exe",
        "slack": "slack.exe",
        "obs": "obs64.exe",
        "obs studio": "obs64.exe",
    }

    proc_name = process_map.get(app_name.lower(), f"{app_name}.exe")
    killed = False

    # Strategy 1: Match by process name (case-insensitive + partial match)
    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info['name']
            if pname:
                pname_lower = pname.lower()
                if proc_name.lower() == pname_lower or app_name.lower() in pname_lower:
                    proc.kill()
                    killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Strategy 2: Fallback - use taskkill command
    if not killed:
        try:
            result = subprocess.run(
                f"taskkill /IM {proc_name} /F",
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                killed = True
        except Exception:
            pass

    return killed


# User home directory for building paths
_USER = os.path.expanduser("~")
_APPDATA = os.environ.get("APPDATA", "")
_LOCALAPPDATA = os.environ.get("LOCALAPPDATA", "")

APPS = {
    # Built-in Windows apps (always available)
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "wordpad": "wordpad.exe",
    "snipping tool": "SnippingTool.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "registry editor": "regedit.exe",
    "character map": "charmap.exe",
    "magnifier": "magnify.exe",
    "narrator": "narrator.exe",
    "sticky notes": "ms-actioncenter:",
    "clock": "ms-clock:",
    "alarm": "ms-clock:",
    "calendar": "outlookcal:",
    "photos": "ms-photos:",
    "camera": "microsoft.windows.camera:",
    "maps": "bingmaps:",
    "weather": "bingweather:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "feedback hub": "feedback-hub:",

    # Browsers
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "brave": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "opera": os.path.join(_LOCALAPPDATA, r"Programs\Opera\launcher.exe"),

    # Development
    "vs code": "code",
    "visual studio code": "code",
    "vscode": "code",
    "git bash": r"C:\Program Files\Git\git-bash.exe",
    "android studio": r"C:\Program Files\Android\Android Studio\bin\studio64.exe",
    "pycharm": r"C:\Program Files\JetBrains\PyCharm\bin\pycharm64.exe",
    "intellij": r"C:\Program Files\JetBrains\IntelliJ IDEA\bin\idea64.exe",

    # Microsoft Office
    "word": "WINWORD.EXE",
    "microsoft word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "microsoft excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
    "microsoft powerpoint": "POWERPNT.EXE",
    "outlook": "OUTLOOK.EXE",
    "onenote": "ONENOTE.EXE",
    "access": "MSACCESS.EXE",

    # Communication & Social (correct Windows paths)
    "discord": os.path.join(_LOCALAPPDATA, r"Discord\Update.exe --processStart Discord.exe"),
    "telegram": os.path.join(_APPDATA, r"Telegram Desktop\Telegram.exe"),
    "whatsapp": os.path.join(_LOCALAPPDATA, r"WhatsApp\WhatsApp.exe"),
    "zoom": os.path.join(_APPDATA, r"Zoom\bin\Zoom.exe"),
    "teams": os.path.join(_LOCALAPPDATA, r"Microsoft\Teams\Update.exe --processStart ms-teams.exe"),
    "microsoft teams": os.path.join(_LOCALAPPDATA, r"Microsoft\Teams\Update.exe --processStart ms-teams.exe"),
    "slack": os.path.join(_LOCALAPPDATA, r"slack\slack.exe"),
    "skype": "ms-skype:",

    # Media & Entertainment (correct Windows paths)
    "spotify": os.path.join(_APPDATA, r"Spotify\Spotify.exe"),
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vlc media player": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "obs studio": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "audacity": r"C:\Program Files\Audacity\Audacity.exe",

    # Utilities
    "winrar": r"C:\Program Files\WinRAR\WinRAR.exe",
    "7zip": r"C:\Program Files\7-Zip\7zFM.exe",
}


def find_and_open_app(app_name, app_path):
    """Try multiple strategies to open an app on Windows."""
    # Strategy 1: URI protocol (ms-settings:, ms-clock:, etc.)
    if ":" in app_path and not (len(app_path) > 1 and app_path[1] == ":"):
        os.startfile(app_path)
        return True

    # Strategy 2: Direct path exists
    # For paths with arguments (like Discord's Update.exe --processStart)
    exe_path = app_path.split(" ")[0] if " --" in app_path else app_path
    if os.path.exists(exe_path):
        subprocess.Popen(app_path, shell=True)
        return True

    # Strategy 3: App is in system PATH (e.g., code, msedge.exe, notepad.exe)
    try:
        subprocess.Popen(app_path, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass

    # Strategy 4: Search Start Menu shortcuts
    start_menu_dirs = [
        os.path.join(_APPDATA, r"Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]
    for start_dir in start_menu_dirs:
        if os.path.exists(start_dir):
            for root, dirs, files in os.walk(start_dir):
                for f in files:
                    if f.lower().endswith(".lnk") and app_name.lower() in f.lower():
                        os.startfile(os.path.join(root, f))
                        return True

    return False


# ─────────────────────────────────────────────
#  SITES DICTIONARY
# ─────────────────────────────────────────────
SITES = {
    "google": "https://google.com",
    "facebook": "https://facebook.com",
    "youtube": "https://youtube.com",
    "linkedin": "https://linkedin.com",
    "instagram": "https://instagram.com",
    "twitter": "https://twitter.com",
    "github": "https://github.com",
    "whatsapp": "https://web.whatsapp.com",
    "amazon": "https://amazon.in",
    "reddit": "https://reddit.com",
    "wikipedia": "https://wikipedia.org",
    "chatgpt": "https://chat.openai.com",
    "gmail": "https://mail.google.com",
    "drive": "https://drive.google.com",
    "netflix": "https://netflix.com",
    "flipkart": "https://flipkart.com",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "leetcode": "https://leetcode.com",
}

# Common folders
FOLDERS = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    "music": os.path.join(os.path.expanduser("~"), "Music"),
}


# ─────────────────────────────────────────────
#  MAIN COMMAND PROCESSOR
# ─────────────────────────────────────────────
def processCommand(c):
    cmd = c.lower().strip()
    print(f"[Processing] {cmd}")

    # ── EXIT ──────────────────────────────────
    if cmd in ["exit", "stop", "quit", "bye", "shutdown", "goodbye", "go away", "shut down", "bye bye"] or any(word in cmd for word in ["stop jarvis", "exit jarvis", "quit jarvis", "bye jarvis",
                                     "close jarvis", "shutdown jarvis", "shut down jarvis", "go to sleep", "see you later"]):
        speak("Goodbye! Shutting down Jarvis.")
        print("Jarvis shutting down...")
        os._exit(0)

    # ── TASK PLANNER ──────────────────────────
    if cmd.startswith("plan task ") or cmd.startswith("create workflow "):
        task_request = cmd.replace("plan task ", "").replace("create workflow ", "").strip()
        speak("Analyzing task requirements...")
        
        plan = planner.generate_plan(task_request, gemini_client)
        if not plan:
            speak("Sorry, I failed to generate a plan for this task.")
            return
            
        summary = planner.format_plan_for_speech(plan)
        if request_plan_approval(summary, speak, listen_for_confirmation):
            for step in plan:
                action = step.get("action")
                target = step.get("target")
                
                if action == "open_app":
                    app_path = APPS.get(target.lower())
                    if app_path:
                        speak(f"Opening {target}")
                        find_and_open_app(target, app_path)
                    else:
                        speak(f"App {target} not found in my registry.")
                elif action == "open_website":
                    url = target if target.startswith("http") else f"https://www.{target}.com"
                    speak(f"Opening {target}")
                    open_url(url)
                elif action == "run_terminal_command":
                    speak(f"Running command {target}")
                    subprocess.Popen(f"start cmd /k {target}", shell=True)
                elif action == "close_app":
                    if close_app(target):
                        speak(f"Closed {target}")
                    else:
                        speak(f"Could not close {target}")
                
            speak("Task execution complete.")
        return

    # ── AUTONOMOUS BROWSER AGENT ──────────────
    if any(word in cmd for word in ["open leetcode and solve", "autonomous", "open browser and", "find my daily problem"]):
        autonomous_agent.start_task(cmd)
        return

    # ── CODING MODE ───────────────────────────
    global CODING_MODE
    if "exit coding mode" in cmd or "stop coding mode" in cmd:
        CODING_MODE = False
        speak("Exited coding mode. Normal operations resumed.")
        return

    if "enter coding mode" in cmd or cmd == "coding mode" or "start coding mode" in cmd or "coding mod" in cmd:
        CODING_MODE = True
        speak("Coding mode activated. I will now only generate code for your commands.")
        return

    if CODING_MODE or any(word in cmd for word in ["screen", "this problem", "leetcode"]):
        prompt = cmd
        try:
            import pyperclip
            import time
            
            if any(word in prompt for word in ["screen", "this problem", "leetcode"]):
                speak("Reading your screen. Please wait...")
                screenshot = pyautogui.screenshot()
                api_contents = [
                    f"You are an expert programmer. Read the coding problem visible in the provided screenshot and solve it. Provide ONLY the raw code for the solution. Do NOT include ANY markdown formatting, backticks, or explanations. Just the code itself. Additional user instruction: {prompt}",
                    screenshot
                ]
            else:
                speak("Generating code. Please click on your code editor...")
                api_contents = f"You are an expert programmer. Provide ONLY the raw code for this request. Do NOT include ANY markdown formatting, backticks, or explanations. Just the code itself. Request: {prompt}"

            response = None
            for attempt in range(3):
                try:
                    response = gemini_client.chats.create(model="gemini-3.6-flash").send_message(api_contents)
                    break
                except Exception as api_e:
                    if "503" in str(api_e) and attempt < 2:
                        time.sleep(2)
                        continue
                    raise api_e
                    
            code = response.text.strip()
            if code.startswith("```"):
                lines = code.split('\n')
                if len(lines) > 1:
                    code = '\n'.join(lines[1:])
            if code.endswith("```"):
                code = '\n'.join(code.split('\n')[:-1])
            pyperclip.copy(code.strip())
            time.sleep(0.2)
            pyautogui.hotkey('ctrl', 'v')
            speak("Code written successfully")
        except Exception as e:
            print(f"Code Gen Error: {e}")
            speak("Sorry, I could not generate the code")
        return

    # ── MEMORY & RAG ──────────────────────────
    elif cmd.startswith("remember that "):
        fact = c[14:].strip() # preserve case
        import datetime
        key = f"Fact_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        jarvis_memory.save_preference(key, fact)
        speak("I will remember that.")
        print(f"Memorized: {fact}")

    elif any(word in cmd for word in ["upload file", "upload document", "upload my things"]):
        speak("Please select a file to upload.")
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw() # Hide the main window
        root.attributes('-topmost', True) # Bring dialog to front
        file_path = filedialog.askopenfilename()
        if file_path:
            os.makedirs("memory/uploads", exist_ok=True)
            filename = os.path.basename(file_path)
            shutil.copy(file_path, os.path.join("memory/uploads", filename))
            speak(f"Successfully uploaded {filename}")
            print(f"Uploaded: {filename}")
        else:
            speak("Upload cancelled")
        root.destroy()

    # ── AUTOMATED LOGIN MACRO ─────────────────
    elif cmd.startswith("login") or cmd.startswith("sign in"):
        target_site = cmd.replace("login", "").replace("sign in", "").replace("into", "").replace("to", "").replace("in", "").replace("on", "").strip()
        
        target_cleaned = target_site.replace("linked in", "linkedin") \
                               .replace("link din", "linkedin") \
                               .replace("link in", "linkedin") \
                               .replace("lead code", "leetcode") \
                               .replace("leet code", "leetcode")
                               
        if target_cleaned:
            login_urls = {
                "leetcode": "https://leetcode.com/accounts/login/",
                "github": "https://github.com/login",
                "facebook": "https://www.facebook.com/login/",
                "twitter": "https://twitter.com/login",
                "linkedin": "https://www.linkedin.com/login",
                "google": "https://accounts.google.com/",
                "gmail": "https://accounts.google.com/"
            }
            
            site_key = target_cleaned.replace(" ", "")
            url = login_urls.get(site_key)
            if not url:
                base_url = SITES.get(site_key)
                if base_url:
                    url = base_url
                else:
                    url = f"https://{site_key}.com"
                    
            speak(f"Opening login page for {target_site}")
            open_url(url)
            import time
            time.sleep(5) # Wait for page to load
            
        speak("Which account would you like to use?")
        account_name = listen_for_confirmation().lower().strip()
        
        credentials = {
            "personal": {"user": "amit_personal", "pass": "pass123"},
            "work": {"user": "amit_work", "pass": "workpass456"}
        }
        
        username = "YOUR_USERNAME"
        password = "YOUR_PASSWORD"
        
        found = False
        for key, creds in credentials.items():
            if key in account_name:
                username = creds["user"]
                password = creds["pass"]
                speak(f"Using {key} account. Please focus the login field.")
                found = True
                break
                
        if not found:
            if account_name:
                speak(f"Account {account_name} not found. Using default placeholder.")
            else:
                speak("No account specified. Using default placeholder.")
                
        speak("Locating the login fields on your screen. Please wait...")
        try:
            import json
            screenshot = pyautogui.screenshot()
            prompt = """
Analyze this screenshot. Find the username or email login input field.
Return ONLY a valid JSON object with the x and y coordinates of the center of that input field.
For example: {"x": 500, "y": 300}
If you absolutely cannot find a login field, return {"error": "not found"}
"""
            response = None
            for attempt in range(3):
                try:
                    response = gemini_client.chats.create(model="gemini-3.6-flash").send_message([prompt, screenshot])
                    break
                except Exception as api_e:
                    if "503" in str(api_e) and attempt < 2:
                        import time
                        time.sleep(2)
                        continue
                    raise api_e
            
            json_str = response.text.strip()
            if json_str.startswith("```json"): json_str = json_str[7:]
            if json_str.startswith("```"): json_str = json_str[3:]
            if json_str.endswith("```"): json_str = json_str[:-3]
                
            data = json.loads(json_str.strip())
            
            if "error" in data:
                speak("I couldn't find the login field on the screen. Please click it yourself.")
                import time
                time.sleep(3)
            else:
                x = data.get("x")
                y = data.get("y")
                if x and y:
                    pyautogui.click(x, y)
                    import time
                    time.sleep(0.5)
                else:
                    speak("Could not determine coordinates. Please click it yourself.")
                    import time
                    time.sleep(3)
        except Exception as e:
            print(f"Vision AI Error: {e}")
            speak("Error using vision. Please click the login field yourself.")
            import time
            time.sleep(3)
            
        pyautogui.typewrite(username, interval=0.05)
        pyautogui.press('tab')
        pyautogui.typewrite(password, interval=0.05)
        pyautogui.press('enter')
        speak("Login credentials entered.")

    # ── AGENTIC CODE RUNNER ───────────────────
    elif "run this code" in cmd:
        speak("Analyzing code on your screen... Please focus your code editor now. You have 3 seconds.")
        import pyperclip
        import time
        import json
        
        time.sleep(3) # Give user time to focus the editor so ctrl+c doesn't kill the terminal
        
        # Copy code from the active editor
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        code = pyperclip.paste()
        
        if not code.strip():
            speak("I could not find any code to run.")
            return

        prompt = f"""
Analyze this code. I want to run it on Windows.
Return a valid JSON object EXACTLY in this format, with no markdown formatting:
{{
    "extension": ".py",
    "install_commands": ["pip install requests"],
    "run_command": "python auto_run.py"
}}
Code:
{code}
"""
        try:
            response = gemini_client.chats.create(model="gemini-3.6-flash").send_message(prompt)
            # Clean JSON
            json_str = response.text.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
                
            data = json.loads(json_str.strip())
            
            filename = "auto_run" + data.get("extension", ".py")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
                
            if data.get("install_commands"):
                speak("Installing dependencies...")
                for install_cmd in data["install_commands"]:
                    subprocess.run(install_cmd, shell=True)
                    
            speak("Running the code now.")
            result = subprocess.run(data.get("run_command", f"python {filename}"), shell=True, capture_output=True, text=True)
            print("Output:\n", result.stdout)
            if result.stderr:
                print("Errors:\n", result.stderr)
            speak("Code execution complete. Check the terminal for output.")
            
        except Exception as e:
            speak("Sorry, I could not run this code.")
            print(f"Agentic Runner Error: {e}")
    # ── SMART CLICK (No API needed) ───────────
    elif cmd.startswith("click "):
        target = cmd.replace("click ", "").strip()
        if target.startswith("on "): target = target[3:].strip()
        elif target.startswith("in "): target = target[3:].strip()
        
        speak(f"Looking for {target}...")
        clicked = False
        target_lower = target.lower()
        
        # Strategy 1: Windows UI Automation - find control by its text/name (no API needed)
        try:
            import uiautomation as auto
            
            def find_and_click(control, depth=0):
                if depth > 8:
                    return False
                try:
                    name = (control.Name or "").lower()
                    if name and all(word in name for word in target_lower.split()):
                        rect = control.BoundingRectangle
                        if rect.width() > 0 and rect.height() > 0:
                            cx = rect.left + rect.width() // 2
                            cy = rect.top + rect.height() // 2
                            pyautogui.click(cx, cy)
                            return True
                except Exception:
                    pass
                try:
                    for child in control.GetChildren():
                        if find_and_click(child, depth + 1):
                            return True
                except Exception:
                    pass
                return False
            
            clicked = find_and_click(auto.GetRootControl())
        except Exception as e:
            print(f"UI Automation error: {e}")
        
        # Strategy 2: Screenshot-based pixel search for the text using pyautogui
        if not clicked:
            try:
                # Search for the text as an image on screen
                loc = pyautogui.locateOnScreen(target, confidence=0.7, grayscale=True)
                if loc:
                    pyautogui.click(pyautogui.center(loc))
                    clicked = True
            except Exception:
                pass
        
        if clicked:
            speak("Clicked.")
        else:
            speak(f"Sorry, I could not find {target} on the screen.")

    # ── CLOSE APP ─────────────────────────────
    elif cmd.startswith("close "):
        app_name = cmd.replace("close ", "").strip()
        if close_app(app_name):
            speak(f"Closed {app_name}")
        else:
            speak(f"Could not find {app_name} running")

    # ── OPEN COMMANDS ─────────────────────────
    elif cmd.startswith("open "):
        target = cmd.replace("open ", "").strip()

        target_cleaned = target.replace("linked in", "linkedin") \
                               .replace("link din", "linkedin") \
                               .replace("link in", "linkedin") \
                               .replace("v s code", "vs code") \
                               .replace("v.s. code", "vs code") \
                               .replace("visual studio", "vs code") \
                               .replace("file manager", "file explorer") \
                               .replace("lead code", "leetcode") \
                               .replace("leet code", "leetcode")

        # 1) Check if it's a folder
        for folder_name, folder_path in FOLDERS.items():
            if folder_name in target_cleaned:
                if os.path.exists(folder_path):
                    speak(f"Opening {folder_name} folder")
                    os.startfile(folder_path)
                else:
                    speak(f"Sorry, {folder_name} folder was not found")
                return

        # 2) Check if it's a known app
        matched_app = False
        for app_name, app_path in APPS.items():
            if app_name in target_cleaned:
                speak(f"Opening {app_name}")
                if not find_and_open_app(app_name, app_path):
                    speak(f"Sorry, {app_name} is not installed or I can't find it")
                matched_app = True
                break

        if matched_app:
            return

        # 3) Check if it's a known website
        for site_name, url in SITES.items():
            if site_name in target_cleaned:
                speak(f"Opening {site_name}")
                open_url(url)
                return

        # 4) Fallback: try as a .com website
        site_guess = target_cleaned.replace(" ", "")
        speak(f"Opening {site_guess}")
        open_url(f"https://{site_guess}.com")

    # ── PLAY MUSIC ────────────────────────────
    elif cmd.startswith("play "):
        song = cmd.replace("play ", "").strip()
        if song in musicLibrary.music:
            link = musicLibrary.music[song]
            speak(f"Playing {song}")
            open_url(link)
        else:
            # Try searching on YouTube
            speak(f"Searching {song} on YouTube")
            open_url(f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}")

    # ── VOLUME CONTROL ────────────────────────
    elif "volume" in cmd:
        try:
            if "mute" in cmd:
                sys_tools.toggle_mute(True)
                speak("Muted")
            elif "unmute" in cmd:
                sys_tools.toggle_mute(False)
                speak("Unmuted")
            elif "up" in cmd or "increase" in cmd:
                new_vol = sys_tools.change_volume(10)
                speak(f"Volume set to {new_vol} percent")
            elif "down" in cmd or "decrease" in cmd or "reduce" in cmd:
                new_vol = sys_tools.change_volume(-10)
                speak(f"Volume set to {new_vol} percent")
            elif "set" in cmd or "to" in cmd:
                import re
                numbers = re.findall(r'\d+', cmd)
                if numbers:
                    level = int(numbers[0])
                    sys_tools.set_volume(level)
                    speak(f"Volume set to {level} percent")
                else:
                    speak("Please specify a volume level")
            elif "what" in cmd or "current" in cmd or "check" in cmd:
                current = sys_tools.get_volume()
                speak(f"Current volume is {current} percent")
            else:
                current = sys_tools.get_volume()
                speak(f"Current volume is {current} percent")
        except Exception as e:
            print(f"Volume Error: {e}")
            speak("Sorry, I couldn't adjust the volume")

    elif cmd in ["mute", "unmute"]:
        try:
            sys_tools.toggle_mute(cmd == "mute")
            speak(f"{'Muted' if cmd == 'mute' else 'Unmuted'}")
        except Exception as e:
            print(f"Mute Error: {e}")
            speak("Sorry, I couldn't change the mute state")

    # ── BRIGHTNESS CONTROL ────────────────────
    elif "brightness" in cmd:
        try:
            if "up" in cmd or "increase" in cmd:
                current = sys_tools.get_brightness()
                new_val = min(100, current + 10)
                sys_tools.set_brightness(new_val)
                speak(f"Brightness set to {new_val} percent")
            elif "down" in cmd or "decrease" in cmd or "reduce" in cmd:
                current = sys_tools.get_brightness()
                new_val = max(0, current - 10)
                sys_tools.set_brightness(new_val)
                speak(f"Brightness set to {new_val} percent")
            elif "set" in cmd or "to" in cmd:
                import re
                numbers = re.findall(r'\d+', cmd)
                if numbers:
                    level = int(numbers[0])
                    sys_tools.set_brightness(level)
                    speak(f"Brightness set to {level} percent")
                else:
                    speak("Please specify a brightness level")
            else:
                current = sys_tools.get_brightness()
                speak(f"Current brightness is {current} percent")
        except Exception as e:
            print(f"Brightness Error: {e}")
            speak("Sorry, I couldn't adjust the brightness")

    # ── SCREENSHOT ────────────────────────────
    elif "screenshot" in cmd or "screen shot" in cmd or "capture screen" in cmd:
        try:
            filepath = sys_tools.take_screenshot()
            speak(f"Screenshot saved to desktop")
            print(f"Screenshot saved: {filepath}")
        except Exception as e:
            print(f"Screenshot Error: {e}")
            speak("Sorry, I couldn't take a screenshot")

    # ── SYSTEM POWER ──────────────────────────
    elif any(w in cmd for w in ["shutdown computer", "shut down computer", "shutdown pc",
                                 "shut down pc", "turn off computer", "turn off pc"]):
        if request_permission("shut down the computer", RiskLevel.HIGH, speak, listen_for_confirmation):
            speak("Shutting down the computer in 10 seconds. Say cancel to abort.")
            sys_tools.shutdown_computer()

    elif "cancel shutdown" in cmd or "abort shutdown" in cmd:
        sys_tools.cancel_shutdown()
        speak("Shutdown cancelled")

    elif any(w in cmd for w in ["restart computer", "restart pc", "reboot"]):
        if request_permission("restart the computer", RiskLevel.HIGH, speak, listen_for_confirmation):
            speak("Restarting the computer in 10 seconds")
            sys_tools.restart_computer()

    elif "lock" in cmd and any(w in cmd for w in ["screen", "computer", "pc", "system"]):
        speak("Locking the screen")
        sys_tools.lock_screen()

    elif "sleep" in cmd and any(w in cmd for w in ["computer", "pc", "system", "mode"]):
        speak("Putting the computer to sleep")
        sys_tools.sleep_computer()

    # ── SEARCH ────────────────────────────────
    elif cmd.startswith("search ") or cmd.startswith("google ") or cmd.startswith("search for "):
        query = cmd.replace("search for ", "").replace("search ", "").replace("google ", "").strip()
        speak(f"Searching for {query}")
        open_url(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    elif cmd.startswith("youtube search ") or (cmd.startswith("search") and "youtube" in cmd):
        query = cmd.replace("youtube search ", "").replace("search ", "").replace("on youtube", "").strip()
        speak(f"Searching YouTube for {query}")
        open_url(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")

    # ── AI CODE GENERATION & TYPING ────────────────
    elif any(w in cmd for w in ["write", "generate", "create"]) and any(w in cmd for w in ["code", "program", "script"]):
        prompt = c.strip()
        speak("Generating code. Please click on your code editor...")
        try:
            import pyperclip
            import time
            response = gemini_client.chats.create(model="gemini-3.6-flash").send_message(f"You are an expert programmer. Provide ONLY the raw code for this request. Do NOT include ANY markdown formatting, backticks, or explanations. Just the code itself. Request: {prompt}")
            code = response.text.strip()
            # Clean up backticks just in case
            if code.startswith("```"):
                lines = code.split('\n')
                if len(lines) > 1:
                    code = '\n'.join(lines[1:])
            if code.endswith("```"):
                code = '\n'.join(code.split('\n')[:-1])
            
            pyperclip.copy(code.strip())
            time.sleep(0.2) # Give user a moment to focus the window
            pyautogui.hotkey('ctrl', 'v')
            speak("Code written successfully")
        except Exception as e:
            print(f"Code Gen Error: {e}")
            speak("Sorry, I could not generate the code")

    # ── TYPING / DICTATION ────────────────────
    elif cmd.startswith("type ") or cmd.startswith("write "):
        text = c[5:] if c.lower().startswith("type ") else c[6:]  # preserve original case
        import time
        time.sleep(0.5)  # small delay so user can switch to target window
        pyautogui.typewrite(text, interval=0.03) if text.isascii() else pyautogui.write(text)
        speak("Done typing")

    # ── CLIPBOARD ─────────────────────────────
    elif "copy" in cmd and ("that" in cmd or "this" in cmd or "selection" in cmd):
        pyautogui.hotkey('ctrl', 'c')
        speak("Copied")

    elif "paste" in cmd:
        pyautogui.hotkey('ctrl', 'v')
        speak("Pasted")

    elif "cut" in cmd and ("that" in cmd or "this" in cmd or "selection" in cmd):
        pyautogui.hotkey('ctrl', 'x')
        speak("Cut to clipboard")

    elif "select all" in cmd:
        pyautogui.hotkey('ctrl', 'a')
        speak("Selected all")

    elif "undo" in cmd:
        pyautogui.hotkey('ctrl', 'z')
        speak("Undone")

    elif "redo" in cmd:
        pyautogui.hotkey('ctrl', 'y')
        speak("Redone")

    elif "save" in cmd and "file" in cmd:
        pyautogui.hotkey('ctrl', 's')
        speak("Saved")

    # ── DATE & TIME ───────────────────────────
    elif any(w in cmd for w in ["what time", "current time", "time now", "tell me the time",
                                 "what's the time", "whats the time"]):
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        speak(f"The time is {time_str}")

    elif any(w in cmd for w in ["what date", "today's date", "current date", "what's the date",
                                 "whats the date", "tell me the date"]):
        now = datetime.datetime.now()
        date_str = now.strftime("%B %d, %Y")
        speak(f"Today's date is {date_str}")

    elif any(w in cmd for w in ["what day", "which day", "what's the day", "whats the day"]):
        now = datetime.datetime.now()
        day_str = now.strftime("%A")
        speak(f"Today is {day_str}")

    # ── SYSTEM INFO ───────────────────────────
    elif "battery" in cmd:
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "plugged in" if battery.power_plugged else "not plugged in"
                speak(f"Battery is at {percent} percent and {plugged}")
            else:
                speak("Battery information is not available on this device")
        except Exception:
            speak("Could not retrieve battery information")

    elif "ip address" in cmd or "my ip" in cmd:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            speak(f"Your local IP address is {local_ip}")
        except Exception:
            speak("Could not retrieve IP address")

    elif "cpu" in cmd and ("usage" in cmd or "status" in cmd or "percent" in cmd):
        usage = psutil.cpu_percent(interval=1)
        speak(f"CPU usage is {usage} percent")

    elif "memory" in cmd or "ram" in cmd:
        mem = psutil.virtual_memory()
        speak(f"Memory usage is {mem.percent} percent. {round(mem.available / (1024**3), 1)} GB available out of {round(mem.total / (1024**3), 1)} GB total")

    elif "disk" in cmd and ("space" in cmd or "usage" in cmd or "storage" in cmd):
        disk = shutil.disk_usage("C:\\")
        total = round(disk.total / (1024**3), 1)
        free = round(disk.free / (1024**3), 1)
        used_pct = round((disk.used / disk.total) * 100, 1)
        speak(f"C drive: {total} GB total, {free} GB free, {used_pct} percent used")

    elif "system info" in cmd or "system information" in cmd:
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            battery = psutil.sensors_battery()
            battery_info = f"Battery at {battery.percent} percent" if battery else "No battery detected"
            speak(f"CPU usage {cpu} percent. Memory usage {mem.percent} percent. {battery_info}")
        except Exception:
            speak("Could not retrieve system information")

    # ── WINDOW CONTROL ────────────────────────
    elif "minimize" in cmd:
        if "all" in cmd or "everything" in cmd:
            pyautogui.hotkey('win', 'd')
            speak("Minimized all windows")
        else:
            pyautogui.hotkey('win', 'down')
            speak("Minimized window")

    elif "maximize" in cmd:
        pyautogui.hotkey('win', 'up')
        speak("Maximized window")

    elif "switch window" in cmd or "alt tab" in cmd or "next window" in cmd:
        pyautogui.hotkey('alt', 'tab')
        speak("Switched window")

    elif "show desktop" in cmd or "go to desktop" in cmd:
        pyautogui.hotkey('win', 'd')
        speak("Showing desktop")

    elif "close window" in cmd or "close this" in cmd:
        pyautogui.hotkey('alt', 'F4')
        speak("Closed window")

    elif "new tab" in cmd:
        pyautogui.hotkey('ctrl', 't')
        speak("Opened new tab")

    elif "close tab" in cmd:
        pyautogui.hotkey('ctrl', 'w')
        speak("Closed tab")

    elif "full screen" in cmd or "fullscreen" in cmd:
        pyautogui.press('f11')
        speak("Toggled fullscreen")

    # ── MEDIA CONTROL ─────────────────────────
    elif cmd in ["pause", "resume", "play pause", "play", "pause music", "resume music"]:
        pyautogui.press('playpause')
        speak("Toggled play pause")

    elif "next track" in cmd or "next song" in cmd or "skip" in cmd:
        pyautogui.press('nexttrack')
        speak("Next track")

    elif "previous track" in cmd or "previous song" in cmd or "go back" in cmd:
        pyautogui.press('prevtrack')
        speak("Previous track")

    elif "stop music" in cmd or "stop playing" in cmd:
        pyautogui.press('stop')
        speak("Stopped")

    # ── WI-FI CONTROL ─────────────────────────
    elif ("wifi" in cmd or "wi-fi" in cmd or "wi fi" in cmd):
        if any(w in cmd for w in ["off", "disable", "turn off", "disconnect"]):
            subprocess.Popen("netsh interface set interface Wi-Fi disable", shell=True)
            speak("Wi-Fi turned off")
        elif any(w in cmd for w in ["on", "enable", "turn on", "connect"]):
            subprocess.Popen("netsh interface set interface Wi-Fi enable", shell=True)
            speak("Wi-Fi turned on")
        else:
            # Check Wi-Fi status
            result = subprocess.run("netsh interface show interface Wi-Fi", shell=True,
                                    capture_output=True, text=True)
            if "Connected" in result.stdout:
                speak("Wi-Fi is currently connected")
            else:
                speak("Wi-Fi is currently disconnected")

    # ── OPEN RECYCLE BIN ──────────────────────
    elif "recycle bin" in cmd or "trash" in cmd:
        speak("Opening recycle bin")
        subprocess.Popen("explorer.exe shell:RecycleBinFolder", shell=True)

    elif "empty recycle bin" in cmd or "empty trash" in cmd:
        speak("Emptying the recycle bin")
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)

    # ── NEWS ──────────────────────────────────
    elif "news" in cmd:
        r = requests.get(f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}")
        if r.status_code == 200:
            # Parse the JSON response
            data = r.json()

            # Extract the articles
            articles = data.get('articles', [])

            # Print the headlines
            for article in articles:
                speak(article['title'])
        else:
            speak("Sorry, I couldn't fetch the news right now")

    # ── KEYBOARD SHORTCUTS ────────────────────
    elif "open run" in cmd or "run dialog" in cmd:
        pyautogui.hotkey('win', 'r')
        speak("Opened Run dialog")

    elif "open emoji" in cmd or "emoji keyboard" in cmd:
        pyautogui.hotkey('win', '.')
        speak("Opened emoji keyboard")

    elif "snip" in cmd or "screen snip" in cmd:
        pyautogui.hotkey('win', 'shift', 's')
        speak("Snipping tool ready")

    elif "action center" in cmd or "notification" in cmd:
        pyautogui.hotkey('win', 'a')
        speak("Opened action center")

    elif "clipboard history" in cmd:
        pyautogui.hotkey('win', 'v')
        speak("Opened clipboard history")

    elif "zoom in" in cmd:
        pyautogui.hotkey('ctrl', '+')
        speak("Zoomed in")

    elif "zoom out" in cmd:
        pyautogui.hotkey('ctrl', '-')
        speak("Zoomed out")

    elif "refresh" in cmd:
        pyautogui.press('f5')
        speak("Refreshed")

    elif "go back" in cmd:
        pyautogui.hotkey('alt', 'left')
        speak("Went back")

    elif "go forward" in cmd:
        pyautogui.hotkey('alt', 'right')
        speak("Went forward")

    # ── FALLBACK: OpenAI ──────────────────────
    else:
        # Let OpenAI handle the request
        try:
            output = aiProcess(c)
            speak(output)
        except Exception as e:
            print(f"OpenAI Error: {e}")
            speak("Sorry, I couldn't process that request")


# ─────────────────────────────────────────────
#  MAIN: Background Listening
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import threading
    import time

    speak("Initializing Jarvis....")

    r = sr.Recognizer()
    r.pause_threshold = 1        # seconds of silence before considering phrase complete
    r.dynamic_energy_threshold = True  # auto-adjust to ambient noise
    r.energy_threshold = 300     # starting sensitivity (lower = more sensitive)

    # Calibrate for ambient noise
    with sr.Microphone() as temp_source:
        print("Calibrating for ambient noise... Please wait.")
        r.adjust_for_ambient_noise(temp_source, duration=2)
        print("Calibration done. Say 'Jarvis' to activate.")

    print("=" * 55)
    print("  JARVIS PC ASSISTANT — READY")
    print("=" * 55)
    print("  Say 'Jarvis' to activate, then speak your command.")
    print("  Press Ctrl+C to quit.")
    print("=" * 55)
    print()
    print("  Available commands:")
    print("  • Open/Close apps      • Volume/Brightness")
    print("  • Screenshot            • Search Google/YouTube")
    print("  • Type text             • Copy/Paste/Undo")
    print("  • Date & Time           • Battery/CPU/RAM/Disk")
    print("  • Minimize/Maximize     • Media controls")
    print("  • Lock/Shutdown/Restart • Wi-Fi on/off")
    print("  • Play music            • News headlines")
    print("  • Ask anything (AI)     • And more...")
    print("=" * 55)
    print()

    def listen_loop():
        """Continuously listen for wake word and commands in a background thread."""
        while True:
            try:
                # If Autonomous Agent is running, bypass wake word and listen for interruptions
                if autonomous_agent.is_running():
                    with sr.Microphone() as source:
                        audio = r.listen(source, phrase_time_limit=3)
                    
                    try:
                        word = r.recognize_google(audio, language="en-IN").lower()
                        print(f"[Interrupt Listener] Heard: {word}")
                        if "stop" in word or "cancel" in word:
                            autonomous_agent.cancel()
                        elif "pause" in word:
                            autonomous_agent.pause()
                        elif "resume" in word or "continue" in word or "done" in word:
                            autonomous_agent.resume()
                    except:
                        pass
                    continue
            
                # Standard Mode: Listen for wake word
                with sr.Microphone() as source:
                    audio = r.listen(source, phrase_time_limit=3)

                word = r.recognize_google(audio, language="en-IN")
                print(f"Heard: {word}")

                if "jarvis" in word.lower():
                    speak("Jarvis is ready to assist.")
                    
                    active = True
                    while active:
                        # Continuous conversation loop
                        print("Jarvis Active... Speak your command.")
                        with sr.Microphone() as cmd_source:
                            r.adjust_for_ambient_noise(cmd_source, duration=0.5)
                            try:
                                cmd_audio = r.listen(cmd_source, timeout=10, phrase_time_limit=10)
                                command = r.recognize_google(cmd_audio, language="en-IN").lower()
                                print(f"Command received: {command}")
                                
                                if command in ["go to sleep", "stop listening", "that is all", "that's all", "nothing", "no", "sleep", "bye"]:
                                    speak("Going to sleep. Say Jarvis to wake me up.")
                                    active = False
                                    break
                                    
                                speak("Yes, sir.")
                                processCommand(command)
                                
                            except sr.WaitTimeoutError:
                                print("Timeout. Going back to sleep.")
                                active = False
                            except sr.UnknownValueError:
                                # Ignore if it didn't understand the speech and keep listening
                                pass

            except sr.UnknownValueError:
                pass  # normal — couldn't understand
            except sr.WaitTimeoutError:
                pass  # normal — no speech detected
            except sr.RequestError as e:
                print(f"Error: Speech Recognition request failed - {e}")
            except Exception as e:
                print(f"Error ({type(e).__name__}): {e}")

    # Run listener in a daemon thread so it works even when terminal is not focused
    listener_thread = threading.Thread(target=listen_loop, daemon=True)
    listener_thread.start()

    # Keep the main thread alive by launching the GUI dashboard
    try:
        dashboard.start_dashboard()
    except KeyboardInterrupt:
        print("\nGoodbye!")

