import os
import pathlib
import pandas as pd

ROOT_PATH = pathlib.Path(__file__).parent.resolve().parent.resolve()

# Parent folder for all data
# Not added to git
DATA_PATH = os.path.join(ROOT_PATH, "data")
if not os.path.exists(DATA_PATH):
    os.mkdir(DATA_PATH)

LOGS_PATH = os.path.join(ROOT_PATH, "logs")
if not os.path.exists(LOGS_PATH):
    os.mkdir(LOGS_PATH)

ARTICLES_PATH = os.path.join(DATA_PATH, "articles")
if not os.path.exists(ARTICLES_PATH):
    os.mkdir(ARTICLES_PATH)

with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SG")) as f:
    df_group = pd.read_csv(f, delimiter='|', names=["Group Abbrev",
                           "Group Name", "TUI", "Semantic Type"], index_col=False)
TUI_MAP = {}
for i, infos in df_group[["Group Abbrev", "TUI"]].iterrows():
    TUI_MAP[infos["TUI"]] = infos["Group Abbrev"]
