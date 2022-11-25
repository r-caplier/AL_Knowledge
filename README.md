# AL_Knowledge

Leveraging data driven techniques and deep learning models to improve knowledge of Anastomotic Leaks.

## Required elements

Create the conda environment using the .yml file, using ```conda env create -f env.yml
``` which will create an env named AL_Knowledge, and install all required packages with ```pip install -r requirements.txt```. The python version used is 3.10.4.

## Organisation of the repository

-   **citations.py**: Uses PubMed to gather all articles matching the search criteria, and creates a dataframe (articles_infos.csv and articles_infos.pkl) containing ID, Title, Authors, Date, and the list of papers citing the initial article.

-   **constants.py**: Paths, inital folder setup, to import in each subsequent file.

-   **display.py**: Allows the user ot display the entities extracted from an articles with color coding. Filenames are the PubMed IDs of each articles, as they appear in the data folder.

-   **dataviz.py**: Provides wordclouds, 2-grams and 3-grams visualization over the entire dataset.

-   **downloader.py**: Creates the dataset, by querying PubMed and downloading the matching articles. The search terms used can be modified easily, at the top of the script. Also contains the cleaning process, with all the patterns used and the method in which they are used. Complete execution for 8K articles takes around 24 hours.

-   **encoding.py**: WIP, trying to improve clustering abilities by creating a representation of each document based of of BERT encodings.

-   **ner.py**: Named entity recognition. With a fully downloaded dataset (through downloader.py), extracts the entities found by varying spacy models. Full execution takes a few hours for 2K articles.

-   **relations.py**: Builds the relations dataset. Entities are matched within the same sentence, with weights related to the distance between every couple of entity.
