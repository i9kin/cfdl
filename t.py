from os import system

from cfdl import cli

step = 1

for i in range(3, 0, -step):
    system("clear")
    print(i, "start")
    cli.download([f"{i - step + 1}-{i}"], debug=True)
    # system(f"python3 -m cfdl download {i - step + 1}-{i}")
    print("asdsad")


__all__ = ["step"]
