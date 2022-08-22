import os
import time
import re
from tqdm.auto import tqdm

import pandas as pd

from constants import *

# -----------------------------------------------------------------------------

MAX_DIST = 20

relations_dicts = []

# -----------------------------------------------------------------------------


with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SRSTRE1")) as f:
    umls_relations_df = pd.read_csv(f, delimiter='|', names=["FirstTUI", "RelationTUI", "EndTUI"], index_col=False)


def get_UMLS_score(StartTUI, EndTUI, startType, endType, umls_relations_df):
    if startType != "ENTITY" or endType != "ENTITY":
        return 1
    else:
        return len(umls_relations_df["RelationTUI"].loc[umls_relations_df["FirstTUI"]
                                                        == StartTUI].loc[umls_relations_df["EndTUI"] == EndTUI])

# -----------------------------------------------------------------------------


def build_relations_from_filename(filename):
    """
    Pairs all possible entities in the text
    Naively done for now - TODO: Lower the number of relations
    """
    with open(os.path.join(ARTICLES_PATH, filename, "entities.csv"), "r") as f:
        entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    relations_dicts = []

    for i in range(len(entities_df)):
        if entities_df.iloc[i]["Type"] not in ["ENTITY", "PERSON", "ORG"]:
            continue
        forward_df = entities_df.iloc[i + 1:].loc[entities_df["Sentence"] == entities_df.iloc[i]["Sentence"]]
        valid_relations = forward_df.loc[(forward_df["EndWord"] <= entities_df["StartWord"].iloc[i] +
                                          MAX_DIST) & (forward_df["Word"] != entities_df.iloc[i]["Word"])]
        for j in range(len(valid_relations)):
            if entities_df.iloc[i]["Word"] != entities_df.iloc[j]["Word"]:
                relations_dicts.append({"First": i,
                                        "End": i + j + 1,
                                        "FirstWord": entities_df.iloc[i]["Word"],
                                        "SecondWord": valid_relations.iloc[j]["Word"],
                                        "Sentence": entities_df.iloc[i]["Sentence"],
                                        "Document": entities_df.iloc[i]["Document"],
                                        "FirstType": entities_df.iloc[i]["Type"],
                                        "SecondType": valid_relations.iloc[j]["Type"],
                                        "FirstCUI": entities_df.iloc[i]["CUI"],
                                        "SecondCUI": valid_relations.iloc[j]["CUI"],
                                        "Distance": valid_relations.iloc[j]["StartWord"] - entities_df.iloc[i]["EndWord"]})

    return pd.DataFrame(relations_dicts)

# -----------------------------------------------------------------------------


for filename in tqdm(os.listdir(ARTICLES_PATH)):

    relations_df = build_relations_from_filename(filename)

    with open(os.path.join(ARTICLES_PATH, filename, "relations.csv"), "wb") as f:
        relations_df.to_csv(f)
