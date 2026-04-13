import os
import time
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "scenario_logs")
CURRENT_LOG_FILE = None

def init_scenario_run():
    global CURRENT_LOG_FILE
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"scenario_run_{timestamp_str}.txt"
    CURRENT_LOG_FILE = os.path.join(LOG_DIR, filename)

    with open(CURRENT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write(f"SCENARIO TEST RUN STARTED AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("================================================================================\n")

def log_scenario_step(scenario_name, step_desc, expected, actual, is_correct, start_time):
    global CURRENT_LOG_FILE
    
    duration = (time.time() - start_time) * 1000
    status = "[PASS]" if is_correct else "[FAIL]"
    
    print(f"\n--- {scenario_name} ---")
    print(f" > Step     : {step_desc}")
    print(f" > Expected : {expected}")
    print(f" > Actual   : {actual}")
    print(f" > Result   : {status} -- Took {duration:.2f} ms")
    
    if not CURRENT_LOG_FILE:
        init_scenario_run()

    with open(CURRENT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{status}] --- {scenario_name} ---\n")
        f.write(f"  > Step        : {step_desc}\n")
        f.write(f"  > Expected    : {expected}\n")
        f.write(f"  > Actual      : {actual}\n")
        f.write(f"  > Time        : {duration:.2f} ms\n")
        f.write("-" * 80 + "\n")
