import os
import time
import re
from tqdm.auto import tqdm

import pickle
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from constants import *

# -----------------------------------------------------------------------------

# Singular pattern formatting is
# {"pattern": regex string matching the pattern to act on,
#  "replace": (optionnal) if type is replace, regex string to use to replace the above matched string,
#  "type": can be remove or replace, if replace, the replace field needs to be filled in the pattern definition}

# Confusing or useless text patterns to remove or replace
BAD_PATTERNS = [
    {"pattern": r"\[([0-9][,-–]? ?)+\],?", "type": "remove"},  # References mentions [3] or [4-9]
    {"pattern": r"\D[0-9]{1,2},", "type": "remove"},  # References mentions 3, 4, 7
    # References mention Text.2 or 35%.4 or Text,3
    {"pattern": r"([a-zA-Z%])([,\.]*)[0-9]+", "replace": r"\1\2", "type": "replace"},
    {"pattern": r"\(.*?\)", "type": "remove"},  # Anything in parentheses, not greedy matching
    {"pattern": r"i[iv]*\)", "type": "remove"},  # Roman bullet points in paragraphs
]

# Same pattern matching, but to run last to cleanup punctuation
PUNCTUATION = [
    {"pattern": r" +", "replace": " ", "type": "replace"},
    {"pattern": r" \.", "replace": ".", "type": "replace"},
    {"pattern": r" ,", "replace": ",", "type": "replace"},
    {"pattern": r"\n+", "replace": "\n", "type": "replace"},
]

# -----------------------------------------------------------------------------


class CleanerClass():

    def __init__(self):
        pass

    def _pattern_remover(self, text, patterns):
        """
        Given text, removes or replaces a list of patterns from it.
        """
        for pattern in BAD_PATTERNS:
            if pattern["type"] == "replace":
                if "replace" in pattern.keys():
                    text = re.sub(pattern["pattern"], pattern["replace"], text)
                else:
                    text = re.sub(pattern["pattern"], "", text)
            elif pattern["type"] == "full" and re.search(pattern["pattern"], text):
                text = ""

        return text

    def clean(self, text):

        paragraphs = text.split('\n')
        clean_paragraphs = []

        for p in paragraphs:
            clean_p = self._pattern_remover(p, BAD_PATTERNS)
            clean_p = self._pattern_remover(p, PUNCTUATION)
            clean_paragraphs.append(clean_p)

        return '\n'.join(clean_paragraphs)

# -----------------------------------------------------------------------------


class DownloaderClass():

    def __init__(self):

        self.ser = Service(GeckoDriverManager().install())

    def _pget(self, url, stream=False):
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

    def _get_search_matches(self, search_terms, max_page_num=False):
        """
        Gets all of the ids of articles matching a given list of search terms
        Optionnaly, set a max number of pages to search through (10 articles per page)
        Selenium not used here
        """
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
                page = self._pget(page_url)
                page_soup = BeautifulSoup(page.text, features="lxml")
                page_ids = page_soup.find("div", {"class": "search-results-chunk results-chunk"}
                                          ).get("data-chunk-ids").split(",")
                full_search_ids += page_ids
            except AttributeError:
                break

        # Saving the results
        self.search_results_ids = full_search_ids

    def _get_article_text(self, article_id):
        """
        Finds the url of the corresponding article based on the article id in the page, wherever it might be hosted
        """
        # Tracks whether or not the url was found
        found = True

        # Getting the inital page
        pubmed_url = "https://pubmed.ncbi.nlm.nih.gov/" + article_id + "/"
        pubmed_page = self._pget(pubmed_url)
        pubmed_soup = BeautifulSoup(pubmed_page.text, features="lxml")

        # Grabbing download links if available
        try:
            dl_features = pubmed_soup.find("div", {"class": "full-text-links"}).find("a", {"class": "link-item"})
            dl_url = dl_features.get('href')
            dl_page_type = dl_features.get('data-ga-action')
        except:
            return False, str(article_id) + " - No article links found"

        soup = self._get_soup(dl_url)
        response, text = self._get_text(soup, dl_page_type)
        if not response:
            if not text:
                text = str(article_id) + f" - {dl_page_type}: Error in HTML"
            else:
                text = str(article_id) + " - " + text
        return response, text

    def _get_soup(self, url):
        """
        Requests the soup from a page
        Selenium is used to account for DDoS protection that exists for some websites
        """
        options = webdriver.FirefoxOptions()
        options.headless = True
        browser = webdriver.Firefox(options=options, service=self.ser)

        browser.get(url)
        time.sleep(2)
        html = browser.page_source
        soup = BeautifulSoup(html, 'lxml')  # .encode("utf-8")

        browser.close()

        return soup

    def _get_text(self, soup, source_name):
        """
        Returns article texts fetched from the HTML content of the page
        Each source needs to be manually implemented
        """
        if source_name == "Wiley":
            try:
                paragraphs = []
                abstract = soup.find("section", {"class": "article-section article-section__abstract"})
                if abstract != None:
                    paragraphs += abstract.find_all("p")
                sections = soup.find("section", {"class": "article-section article-section__full"})
                if sections != None:
                    good_sections = sections.find_all("section", {"class": "article-section__content"})
                    if good_sections != None:
                        for section in good_sections:
                            paragraphs += section.find_all("p")
                return True, '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in paragraphs])
            except:
                return False, None

        elif source_name == "Springer":
            try:
                article = soup.find("div", attrs={"class": "c-article-body"})
                paragraphs = article.find_all(re.compile("[section|div]"), recursive=False)
                good_paragraphs = []
                i = 0
                found = False
                while i < len(paragraphs) and not found:
                    if paragraphs[i].find("section", {"data-title": "References"}) != None:
                        found = True
                    else:
                        for p in paragraphs[i].find_all("p"):
                            good_paragraphs.append(p)
                        i += 1
                article_text = '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in good_paragraphs])
                # Remove this line, just return article text and process it later
                return True, re.sub("Access provided by ETH Zürich Elektronische Ressourcen\n", "", article_text)
            except:
                return False, None

        elif source_name == "Elsevier Science":
            try:
                abstract = soup.find("div", {"id": "abstracts"})
                if abstract != None:
                    abstract_text = '\n'.join([re.sub("<.{1,2}>", "", paragraph.text)
                                              for paragraph in abstract.find_all("p")])
                else:
                    abstract_text = ""
                body = soup.find("div", {"id": "body"}).find("div", {"class": ""})
                body_text = '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in body.find_all("p")])
                return True, abstract_text + '\n' + body_text
            except:
                return False, None

        else:
            return False, f"{source_name}: Not implemented"

    def download(self, search_terms, max_page_num=False, overwrite=False):
        """
        Downloads the pdfs of matching search results
        """
        save_search_id_name = "full_search_ids_" + "_".join(search_terms) + ".pkl"

        if not os.path.exists(os.path.join(LOGS_PATH, save_search_id_name)) or overwrite:
            print("\n\nGrabbing all search results...")
            self._get_search_matches(search_terms, max_page_num=max_page_num)
            with open(os.path.join(LOGS_PATH, save_search_id_name), "wb") as f:
                pickle.dump(self.search_results_ids, f)
        else:
            print("\n\nFound already pre-downloaded search results!")
            with open(os.path.join(LOGS_PATH, save_search_id_name), "rb") as f:
                self.search_results_ids = pickle.load(f)
        print(f"Found {len(self.search_results_ids)} matching documents.")

        print("Downloading...")
        doc_num = 0
        found_num = 0
        found_dict = {"Name": [], "PubMedID": [], "Path": []}
        log = "Logged actions -------------------\n"

        for article_id in tqdm(self.search_results_ids):
            doc_num += 1
            found, text = self._get_article_text(article_id)

            if found:
                found_num += 1
                article_path = os.path.join(DATA_PATH, article_id)
                if not os.path.exists(article_path):
                    os.mkdir(article_path)
                with open(os.path.join(article_path, "raw.txt"), "w") as f:
                    f.write(text)
                log += article_id + " - Downloaded\n"
            else:
                log += text + "\n"

        time.sleep(1)

        log = f"Downloaded {found_num}/{len(self.search_results_ids)} documents\n" + log
        with open(os.path.join(LOGS_PATH, "download_log.txt"), "w") as f:
            f.write(log)

        os.remove("geckodriver.log")

# -----------------------------------------------------------------------------


downloader = DownloaderClass()
print("Downloading...")
search_terms = ["anastomotic", "leak"]
downloader.download(search_terms, max_page_num=False, overwrite=False)

cleaner = CleanerClass()
print("Cleaning text...")
for folder_path in tqdm(os.listdir(DATA_PATH)):
    with open(os.path.join(DATA_PATH, folder_path, "raw.txt"), "r") as f:
        text = f.read()
    clean_text = cleaner.clean(text)
    with open(os.path.join(DATA_PATH, folder_path, 'clean.txt'), "w") as f:
        f.write(clean_text)
