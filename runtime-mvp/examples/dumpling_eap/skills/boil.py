import time


def run():
    print("[Skill]    Placing dumpling in pot...")
    time.sleep(0.2)
    print("[Skill]    Boiling for 8 minutes...")
    time.sleep(0.3)
    print("[Skill]    Dumpling cooked and ready to serve.")
    return {"status": "success"}
