import keyboard
import unicodedata
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

# ---------- CONFIG ----------
TYPE_KEY = "f9"   # toggle typing on/off (with F9 by default to avoid conflict with F8 stop-all)
STOP_ALL = "f8"   # stop everything and exit
# set all to 0 for max speed; adjust to add human-like delays
SPEED_MIN = 0.15  # lower = faster (seconds per char) 
SPEED_MAX = 0.11  # upper bound for random delay to simulate human typing
PUNCT_MIN = 0.18  # punctuation delay (longer than normal to simulate human hesitation on punctuation)
PUNCT_MAX = 0.12  # upper bound for punctuation delay
# ----------------------------

# shared state
full_text = ""
static_type = False  
SCAN_KEY = "f7"         # typing enabled/disabled (toggle)
scan_trigger = th.Event()
stop_event = th.Event()
type_trigger = th.Event()

# Selenium setup
driver_path = ChromeDriverManager().install()
service = Service(driver_path)
driver = webdriver.Chrome(service=service)
driver.get("https://play.typeracer.com/")

# ----------------- control callbacks -----------------
def stop_everything():
    print("Stopping... (F8 pressed)")
    stop_event.set()
    try:
        driver.quit()
    except Exception:
        pass

def toggle_typing_cb():
    global static_type
    static_type = not static_type
    print("Typing toggle ->", static_type)
    # if toggled on and there's already text available, trigger typing
    if static_type and full_text:
        type_trigger.set()

def trigger_scan_cb():
    print("Manual scan triggered (F7)")
    scan_trigger.set()

keyboard.add_hotkey(SCAN_KEY, trigger_scan_cb)
keyboard.add_hotkey(STOP_ALL, stop_everything)
keyboard.add_hotkey(TYPE_KEY, toggle_typing_cb)

# ----------------- helper functions -----------------
def safe_find_text(xpath):
    """Try to find element text; return '' if not found."""
    try:
        el = driver.find_element(By.XPATH, xpath)
        return el.text or ""
    except Exception:
        return ""

def wait_for_element(xpath, timeout=10):
    """Return element or raise."""
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

def press_key(vk, shift=False):
    """Press and release a vk code, with optional shift wrapper."""
    try:
        if shift:
            win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
            time.sleep(0.002)
        # key down
        win32api.keybd_event(vk, 0, 0, 0)
        time.sleep(0.003)
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



# ----------------- text normalizer -----------------

def normalize_text(txt):
    # Normalize and remove zero-width / weird spaces
    txt = unicodedata.normalize("NFC", txt)
    txt = txt.replace("\u200b", "").replace("\u00a0", " ")
    return txt.strip()


# ----------------- threads -----------------

# Each tuple is (FIRST_LETTER_XPATH, REST_XPATH, REMAINING_XPATH)
XPATH_SETS = [
    # online match layout
    ('//*[@id="gwt-uid-21"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[1]',
     '//*[@id="gwt-uid-21"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[2]',
     '//*[@id="gwt-uid-21"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[3]'),
    # computer/opponent layout
    ('//*[@id="gwt-uid-20"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[1]',
     '//*[@id="gwt-uid-20"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div/span[2]',
     '//*[@id="gwt-uid-20"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div/span[3]'),
    # solo match layout (same as computer/opponent but with different span indexing)
    ('//*[@id="gwt-uid-20"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[1]',
     '//*[@id="gwt-uid-20"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[2]',
     '//*[@id="gwt-uid-20"]/table/tbody/tr[2]/td/table/tbody/tr[1]/td/table/tbody/tr[1]/td/div/div[1]/span[3]'),
]


def find_working_xpath_set():
    """
    Try each triple in XPATH_SETS and return the first that appears to have useful span text.
    Quick check uses find_elements (fast, non-blocking). Returns index and the triple, or (None, None).
    """
    for idx, (x_first, x_rest, x_rem) in enumerate(XPATH_SETS):
        try:
            # check if first xpath yields any element; if not, this set likely doesn't match the current layout
            els = driver.find_elements(By.XPATH, x_first)
            if not els:
                continue
            # if first xpath found, check if rest or rem have text to confirm this set is correct (robust to some layout variations)
            rest_found = bool(driver.find_elements(By.XPATH, x_rest))
            rem_found = bool(driver.find_elements(By.XPATH, x_rem))

            # if we found the first element and at least one of the rest/rem elements, this set is likely correct; return it
            parent = None
            try:
                parent = els[0].find_element(By.XPATH, "..")
            except Exception:
                parent = None

            if parent:
                spans = parent.find_elements(By.TAG_NAME, "span")
                if len(spans) >= 1:
                    for s in spans:
                        txt = (s.text or "").strip()
                        if txt:
                            return idx, (x_first, x_rest, x_rem)
            # fallback: if we found the first element and at least one of the rest/rem elements, this set is likely correct; return it
            if rest_found or rem_found:
                return idx, (x_first, x_rest, x_rem)
        except Exception:
            continue
    return None, None


def get_text_thread():
    global full_text
    while not stop_event.is_set():
        try:
            # --- wait for either auto-scan OR manual trigger ---
            if not scan_trigger.is_set():
                # normal auto-scan pacing
                time.sleep(0.2)
            else:
                # manual scan overrides, reset immediately
                scan_trigger.clear()

            # pick a working xpath set for the current page/race
            set_index, triple = find_working_xpath_set()
            if triple is None:
                time.sleep(0.2)
                continue
            x_first, x_rest, x_rem = triple

            # Wait for first-letter element to appear (short timeout)
            try:
                el = wait_for_element(x_first, timeout=6)
            except Exception:
                # If the explicit first xpath didn't appear in time, give up this loop iteration
                time.sleep(0.1)
                continue

            # find parent container for spans (prefer stable parent)
            parent = None
            try:
                # common pattern: go up a couple levels to the containing div for spans
                parent = el.find_element(By.XPATH, "./ancestor::div[1]")
            except Exception:
                parent = el

            # extract text from all spans under the parent container; this is more robust to layout changes than relying on specific xpaths for rest/rem
            spans = parent.find_elements(By.TAG_NAME, "span")
            span_texts = []
            for i, s in enumerate(spans, start=1):
                txt = s.text or s.get_attribute("textContent") or ""
                txt = txt.replace("\u00a0", " ").strip()
                if txt:
                    span_texts.append(txt)

            # If the triple matched but span_texts empty, attempt direct XPATH reads
            if not span_texts:
                a = safe_find_text(x_first)
                b = safe_find_text(x_rest)
                c = safe_find_text(x_rem)
                # assemble while avoiding duplicates
                parts = []
                if a:
                    parts.append(a)
                if b:
                    # if b starts with a (duplicate) skip a 
                    if parts and b.startswith(parts[-1]):
                        parts[-1] = b
                    else:
                        parts.append(b)
                if c:
                    parts.append(c)
                combined = " ".join(parts).replace("\n", " ").strip()
                full_text = combined
            else:
                # smart joining: if first span is 1-char and second continues word, merge without space
                if len(span_texts) >= 2 and len(span_texts[0]) == 1:
                    second = span_texts[1]
                    if second and (second[0].isalnum() or second[0] in "‹›«»'\"“”`"):
                        merged = span_texts[0] + second
                        rest = span_texts[2:]
                        parts = [merged] + rest
                        full_text = " ".join(parts)
                    else:
                        full_text = " ".join(span_texts)
                else:
                    full_text = " ".join(span_texts)

                full_text = full_text.replace("\n", " ").strip()

            print("Captured text (auto-set idx={}): {}".format(set_index, repr(full_text)))

            # trigger typing if enabled
            if full_text and static_type:
                type_trigger.set()

            # wait for race to end (first-letter disappears) or stop 
            while not stop_event.is_set():
                try:
                    driver.find_element(By.XPATH, x_first)
                    time.sleep(0.25)
                except Exception:
                    break

        except Exception as e:
            print("get_text_thread ERROR (multi-xpath):", e)
            time.sleep(0.5)




def typing_thread():
    """Wait for trigger; focus input box, then type the captured text."""
    global full_text
    while not stop_event.is_set():
        # Wait for trigger; timeout so we can check stop_event regularly
        triggered = type_trigger.wait(timeout=0.2)
        if stop_event.is_set():
            break
        if not triggered:
            continue

        # if typing not enabled, clear and continue
        if not static_type:
            type_trigger.clear()
            continue

        # grab snapshot of text
        text_to_type = full_text
        if not text_to_type:
            type_trigger.clear()
            continue

        # focus input box before typing
        try:
            # try class name 'txtInput' first; fallback to provided XPath input if available
            try:
                input_el = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "txtInput"))
                )
            except Exception:
                # try an input xpath fallback
                try:
                    input_el = driver.find_element(By.XPATH, '//*[@id="gwt-uid-21"]/table/tbody/tr[2]/td/table/tbody/tr[2]/td/input')
                except Exception:
                    input_el = None

            if input_el is not None:
                try:
                    input_el.click()
                    time.sleep(0.02)
                except Exception:
                    pass
            else:
                # if we can't focus via selenium, print warning and still attempt typing (user must focus) 
                print("Warning: couldn't find input to focus; ensure input is focused manually.")
                time.sleep(0.05)

            # do the low-level typing
            press_char_sequence(text_to_type)

        except Exception as e:
            print("typing error:", e)

        # clear after typing and clear trigger
        full_text = ""
        type_trigger.clear()

# ----------------- start -----------------
t1 = th.Thread(target=get_text_thread)   
t2 = th.Thread(target=typing_thread)
t3 = th.Thread(target=lambda: None)  # placeholder so we can join a list consistently 
# start toggle handled by hotkey callback; no thread needed for it but we can still join on it for clean exit

t1.start()
t2.start()

try:
    # main loop: keep alive until stop pressed or Ctrl+C; threads will check stop_event to exit cleanly
    while not stop_event.is_set():
        time.sleep(0.5)
except KeyboardInterrupt:
    stop_everything()

# join threads for clean exit (typing and get_text will check stop_event and exit; toggle has no thread but we can still join on it for consistency)
stop_event.set()
t1.join(timeout=2)
t2.join(timeout=2)
t3.join(timeout=2)
try:
    driver.quit()
except Exception:
    pass
print("Exited cleanly.")
