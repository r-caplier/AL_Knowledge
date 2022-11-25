import os
import pandas as pd

import torch
from transformers import AutoTokenizer, AutoModel

from tqdm.auto import tqdm

from constants import *

sentences_list = []

for filename in os.listdir(ARTICLES_PATH):

    with open(os.path.join(ARTICLES_PATH, filename, "entities.csv"), "r") as f:
        entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1).dropna()
        doc_sentences_raw = entities_df.groupby("Sentence")["Word"].agg(lambda x: " ".join(x))
        doc_sentences = [''.join([c for c in s if c.isalpha() or c == " " or c == "-"]).strip() for s in doc_sentences_raw]
        doc_sentences = [s for s in doc_sentences if len(s) > 0]

        sentences_dict = {}
        sentences_dict["Document"] = filename
        sentences_dict["Sentences"] = doc_sentences

        sentences_list.append(sentences_dict)

sentences_df = pd.DataFrame(sentences_list)
sentences_df["Len"] = sentences_df["Sentences"].apply(lambda x: len(x))

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")

sentences_encodings = []

for i in tqdm(range(len(sentences_df))):

    inputs = tokenizer(sentences_df.iloc[i]["Sentences"], return_tensors="pt", padding="max_length", max_length=100)
    outputs = model(**inputs)
    encoding = outputs.last_hidden_state

    sentences_encodings.append(encoding)

with open(os.path.join(DATA_PATH, 'encodings.pkl'), "rb") as f:
    pickle.dump(sentences_encodings, f)
