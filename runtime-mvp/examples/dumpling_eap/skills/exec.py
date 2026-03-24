import time


def run():
    steps = [
        ("Picking up dough", 0.2),
        ("Wrapping filling", 0.3),
        ("Shaping dumpling", 0.2),
        ("Placing on tray", 0.1),
    ]
    for step, delay in steps:
        print(f"[Skill]    {step}...")
        time.sleep(delay)
    print("[Skill]    Dumpling complete.")
