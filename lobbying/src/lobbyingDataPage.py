import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import re

class DataPage:
    def __init__(self, html):
        self.tables = {} # A dictionary that will hold all the tables as they are extracted
        self.soup = bs(html, 'html.parser')
        self.dfs = pd.read_html(html)

        if self.check_validity():
            self.get_header()
            self.get_source_info()
            self.scrape_tables()

    # returns true if the html is valid and processable
    def check_validity(self):
        if 'An Error Occurred' in self.soup.text:
            return False
        return True

    def get_source_info(self):
        self.get_date_range()
        self.get_source_name()

    def get_date_range(self):
        self.date_range = self.dfs[4][0][2].split('period:  ')[1]

    # Implement seperately for lobbyists and entities
    def get_source_name():
        pass

    # Empty function, needs to be implemented seperately for Lobbyists and Entities
    # This function does the actual work of scraping the tables. Calls a bunch of helpers
    def scrape_tables(self):
        self.get_lobbying_activity()
        self.get_campaign_contributions()
        self.get_client_compensation()
        #SALARIES?
        #OPERATING EXPENSES?
        #ENTERTAINMENT / ADDITIONAL EXPENSES?

    def get_lobbying_activity(self):
        pass

    def get_campaign_contributions(self):
        pass

    def get_client_compensation(self):
        pass

    def get_header(self):
        self.tables['Headers'] = pd.DataFrame(columns=['Authorizing Officer name','Lobbyist name','Title','Business name','Address','City, state, zip code','Country','Agent type','Phone'])
        header = self.dfs[5][0:7].transpose() #Extract header table and orient it properly
        header.columns = header.iloc[0] #Pull the column names from the first row...
        header = header[1:] # ... and then drop that row
        self.tables['Headers'] = pd.concat([self.tables['Headers'], header])

    # This function adds the date range and entity / lobbyist name to each table
    def add_source(self):
        for table in self.tables:
            table['Date Range'] = self.date_range
            table['Source'] = self.source_name

    # Attempts to save each table from the page to disk
    def save(self):
        for table in self.tables.keys():
            self.write_data(f'lobbying\data\{table.replace(" ","_").lower()}.csv', self.tables[table])

    def write_data(self, file_path, dataframe):
        write = True
        #if os.path.exists(file_path):
        with open(file_path, mode = 'a', encoding = 'utf-8') as f:
            for line in f:
                if self.company_name in line and self.date_range in line:
                    print('Data already present in ' + file_path)
                    write = False
                    break

        if write and type(dataframe) == pd.DataFrame:
            print('Saving data to ' + file_path)
            dataframe.to_csv(file_path, mode ='a+',header=(not os.path.exists(file_path)), index=False)

    # Helper function to replace all blocks of whitespace with a single space
    def clean_entry(entry):
        return re.sub("\s\s+", " ", entry)


class LobbyistDataPage(DataPage):
    def __init__(self, html):
        DataPage.__init__(self, html)

    def get_source_name(self):
        self.source_name = self.tables['Headers']['Lobbyist name']

    def get_lobbying_activity(self):
        pass

    def get_campaign_contributions(self):
        pass

    def get_client_compensation(self):
        pass

class EntityDataPage(DataPage):
    def __init__(self, html):
        DataPage.__init__(self,html)

    def get_source_name(self):
        self.source_name = self.tables['Headers']['Business name']

    def get_lobbying_activity(self):
        pass

    def get_campaign_contributions(self):
        pass

    def get_client_compensation(self):
        pass









# Takes a list of html files, extracts the data, and saves them to disk
def extract_and_save(html_list):
    ## TODO: Add check for entity vs lobbyist
    #for html in html_list:
        #LobbyingDataPage(html).save()
    for i in range(len(html_list)):
        print("Saving "+str(i))
        DataPage(html_list[i]).save()

# Downloads html from a url
def pull_data(url):
    headers={"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
    result = requests.get(url, headers=headers)
    result.raise_for_status()
    return result.content

# Downloads a list of html pages from a list of url's
def download_html_list(url_list):
    html_list = []
    for url in url_list:
        print("Pulling data from " + url)
        html_list.append(pull_data(url))
    return html_list

# Takes a list of URL's, downloads them, processes them, and saves them to disk
def save_data_from_url_list(url_list):
    disclosure_links = extract_and_save(download_html_list(url_list))
    html_list = download_html_list(disclosure_links)

