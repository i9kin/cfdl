import glob
from os import system

import isort

files = glob.glob("*.py") + glob.glob("codeforces2html/*.py")

for file in files:
    isort.file(file)
system("black . --line-length 79")
