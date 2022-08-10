import os
import pathlib

ROOT_PATH = pathlib.Path(__file__).parent.resolve().parent.resolve()

# Parent folder for all data
# Not added to git
DATA_PATH = os.path.join(ROOT_PATH, "data")
if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)

LOGS_PATH = os.path.join(ROOT_PATH, "logs")
if not os.path.exists(LOGS_PATH):
    os.mkdir(LOGS_PATH)
