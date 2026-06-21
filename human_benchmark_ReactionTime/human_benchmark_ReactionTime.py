import time
import threading
import keyboard
import win32api, win32con
import mss

# CONFIG
# Note Adjusting X and Y to match the target position on your screen is crucial for this to work correctly.
# The TARGET_GREEN color should also be verified with a color picker tool to ensure it matches the exact shade used in the benchmark.
X, Y = 489, 409
TARGET_GREEN = (75, 219, 106)
TOGGLE_KEY = "f9" 
static = True

# Toggle thread
def toggle_static():
    global static
    prev = False
    while True:
        curr = keyboard.is_pressed(TOGGLE_KEY)
        if curr and not prev:
            static = not static
        prev = curr
        time.sleep(0.0001)  # very tight polling

# Fast click function
def click_loop():
    global static
    sct = mss.mss()
    region = {"top": Y, "left": X, "width": 1, "height": 1}
    while True:
        if not static:
            continue
        pixel = sct.grab(region).pixel(0, 0)
        if pixel[:3] == TARGET_GREEN:
            win32api.SetCursorPos((X, Y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)

# Status printing thread
def print_status():
    global static
    while True:
        print("Static status:", static)
        time.sleep(0.1)  # prints every 100ms

# Start threads
threading.Thread(target=toggle_static, daemon=True).start()
threading.Thread(target=click_loop, daemon=True).start()
threading.Thread(target=print_status, daemon=True).start()

# Keep main thread alive
while True:
    time.sleep(1)
