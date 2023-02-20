import logging
import pickle
from lobbyingDataPage import *
from lobbyingScraper import *

if __name__ == "__main__":
    logging.basicConfig(level=logging.CRITICAL)

    for year in range(2007,2023): #remember, this will generate 2005-2022, NOT 2023
        print(f'YEAR: {year}')
        print(f'Collecting Disclosure URLs for year {year}')
        disclosure_urls = get_disclosures_by_year(year)
        print(f"{len(disclosure_urls)} disclosure urls collected.")
        filename = f'../tests/testfiles/{year}_urls.pkl'
        print(f"URL list acquired. Saving to {filename}")
        with open(filename, 'wb+') as f:
                    pickle.dump(disclosure_urls, f)
    print("Job's done!")


