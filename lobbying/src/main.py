## TODO:
## SAVE HTML
# workflow goes: run scraper -> save html from each page to disk -> iterate thru html pages and save tables to disk
# Need to change: Right now scraper just generates url's, we should just go ahead and have it save the relevant html to file
#                 Scraper is currently configured to just suck up 2020 data, need to make that variable - DONE

# FINALIZE BEHAVIOR
# the program should examine it's environment when run to see if files have been downloaded yet.
#               ALTERNATELY, query our database to find the latest date, and get the one after that
#       if NO, it needs to download all the files, from every year, and convert them to tables
#       if YES, it needs to download the LATEST files and convert them to tables
# After generating tables, we need to upload them to whatever long-term storage solution we are using
#
# right now, we need to start saving it to a SQL database locally

from lobbyingDataPage import *
from lobbyingScraper import *

if __name__ == "__main__":
    #disclosure_links = extract_disclosures(extract_client_links())
    #html_list = download_html_list(disclosure_links)
    disclosure_url_list = extract_disclosures(extract_client_links('2020'))
    save_data_from_url_list(disclosure_url_list, save_type='psql')
