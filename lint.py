import glob
from os import system

files = glob.glob("*.py") + glob.glob("cfdl/*.py")
system("python3 -m black . --line-length 79")
for file in files:
    # system(f"python3 -m pybetter {file}")
    system(f"python3 -m isort {file}")

__all__ = ["files"]
