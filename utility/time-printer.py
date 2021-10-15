from datetime import datetime
from time import sleep, time
import sys

# FAKETIME_SAVE_FILE FAKETIME_LOAD_FILE

for _ in range(3):
    print(datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S %Z"))
    sys.stdout.flush()
    sleep(1)