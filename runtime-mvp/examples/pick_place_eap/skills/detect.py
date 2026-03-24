import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import time


def run():
    print("[Skill]    Scanning workspace with RGB-D camera...")
    time.sleep(0.3)
    print("[Skill]    Detected: red_cup at (0.35, 0.12, 0.08)")
    return {"status": "success"}
