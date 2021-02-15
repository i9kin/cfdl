import glob
from os import system

import isort

files = glob.glob("*.py") + glob.glob("cfdl/*.py")
for file in files:
    # isort.file(file)
    system(f"pybetter {file}")
system("black . --line-length 79")


__all__ = ["files"]
