import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import re

class DataPage:
    def __init__(self, html):
        self.tables = {} # A dictionary that will hold all the tables as they are extracted

        self.dfs = pd.read_html(html)

        self.get_date_range()
        self.get_header()
        self.scrape_tables()

    def get_date_range(self):
        self.date_range = self.dfs[4][0][2].split('period:  ')[1]

    def get_header(self):
        self.tables['Headers'] = pd.DataFrame(columns=['Authorizing Officer name','Lobbyist name','Title','Business name','Address','City, state, zip code','Country','Agent type','Phone'])
        header = self.dfs[5][0:7].transpose() #Extract header table and orient it properly
        header.columns = header.iloc[0] #Pull the column names from the first row...
        header = header[1:] # ... and then drop that row
        self.tables['Headers'].append(header)

    # Empty function, needs to be implemented seperately for Lobbyists and Entities
    def scrape_tables(self):
        pass

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



class LobbyistDataPage(DataPage):
    def __init__(self, html):
        DataPage.__init__(self, html)

    def scrape_tables(self):
        pass

class EntityDataPage(DataPage):
    def __init__(self, html):
        DataPage.__init__(self,html)

    def scrape_tables(self):
        for i in range(len(self.dfs)):
            df_str = str(self.dfs[i])
            #ACTIVITIES TABLES
            if 'House / Senate' in df_str and len(self.dfs[i]) == 1:
                self.get_activities(i)

            #CLIENT COMPENSATION
            if 'Client Compensation' in df_str and len(self.dfs[i]) == 2:
                self.get_compensation(i)

            #SALARIES
            if 'Salaries' in df_str and len(self.dfs[i]) == 2:
                self.get_salaries(i)


    def get_activities(self, i):
        self.tables.setdefault('Activities', pd.DataFrame()) #Create table if it doesn't exist
        client = str(self.dfs[i-1][0][0]).split('Client:')[1].strip()
        lobbyist = self.dfs[i-2][0][0].split('Lobbyist:')[1].strip()
        table = self.dfs[i+1][:-1]
        table.insert(0, 'Client', client)
        table.insert(0, 'Lobbyist', lobbyist)
        table.insert(0, 'Date Range', self.date_range)
        self.tables['Activities'] = pd.concat( [self.tables['Activities'], table])

    def get_compensation(self, i):
        self.tables.setdefault('Compensation', pd.DataFrame())
        comp_str = self.dfs[i][0][1]
        data = re.findall(r'[\w\s\.&,]+\s\$[\d,\.]+', comp_str[11:])
        data = [d.split(" $") for d in data]
        data = [[d[0], float(d[1].replace(',',''))] for d in data if len(d) == 2]
        table = pd.DataFrame(data, columns = ['Name', 'Amount'])
        self.tables['Compensation'] = pd.concat( [self.tables['Compensation'], table])

    def get_salaries(self, i):
        self.tables.setdefault('Salaries', pd.DataFrame())
        table = self.dfs[i][:-1]
        self.tables['Salaries'] = pd.concat( [self.tables['Salaries'], table])

    # Helper function to replace all blocks of whitespace with a single space
    def clean_entry(entry):
        return re.sub("\s\s+", " ", entry)

    # Getter function, mostly here for testing purposes
    def fetch_tables(self):
        return self.tables

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

