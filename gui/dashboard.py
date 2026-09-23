import tkinter as tk
from tkinter import ttk
import psutil
import threading
import time

class JarvisDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS 2.0 - System Monitor")
        self.root.geometry("400x700")
        self.root.configure(bg="#0a0a0a")
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#0a0a0a", foreground="#00ffcc", font=("Consolas", 12))
        style.configure("Title.TLabel", font=("Consolas", 20, "bold"))
        style.configure("TProgressbar", background="#00ffcc", troughcolor="#222222")

        # Header
        self.header = ttk.Label(root, text="JARVIS 2.0", style="Title.TLabel")
        self.header.pack(pady=20)

        # Status Label
        self.status_var = tk.StringVar()
        self.status_var.set("Status: ONLINE")
        self.status_label = ttk.Label(root, textvariable=self.status_var, font=("Consolas", 14, "bold"), foreground="#00ff00")
        self.status_label.pack(pady=10)

        # System Metrics Frame
        self.metrics_frame = tk.Frame(root, bg="#0a0a0a")
        self.metrics_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # CPU
        ttk.Label(self.metrics_frame, text="CPU Usage:").pack(anchor=tk.W)
        self.cpu_bar = ttk.Progressbar(self.metrics_frame, orient=tk.HORIZONTAL, length=350, mode='determinate')
        self.cpu_bar.pack(pady=5)
        self.cpu_lbl = ttk.Label(self.metrics_frame, text="0%")
        self.cpu_lbl.pack(anchor=tk.E)

        # RAM
        ttk.Label(self.metrics_frame, text="RAM Usage:").pack(anchor=tk.W, pady=(10,0))
        self.ram_bar = ttk.Progressbar(self.metrics_frame, orient=tk.HORIZONTAL, length=350, mode='determinate')
        self.ram_bar.pack(pady=5)
        self.ram_lbl = ttk.Label(self.metrics_frame, text="0%")
        self.ram_lbl.pack(anchor=tk.E)

        # Battery
        ttk.Label(self.metrics_frame, text="Battery:").pack(anchor=tk.W, pady=(10,0))
        self.bat_bar = ttk.Progressbar(self.metrics_frame, orient=tk.HORIZONTAL, length=350, mode='determinate')
        self.bat_bar.pack(pady=5)
        self.bat_lbl = ttk.Label(self.metrics_frame, text="0%")
        self.bat_lbl.pack(anchor=tk.E)
        
        # Autonomous Agent Frame
        self.agent_frame = tk.Frame(root, bg="#1a1a2e", bd=2, relief=tk.RIDGE)
        self.agent_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(self.agent_frame, text="AUTONOMOUS MODE", font=("Consolas", 14, "bold"), background="#1a1a2e", foreground="#ff00ff").pack(pady=5)
        
        self.task_var = tk.StringVar(value="Task: None")
        ttk.Label(self.agent_frame, textvariable=self.task_var, background="#1a1a2e").pack(anchor=tk.W, padx=10)
        
        self.agent_status_var = tk.StringVar(value="Status: IDLE")
        ttk.Label(self.agent_frame, textvariable=self.agent_status_var, background="#1a1a2e", font=("Consolas", 12, "bold")).pack(anchor=tk.W, padx=10, pady=5)
        
        self.url_var = tk.StringVar(value="URL: None")
        ttk.Label(self.agent_frame, textvariable=self.url_var, background="#1a1a2e").pack(anchor=tk.W, padx=10)

        self.update_metrics()

    def update_metrics(self):
        # CPU
        cpu = psutil.cpu_percent()
        self.cpu_bar['value'] = cpu
        self.cpu_lbl.config(text=f"{cpu}%")

        # RAM
        ram = psutil.virtual_memory().percent
        self.ram_bar['value'] = ram
        self.ram_lbl.config(text=f"{ram}%")

        # Battery
        try:
            battery = psutil.sensors_battery()
            if battery:
                bat_pct = battery.percent
                self.bat_bar['value'] = bat_pct
                self.bat_lbl.config(text=f"{bat_pct}% {'(Charging)' if battery.power_plugged else ''}")
            else:
                self.bat_lbl.config(text="No Battery Detected")
        except Exception:
            pass

        try:
            import main
            if hasattr(main, 'autonomous_agent') and main.autonomous_agent:
                agent = main.autonomous_agent
                self.task_var.set(f"Task: {agent.goal[:35]}..." if len(agent.goal) > 35 else f"Task: {agent.goal}")
                self.agent_status_var.set(f"Status: {agent.state}")
                if agent.browser:
                    url = agent.browser.get_url()
                    self.url_var.set(f"URL: {url[:35]}..." if len(url) > 35 else f"URL: {url}")
                
                if agent.state == "EXECUTING":
                    self.agent_status_var.set("Status: EXECUTING...")
                elif agent.state == "WAITING_FOR_USER":
                    self.agent_status_var.set("Status: WAITING FOR INPUT")
        except Exception:
            pass

        # Schedule next update
        self.root.after(2000, self.update_metrics)

def start_dashboard():
    root = tk.Tk()
    app = JarvisDashboard(root)
    
    # Make sure app closes properly when user clicks X
    def on_closing():
        import os
        os._exit(0)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    root.mainloop()

if __name__ == "__main__":
    start_dashboard()
