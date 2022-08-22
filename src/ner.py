import os
import time
import re
from tqdm.auto import tqdm

import pandas as pd
import spacy
import scispacy
from scispacy.linking import EntityLinker
from scispacy.abbreviation import AbbreviationDetector

from constants import *

import warnings
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------

# Manual Models
# Matches an entity type directly to a text pattern.
# Use it for very specific expressions


def names_et_al(text):
    """
    Catches the "NAME et al." mentions in the text, to label the name efficiently
    """
    pat = r"[A-Z][a-z][a-zA-Z]( [A-Z])? et al\.?"
    entity_type = "PERSON"
    return re.findall(pat, text), entity_type

# -----------------------------------------------------------------------------


def get_entities_from_spacy(text, model, name, filename):
    """
    Uses a spacy model to return all entities found
    """
    doc = model(text)
    entities = list(doc.ents)
    entities.sort(key=lambda x: x.start_char)

    entities_list = []
    try:
        linker = model.get_pipe("scispacy_linker")
        scispacy_m = True
    except:
        linker = None
        scispacy_m = False

    for ent in entities:
        word = ent.lemma_
        e_type = ent.label_
        source = name
        start_char = ent.start_char
        end_char = ent.end_char
        document = filename.split('.')[0]
        try:
            CUI, score = ent._.kb_ents[0]
        except:
            CUI, score = None, None
        if CUI and score:
            TUI = re.search(r"T[0-9]{3}", str(linker.kb.cui_to_entity[CUI]))[0]
            e_type, group = None, None
            e_type = TUI_MAP[TUI]
            group = TUI_MAP[TUI]
        else:
            TUI, group = None, None

        entities_list.append({"Word": word,
                              "Type": e_type,
                              "CUI": CUI,
                              "Document": document,
                              "StartChar": start_char,
                              "EndChar": end_char})

    return entities_list


def get_entities_from_manual(text, model, name, filename):
    """
    Uses a manual model to return all entities found
    Manual modesl are defined using the above scheme
    """
    words_list, e_type = model(text)

    entities_list = []

    for word in words_list:
        source = name
        start_char, end_char = re.search(word, text).span()
        document = filename.split('.')[0]
        entities_list.append({"Word": word,
                              "Type": e_type,
                              "CUI": None,
                              "Document": document,
                              "StartChar": start_char,
                              "EndChar": end_char})

    entities_list.sort(key=lambda x: x["StartChar"])
    return entities_list


def build_merged_entities_df(filename, ner_models):
    """
    Merges all results from all models to create a final dataframe of entities
    """
    with open(os.path.join(ARTICLES_PATH, filename, "clean.txt"), "r") as f:
        text = f.read()

    entities_df = pd.DataFrame()
    seen = [0] * len(text)

    for model in ner_models:
        model_type = model["type"]
        model_name = model["name"]
        model_prio = model["prio"]
        model_nlp = model["model"]
        if model_type == "Spacy":
            entities_list = get_entities_from_spacy(text, model_nlp, model_name, filename)
        elif model_type == "Manual":
            entities_list = get_entities_from_manual(text, model_nlp, model_name, filename)
        else:
            raise NotImplementedError(f"Model type {model_type} is unknown.")

        if len(entities_df) > 0:
            good_entities = []
            for ent in entities_list:
                if sum(seen[ent["StartChar"]:ent["EndChar"]]) == 0:
                    good_entities.append(ent)
                    seen[ent["StartChar"]:ent["EndChar"]] = [1] * (ent["EndChar"] - ent["StartChar"])
            entities_df = pd.concat([entities_df, pd.DataFrame(good_entities)])
        else:
            for ent in entities_list:
                seen[ent["StartChar"]:ent["EndChar"]] = [1] * (ent["EndChar"] - ent["StartChar"])
            entities_df = pd.DataFrame(entities_list)

    if len(entities_df) != 0:
        entities_df = entities_df.sort_values(by=["Document", "StartChar"], axis=0).reset_index(drop=True)

    text = re.sub("[^a-zA-Z0-9\.]", " ", text)

    if len(entities_df) > 0:
        cursor = 0
        cnt_words = 0
        cnt_sentences = 0
        words_dicts = []
        for word, start_char, end_char in list(entities_df[["Word", "StartChar", "EndChar"]].itertuples(index=False, name=None)):
            cnt_words += sum([len(a) > 0 for a in text[cursor:start_char].split(" ")])
            cnt_sentences += sum([a == "." for a in text[cursor:start_char]])
            start_id = cnt_words
            sentence_id = cnt_sentences
            num_words = sum([len(a) > 0 for a in word.split(" ")])
            end_id = start_id + num_words - 1
            cnt_words += num_words
            words_dicts.append({"Word": word, "StartWord": start_id, "EndWord": end_id, "Sentence": sentence_id})
            cursor = end_char
        words_df = pd.DataFrame(words_dicts)

        entities_df = pd.concat([entities_df, words_df[["StartWord", "EndWord", "Sentence"]]], axis=1)

    return entities_df

# -----------------------------------------------------------------------------


nlp_scispacy = spacy.load("en_core_sci_md")
nlp_scispacy.add_pipe("abbreviation_detector")
nlp_scispacy.add_pipe("scispacy_linker", config={"resolve_abbreviations": True,
                      "linker_name": "umls", "max_entities_per_mention": 1})

ner_models = [
    {"type": "Spacy", "name": "SciSpacy MD", "prio": 0, "model": nlp_scispacy},
    {"type": "Spacy", "name": "Spacy SM", "prio": 1, "model": spacy.load("en_core_web_md")},
    {"type": "Manual", "name": "Names et al.", "prio": -1, "model": names_et_al}
]

ner_models.sort(key=lambda x: x["prio"])

for filename in tqdm(os.listdir(ARTICLES_PATH)):

    entities_df = build_merged_entities_df(filename, ner_models)
    entities_df.fillna(value="UNDEF", inplace=True)

    if len(entities_df) != 0:
        with open(os.path.join(ARTICLES_PATH, filename, "entities.csv"), "wb") as f:
            entities_df.to_csv(f)
