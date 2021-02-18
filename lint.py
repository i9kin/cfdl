import glob
from os import system

files = glob.glob("*.py") + glob.glob("cfdl/*.py")
for file in files:
    # isort.file(file)
    # system(f"pybetter {file}")
    system(f"isort {file}")
system("black . --line-length 79")
