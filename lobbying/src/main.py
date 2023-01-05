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

import requests, datetime, os
from lobbyingDataPage import LobbyingDataPage
from lobbyingScraper import extract_disclosures, extract_client_links

def extract_and_save(html_list):
    #for html in html_list:
        #LobbyingDataPage(html).save()
    for i in range(len(html_list)):
        print("Saving "+str(i))
        LobbyingDataPage(html_list[i]).save()

def pull_data(url):
    headers={"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
    result = requests.get(url, headers=headers)
    result.raise_for_status()
    return result.content

def download_html_list(url_list):
    html_list = []
    for url in url_list:
        print("Pulling data from " + url)
        html_list.append(pull_data(url))
    return html_list

def save_data_from_url_list(url_list):
    extract_and_save(download_html_list(url_list))

def scrape_past_data():
    start_year = 2005
    this_year = datetime.date.today().year
    date_range = range(start_year, this_year)
    for year in date_range:
        extract_and_save(download_html_list(extract_disclosures(extract_client_links(str(year)))))

if __name__ == "__main__":
    #disclosure_links = extract_disclosures(extract_client_links())
    #html_list = download_html_list(disclosure_links)
    scrape_past_data()
