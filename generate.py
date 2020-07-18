import os
import sys
import time

a = [["python3 cli.py --help"], "examples/cli_help.svg"]

PROMPT = "❯"


def slowprint(s):
    for c in s + "\n":
        sys.stdout.write(c)
        sys.stdout.flush()
        time.sleep(0.05)


def run(command):
    print(PROMPT, end=" ")
    slowprint(command)
    os.system(command)
    print()


command1 = "python3 codeforce --help"

run(command1)


__all__ = ["PROMPT", "a", "command1", "command2", "run", "slowprint"]

# termtosvg examples/help.svg --command='python3 examples/generate.py' --screen-geometry=80x20 -t examples/window.svg
