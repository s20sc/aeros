import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.agent import Agent
from eap.loader import load_eap


def main():
    agent = Agent()

    eap_path = os.path.join(os.path.dirname(__file__), "examples", "dumpling_eap")
    load_eap(eap_path)

    print("\nEAPOS Runtime v0.1")
    print('Type a command (or "exit" to quit)\n')

    while True:
        try:
            instruction = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if instruction.strip() == "exit":
            break
        if not instruction.strip():
            continue
        agent.run(instruction)


if __name__ == "__main__":
    main()
