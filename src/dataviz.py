import os

import pandas as pd
from nltk import ngrams
from wordcloud import WordCloud
from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns

from constants import *

# -----------------------------------------------------------------------------

with open(os.path.join(DATA_PATH, "2021AB_SN", "SG"), "r") as f:
    group_df = pd.read_csv(f, sep="|", header=None)

full_names = {}
for abbrev, name in group_df[[0, 1]].itertuples(index=False):
    if abbrev not in full_names.keys():
        full_names[abbrev] = name.upper()

# -----------------------------------------------------------------------------

total_distrib = {}
tokens = []

for filename in os.listdir(ARTICLES_PATH):

    with open(os.path.join(ARTICLES_PATH, filename, "entities.csv"), "r") as f:
        entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    for i, v in entities_df["Type"].value_counts().iteritems():
        if i == "ENTITY":
            i = "UNDEF"
        elif i in full_names.keys():
            i = full_names[i]
        if i not in total_distrib.keys():
            total_distrib[i] = v
        else:
            total_distrib[i] += v

    tokens += list(entities_df["Word"].astype(str).values)

list_distrib = []
for name, v in total_distrib.items():
    list_distrib.append({"group": name, "frequency": v})

counted = Counter(tokens)
counted_2 = Counter(ngrams(tokens, 2))
counted_3 = Counter(ngrams(tokens, 3))

word_freq = pd.DataFrame(counted.items(), columns=['word', 'frequency']).sort_values(by='frequency', ascending=False)
word_pairs = pd.DataFrame(counted_2.items(),columns=['pairs', 'frequency']).sort_values(by='frequency', ascending=False)
trigrams = pd.DataFrame(counted_3.items(), columns=['trigrams', 'frequency']).sort_values(by='frequency', ascending=False)

# -----------------------------------------------------------------------------

plt.figure(figsize=(9,5))
sns.barplot(x='frequency', y='group', data=pd.DataFrame(list_distrib))

plt.figure(figsize=(9,5))
sns.barplot(x='frequency',y='word',data=word_freq.head(40))

plt.figure(figsize=(9,5))
sns.barplot(x='frequency',y='pairs',data=word_pairs.head(20))

plt.figure(figsize=(9,5))
sns.barplot(x='frequency',y='trigrams',data=trigrams.head(20))

clean_words_string = " ".join(tokens)
wordcloud = WordCloud(background_color="white").generate(clean_words_string)

plt.figure(figsize = (12, 8))
plt.imshow(wordcloud)

plt.axis("off")
plt.show()
