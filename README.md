# Web Automation and Reflex Benchmarking Suite

A comprehensive collection of Python automation utilities designed to interface with online skill tests and competitive typing platforms. This suite demonstrates multi-threading synchronization, low-level OS input simulation, high-frequency frame buffer sampling, and dynamic document object model (DOM) parsing.

---

## Directory Navigation
* [1. Reaction Time Automator (`human_benchmark_ReactionTime`)](#1-reaction-time-automator)
* [2. Human Benchmark Typer (`human_benchmark_typer`)](#2-human-benchmark-typer)
* [3. TypeRacer Bypass Bot (`typeracer_bot`)](#3-typeracer-bypass-bot)
* [4. Global Environment Setup](#4-global-environment-setup)

---

## 1. Reaction Time Automator

### Folder Allocation
`/human_benchmark_ReactionTime/`

### File Component
* `human_benchmark_ReactionTime.py`

### Project Overview
This module isolates frame-buffer monitoring loops to eliminate standard software rendering overhead, executing hardware-level click commands the exact millisecond a target color change is detected on screen.

### Core Architecture and Mechanics
The script leverages the `mss` library to perform high-frequency pixel polling on a specified coordinate rather than processing full screenshots, minimizing CPU overhead. The program monitors the memory array of the screen slice. The instant the RGB values shift to match the target color signature of the site's green screen, the main loop ceases polling and issues immediate mouse click states using direct Windows User32 API structures (`win32api`). This bypasses virtual pointer layers and mouse event queues, reducing reaction delay to near-zero milliseconds.

### Manual Configuration
Before running the bot, you must define the target box position to match your active monitor resolution:
1. Open `human_benchmark_ReactionTime.py`.
2. Locate the configuration lines:
   X, Y = 489, 409
   TARGET_GREEN = (75, 219, 106)
3. Update the `X` and `Y` integers to target the center of the color-changing canvas on your display panel.

### Script Execution and Detailed Usage
1. Navigate to the script subfolder:
   `cd human_benchmark_ReactionTime`
2. Install the targeted environment requirements:
   `pip install -r requirements.txt`
3. Execute the module:
   `python human_benchmark_ReactionTime.py`
4. **Runtime Operations:**
   * Open the target benchmark link in your browser window.
   * Press `F9` to toggle the active monitoring thread on or off. 
   * Click the screen manually to begin the test sequence, then let the background loop handle subsequent color changes.

---

## 2. Human Benchmark Typer

### Folder Allocation
`/human_benchmark_typer/`

### File Component
* `human_benchmark_typer.py`

### Project Overview
An automated input wrapper that extracts text content from active browser DOM frames and offloads typing tasks to an independent worker thread configured with variable entry pacing.

### Core Architecture and Mechanics
The utility uses Selenium WebDriver to initialize a managed automated browser instance and load the testing platform. Once initialized, the main script utilizes explicit XPath tracking to look up the textual prompt block elements from the page framework. 

To ensure the browser application remain responsive and to prevent input blocking, the captured string payload is transferred to a detached thread worker. This background thread loops through the string character by character, translating symbols into Windows Virtual Key Codes. To simulate realistic manual typing profiles, the thread applies random timing offsets via `random.uniform()`, injecting tight delays between alphanumeric keys and prolonged pauses after special punctuation markers.

### Script Execution and Detailed Usage
1. Navigate to the script subfolder:
   `cd human_benchmark_typer`
2. Install the necessary dependency binaries:
   `pip install -r requirements.txt`
3. Execute the script module:
   `python human_benchmark_typer.py`
4. **Runtime Operations:**
   * The script will spin up an automated Chrome instance navigating directly to the typing test.
   * Press `F7` to trigger the DOM scrapper to parse and pull the active text block into memory.
   * Press `F9` to toggle the background input thread, allowing it to begin injecting text into the target box.
   * Press `F8` at any time to actuate an emergency system override, killing active thread iterations and closing the open browser processes safely.

---

## 3. TypeRacer Bypass Bot

### Folder Allocation
`/typeracer_bot/`

### File Component
* `typeracer_bot.py`

### Project Overview
An advanced automation tool built to handle changing document layouts, hidden string tokens, and keyboard layout translation mismatches on competitive gamified platforms.

### Core Architecture and Mechanics
Platforms like TypeRacer regularly shuffle text box element properties to deter simple automation. This application uses an array of fallback XPaths, checking multiple target configurations to find the correct text container. 

Once retrieved, the text goes through a regex cleaning pipeline that strips hidden zero-width space characters (`\u200b`) and non-breaking spaces (`\u00a0`), preventing layout tracking bugs. The input module maps elements via standard hardware scan codes. If a special symbol or localized character cannot be resolved by the active keyboard driver, the script copies that specific character into the Windows clipboard memory ring, sending a direct hardware paste sequence (`Ctrl + V`) via low-level virtual key events to ensure zero missed characters.

### Script Execution and Detailed Usage
1. Navigate to the designated subfolder path:
   `cd typeracer_bot`
2. Install the subfolder module requirements:
   `pip install -r requirements.txt`
3. Run the automation program:
   `python typeracer_bot.py`
4. **Runtime Operations:**
   * A clean Chrome browser instance will open automatically and load the typing workspace.
   * Enter a live or solo racing lobby.
   * The tracking script will attempt to scrape text automatically. If a custom web template layout blocks this, press `F7` to force a manual DOM scan override.
   * Press `F9` to enable the typing injection engine when the race countdown timer reaches zero.
   * Press `F8` to stop execution instantly if an application error occurs or if you need to close out the browser session.

---

## 4. Global Environment Setup

### Infrastructure Prerequisites
These automation utilities require a **Windows OS Platform** due to their core architectural dependencies on native Win32 system binaries and direct hardware execution hooks.

### Local Dependency Isolation
To run any tool in this suite, navigate into its designated subfolder and install its isolated dependencies using the project's local manifest file:
`pip install -r requirements.txt`

## License
Distributed under the terms of the open-source MIT License.