import os
import argparse

import spacy
import numpy as np
import pandas as pd

from termcolor import colored

from constants import *


def get_color_map_types(entities_df):

    colors = ["red", "blue", "green", "yellow", "magenta", "cyan", "grey", "white"]

    types_to_color = {}
    cnt = 0
    for type_ent in list(entities_df["Type"].value_counts().index):
        # try:
        #     types_to_color[type_ent] = colors[cnt]
        # except:
        #     types_to_color[type_ent] = None
        # cnt += 1
        if len(type_ent) == 4 or type_ent == "ENTITY":
            try:
                types_to_color[type_ent] = colors[cnt]
            except:
                types_to_color[type_ent] = None
            cnt+=1
        else:
            types_to_color[type_ent] = None

    return types_to_color


def print_entity_types(text, entities_df, no_color=False):

    color_map = get_color_map_types(entities_df)
    colored_text = ""
    last_end = 0

    for i in range(len(entities_df)):
        start = entities_df.iloc[i]["StartChar"]
        end = entities_df.iloc[i]["EndChar"]
        e_type = entities_df.iloc[i]["Type"]
        if last_end <= start:
            if no_color:
                color_e = "white"
            else:
                color_e = color_map[e_type]
            colored_text += text[last_end:start] + colored(text[start:end], color_e)
            last_end = end
        elif last_end > start and last_end < end:
            colored_text += colored(text[last_end:end], color_map[e_type])
            last_end = end
    if last_end != len(text):
        colored_text += text[last_end:]

    print(colored_text)

    for k, v in color_map.items():
        print(colored(k, v))


# filename corresponds to the id of the article, like it appears on PubMed or in the data folder
parser = argparse.ArgumentParser(description="Displays entities found in a colored fashion")
parser.add_argument("--filename", help="Name of the file to display")

args = parser.parse_args()
filename = args.filename

with open(os.path.join(ARTICLES_PATH, filename, "clean.txt"), "r") as f:
    text = f.read()

with open(os.path.join(ARTICLES_PATH, filename, "entities.csv"), "r") as f:
    entities_df = pd.read_csv(f)

print_entity_types(text, entities_df)
