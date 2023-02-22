import logging
import pickle
import datetime
from lobbyingDataPage import *
from lobbyingScraper import *

if __name__ == "__main__":

    logging.basicConfig(level=logging.CRITICAL)

    with open('../tests/testfiles/all_current_urls.pkl', 'rb') as f:
        all_urls = pickle.load(f)

    for url in all_urls:
        PageFactory(url).save()
