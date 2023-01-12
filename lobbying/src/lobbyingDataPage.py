import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import re

class LobbyingDataPage:
    def __init__(self, html):
        self.tables = {}
        self.dfs = pd.read_html(html)
        if 'An Error Occurred' in str(self.dfs[0][0]):
            #end this. Set default values?
            pass
        else:
            self.is_entity = 'Entity' in self.dfs[4][0][2]
            self.get_date_range()
            self.get_header()
            self.scrape_tables()

    def get_date_range(self):
        self.date_range = self.dfs[4][0][2].split('period:  ')[1]

    #Extracts the table of header info from the top of the page
    def get_header(self):
        table = self.dfs[5][0:7].transpose()
        table.columns = table.iloc[0]
        table = table[1:]
        if self.is_entity:
            self.tables['Entities'] = table
        else:
            self.tables['Lobbyists'] = table

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
        if self.is_entity:
            lobbyist = self.dfs[i-2][0][0].split('Lobbyist:')[1].strip()
        else:
            lobbyist = str(self.tables['Lobbyists']['Lobbyist name'][1])
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

    def clean_entry(entry):
        return re.sub("\s\s+", " ", entry)

    def fetch_tables(self):
        return self.tables


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
    disclosure_links = extract_and_save(download_html_list(url_list))
    html_list = download_html_list(disclosure_links)

