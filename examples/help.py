import subprocess
import sys
import time

command = sys.argv[1]


PROMPT = "❯"


def slowprint(s):
    print(s)
    time.sleep(0.05)


def show(command, execute=True):
    print(PROMPT, end=" ")
    slowprint(command)
    if execute:
        start = time.time()
        subprocess.call("python3 -m " + command, shell=True)
        print(f"took {int(time.time()  - start)}s")


if command == "download":
    show("cfdl download 1380A # download task")

    show("cfdl download 1380A --pdf # download task with pdf")
    show(
        "cfdl download 1371 # download one contest with submition in tutorial"
    )
# termtosvg examples/download.svg --command='python3 examples/help.py download' --screen-geometry=80x20 -t examples/window.svg
