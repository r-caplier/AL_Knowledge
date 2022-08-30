import os
import time
import pandas as pd
from datetime import datetime

import pickle

import requests
from bs4 import BeautifulSoup

import networkx as nx
from pyvis.network import Network

from tqdm.auto import tqdm

from constants import *

search_terms = ["anastomotic", "leak"]
max_page_num = 1

# -----------------------------------------------------------------------------


def _pget(url, stream=False):
    """
    Acounts for network errors in   getting a request (Pubmed often appears offline, but not for long periods of time)
    Retries every 2 seconds for 60 seconds and then gives up
    """
    downloaded = False
    count = 0

    while not downloaded and count < 60:
        try:
            page = requests.get(url, stream=stream)
            downloaded = True
        except:
            print(url + f" - Network error, retrying... ({count + 1})")
            time.sleep(2)
            count += 1

    if page != None:
        return page
    else:
        raise ValueError

# -----------------------------------------------------------------------------


# Filtering out every non English match
search_url = "https://pubmed.ncbi.nlm.nih.gov/?term=" + '+'.join(search_terms) + '&filter=lang.english'
full_search_ids = []

# Grabs every page
page_num = 0
while (max_page_num and page_num < max_page_num) or not max_page_num:
    page_num += 1
    if page_num != 1:
        page_url = search_url + "&page=" + str(page_num)
    else:
        page_url = search_url
    try:
        page = _pget(page_url)
        page_soup = BeautifulSoup(page.text, features="lxml")
        page_ids = page_soup.find("div", {"class": "search-results-chunk results-chunk"}
                                  ).get("data-chunk-ids").split(",")
        full_search_ids += page_ids
    except AttributeError:
        break

with open(os.path.join(LOGS_PATH, "full_search_ids_anastomotic_leak.pkl"), "rb") as f:
    full_search_ids = pickle.load(f)

articles_list = []

for article_id in tqdm(full_search_ids[:50]):

    url = "https://pubmed.ncbi.nlm.nih.gov/" + str(article_id)

    with _pget(url) as r:
        soup = BeautifulSoup(r.text, "html.parser")

    citations_ids = []
    citedby = soup.find("div", {"class": "citedby-articles"})
    if citedby:
        for a in citedby.find_all("a", {"class": "docsum-title"}):
            citations_ids.append(a["data-ga-action"])

    try:
        date_text = soup.find("div", {"class": "article-source"}).find("span", {"class": "cit"}).text.split(";")[0]
        date_text = " ".join(date_text.split(" ")[:2])
        date = datetime.strptime(date_text, "%Y %b")
    except:
        date = "Undef"

    articles_list.append({"ID": article_id,
                          "Publication Date": date,
                          "Citations ID": citations_ids})

citations_df = pd.DataFrame(articles_list).set_index("ID")

# -----------------------------------------------------------------------------

with open(os.path.join(DATA_PATH, "citations.csv"), "w") as f:
    citations_df.to_csv(f)

G = nx.DiGraph()

for i, c in citations_df["Citations ID"].iteritems():
    G.add_node(i)
    for c2 in c:
        G.add_edge(c2, i)

net = Network(height='600px', width='50%', directed=True)
net.show_buttons(filter_=['physics'])
net.from_nx(G)
net.show(os.path.join(DATA_PATH, "citations_graph.html"))
