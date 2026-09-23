import os
import datetime
import subprocess
import ctypes
import pyautogui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc

# ─────────────────────────────────────────────
#  VOLUME CONTROL
# ─────────────────────────────────────────────
def get_volume_interface():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))

def set_volume(level):
    volume = get_volume_interface()
    scalar = max(0.0, min(1.0, level / 100.0))
    volume.SetMasterVolumeLevelScalar(scalar, None)

def get_volume():
    volume = get_volume_interface()
    return int(volume.GetMasterVolumeLevelScalar() * 100)

def change_volume(delta):
    current = get_volume()
    new_level = max(0, min(100, current + delta))
    set_volume(new_level)
    return new_level

def toggle_mute(mute=None):
    volume = get_volume_interface()
    if mute is None:
        current = volume.GetMute()
        volume.SetMute(not current, None)
    else:
        volume.SetMute(mute, None)

# ─────────────────────────────────────────────
#  BRIGHTNESS CONTROL
# ─────────────────────────────────────────────
def set_brightness(level):
    sbc.set_brightness(level)

def get_brightness():
    return sbc.get_brightness()[0]

# ─────────────────────────────────────────────
#  SCREENSHOT
# ─────────────────────────────────────────────
def take_screenshot():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.png"
    filepath = os.path.join(desktop, filename)
    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    return filepath

# ─────────────────────────────────────────────
#  POWER CONTROLS
# ─────────────────────────────────────────────
def shutdown_computer():
    subprocess.Popen("shutdown /s /t 10", shell=True)

def cancel_shutdown():
    subprocess.Popen("shutdown /a", shell=True)

def restart_computer():
    subprocess.Popen("shutdown /r /t 10", shell=True)

def lock_screen():
    ctypes.windll.user32.LockWorkStation()

def sleep_computer():
    subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
