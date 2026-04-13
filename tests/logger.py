import os
import time
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "test_logs")
# O anki test koşusuna (run) ait dosya yolunu global olarak tutacağız
CURRENT_LOG_FILE = None

def init_test_run():
    global CURRENT_LOG_FILE
    
    # "test_logs" klasörü yoksa oluştur
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    # Her pytest çalıştırıldığında timestamp ile benzersiz bir dosya oluştur
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"run_{timestamp_str}.txt"
    CURRENT_LOG_FILE = os.path.join(LOG_DIR, filename)

    with open(CURRENT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write("================================================================================\n")
        f.write(f"TEST RUN STARTED AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("================================================================================\n")

def log_step(test_name, input_desc, expected, actual, is_correct, start_time):
    global CURRENT_LOG_FILE
    
    duration = (time.time() - start_time) * 1000
    status = "[PASS]" if is_correct else "[FAIL]"
    
    # Ekrana yazdır (console output için)
    print(f"\n--- {test_name} ---")
    print(f" > Request  : {input_desc}")
    print(f" > Expected : {expected}")
    print(f" > Actual   : {actual}")
    print(f" > Result   : {status} -- Took {duration:.2f} ms")
    print("-" * 55)
    
    # Dosya oluşmamışsa (fail safe)
    if not CURRENT_LOG_FILE:
        init_test_run()

    # O anki koşuya özel dosyaya kaydet
    with open(CURRENT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"--- {test_name} ---\n")
        f.write(f"  > Input / Req : {input_desc}\n")
        f.write(f"  > Expected    : {expected}\n")
        f.write(f"  > Actual      : {actual}\n")
        f.write(f"  > Result      : {status} -- Took {duration:.2f} ms\n")
        f.write("-" * 80 + "\n")
