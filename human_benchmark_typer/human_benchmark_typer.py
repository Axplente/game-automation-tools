import keyboard
import pyperclip
import win32api, win32con
import random
import threading as th
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#----------Configs----------
full_text = ""
static = False
static_type = False
type_pressed = False
previously_pressed = False
"F7 to fetch new text; F9 to toggle typing; F8 to stop everything and exit"
STOP_KEY = "f9"   # type toggle key
STOP_ALL = "f8"
# set all to 0 for max speed; adjust to add human-like delays
SPEED_MIN = 0.02  # lower = faster (seconds per char)
SPEED_MAX = 0.03  # upper bound for random delay to simulate human typing
PUNCT_MIN = 0.01  # punctuation delay (longer than normal to simulate human hesitation on punctuation)
PUNCT_MAX = 0.02  # upper bound for punctuation delay


#----------shared state----------
stop_event = th.Event()
type_trigger = th.Event()
full_text = ""
static_type = False
fetch_allowed = False


#----------XPath----------
FULL_TEXT_XPATH = '//*[@id="root"]/div/div[4]/div[1]/div/div[2]/div'


#----------Selenium setup----------
driver_path = ChromeDriverManager().install()
service = Service(driver_path)
driver = webdriver.Chrome(service=service)
driver.get("https://humanbenchmark.com/tests/typing")


#----------controll callback---------
def stop_everything():
    print("stopping... (f8 pressed)")
    stop_event.set()
    try:
        driver.quit()
    except Exception:
        pass


# ----------helper function to allow fetching----------
def trigger_fetch():
    global fetch_allowed
    fetch_allowed = True
    print("Fetch triggered")


#---------stop trigers--------
def toggle_typing_cb():
    global static_type
    static_type = not static_type
    print("Typing toggle ->", static_type)
    if static_type and full_text:
        type_trigger.set()
    
keyboard.add_hotkey(STOP_ALL, stop_everything)
keyboard.add_hotkey(STOP_KEY, toggle_typing_cb)


# ----------------- helper functions -----------------
def fetch_text_loop():
    global full_text, fetch_allowed
    while not stop_event.is_set():
        if not fetch_allowed:
            time.sleep(0.05)
            continue

        try:
            el = driver.find_element(By.XPATH, FULL_TEXT_XPATH)
            new_text = el.text
            if new_text:
                full_text = new_text
                print("Fetched text:", repr(full_text))  # print after fetching
                if static_type:
                    type_trigger.set()
            fetch_allowed = False  # block further fetches until next trigger
        except Exception:
            pass

        time.sleep(0.05)


# ----------keyboard trigger to fetch----------
keyboard.add_hotkey("f7", trigger_fetch)  # press F7 to fetch new text



def wait_for_element(xpath, timeout=10):
    """Return element or raise."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))


#----------key presses----------
def press_key(vk, shift=False):
    """Press and release a vk code, with optional shift wrapper."""
    try:
        if shift:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        # key down
        win32api.keybd_event(vk, 0, 0, 0)
        # time.sleep(0.001) if it doesnt register correctly rremove the #
        # key up
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
    finally:
        if shift:
            time.sleep(0.001)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)

def press_char_sequence(text):
    """Type a text using VkKeyScan mapping; fallback to clipboard for unsupported characters."""
    for ch in text:
        if stop_event.is_set():
            return
        vk = win32api.VkKeyScan(ch)
        if vk == -1:
            # Character not in keyboard layout -> paste from clipboard
            pyperclip.copy(ch)
            time.sleep(0.01)  # tiny delay to ensure clipboard is ready

            # Ctrl+V paste
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            time.sleep(0.005)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            time.sleep(0.01)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.005)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)
        else:
            vk_code = vk & 0xff
            shift_state = (vk >> 8) & 0xff
            need_shift = (shift_state & 1) == 1
            press_key(vk_code, shift=need_shift)

        # tiny humanized delay
        if ch in " .,!?:;\"'":
            time.sleep(random.uniform(PUNCT_MIN, PUNCT_MAX))
        else:
            time.sleep(random.uniform(SPEED_MIN, SPEED_MAX))


#----------writer---------
def typing_thread():
    """Wait for trigger; focus input box, then type the captured text."""
    global full_text
    while not stop_event.is_set():
        triggered = type_trigger.wait(timeout=0.2)
        if stop_event.is_set():
            break
        if not triggered:
            continue

        # grab snapshot of text
        text_to_type = full_text
        if not text_to_type:
            type_trigger.clear()
            continue

        try:
            # focus input box before typing
            try:
                input_el = driver.find_element(By.CLASS_NAME, "txtInput")
                input_el.click()
            except Exception:
                print("Warning: couldn't find input to focus; please focus it manually.")

            press_char_sequence(text_to_type)

        except Exception as e:
            print("typing error:", e)

        # clear AFTER typing, always, so it won't re-type
        full_text = ""
        type_trigger.clear()


# ----------------- start -----------------
t1 = th.Thread(target=fetch_text_loop)
t2 = th.Thread(target=typing_thread)

t1.start()
t2.start()

try:
    # main loop: keep alive until stop pressed or Ctrl+C; threads will check stop_event to exit cleanly
    while not stop_event.is_set():
        time.sleep(0.5)
except KeyboardInterrupt:
    stop_everything()

# join threads for clean exit 
stop_event.set()
t1.join(timeout=2)
t2.join(timeout=2)
try:
    driver.quit()
except Exception:
    pass
print("Exited cleanly.")

