import logging
import pickle
import sys
import datetime
from lobbyingDataPage import *
from lobbyingScraper import *
from settings import *

def process_current_htmls(argv):
    if argv:
        offset = int(argv[1])
    else:
        offset = 0

    with open('../tests/testfiles/all_current_urls.pkl', 'rb') as f:
        all_urls = pickle.load(f)

    for url in all_urls[offset:]:
        PageFactory(url).save()

def query_database_size():
    pass


if __name__ == "__main__":

    logging.basicConfig(level=logging.CRITICAL)

    process_current_htmls(sys.argv)

