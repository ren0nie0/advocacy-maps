import re
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import psycopg2
import psycopg2.extras as extras
import numpy as np
import logging

save_type = 'psql'

params_dict = {
    'host'      : 'localhost',
    'port'      : '5432',
    'database'  : 'maple_lobbying',
    'user'      : 'geekc',
    'password'  : 'asdf'
}

def save_data_from_url_list(url_list, save_type=save_type):
    for url in url_list:
        page = PageFactory(url)
        if page:
            page.save(save_type)

def text_splitter(query_result):
    return [line.strip() for line in query_result.split('\n') if line.strip()]


def divide_text(query_result, chunk_size):
    # splits a list into a list of lists,
    # with the length of each inner list
    # equal to chunk_size
    def chunk_list(some_list,chunk_size):
            for i in range(0, len(some_list), chunk_size):
                yield some_list[i:i+chunk_size]

    split_text=text_splitter(query_result)

    if len(split_text) % chunk_size != 0:
        split_text = separate_date(split_text)
        if len(split_text) % chunk_size != 0:
            logging.exception("Table Error")
            return []

    divided_text = list(chunk_list(split_text, chunk_size))
    return divided_text

def create_table(row_list, columns):
    try:
        table_df = pd.DataFrame(row_list, columns=columns)
        return table_df
    except:
        dataframe_exception(row_list, columns)

def dataframe_exception(row_list, columns):
    logging.exception('DATAFRAME EXCPETION')
    logging.exception(row_list)
    logging.exception(columns)
    # for i in range(len(row_list)):
    #     row_list[i] = separate_date(row_list[i])
    # create_table(row_list, columns)


def separate_date(row_list):
    new_list = []
    regex_string = r"(\d+/\d+/\d+)\s?(.*)"
    regex_query = re.compile(regex_string)
    for i in range(len(row_list)):
        result = re.fullmatch(regex_query, row_list[i])
        if result:
            new_list.append(result.group(1))
            new_list.append(result.group(2))
        else:
            new_list.append(row_list[i])
    return new_list


# Given html or a url, generates a DataPage
class PageFactory:
    def __new__(cls, url = None, html = None):

        if not (url or html):
            logging.exception("PageFactory requires either a url string or html file")

        html = html if html else PageFactory.pull_html(url)
        soup = bs(html, 'html.parser')

        if 'Disclosure reporting details' not in soup.text:
            logging.exception(f'Page Error for url {url}: No Disclosure Report')
            return None

        if 'Lobbyist Entity' in soup.text:
            return EntityDataPage(soup, url)
        else:
            return LobbyistDataPage(soup, url)

    def pull_html(url):
        headers={"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
        result = requests.get(url, headers=headers)
        result.raise_for_status()
        return result.content


# Given html of a lobbying disclosure page, a data page extracts all the data from the relevant tables
# It also has the ability to save the tables to disk in different ways
class DataPage:

    def __init__(self, soup, url = None):
        self.has_error = False  # flag for debugging purposes
        self.url = url
        self.tables = {} # A dictionary that will hold all the tables as they are extracted
        self.soup = soup
        self.dfs = pd.read_html(str(soup))

        self.get_header()
        logging.info(f'Got Header {self.source_name} {self.date_range}')
        self.scrape_tables()
        self.add_source()


    ## BEGIN INIT FUNCTIONS ##

    #updates a table in the tables dictionary
    #creates the table if it does not yet exist
    def update_table(self, table_name, dataframe):
        if dataframe is None: #TODO This is also error handling! Dataframe should NEVER be none unless something goes wrong
            logging.exception(f"INVALID DATAFRAME {table_name}")
            return
        if table_name in self.tables.keys():
            self.tables[table_name] = pd.concat([self.tables[table_name], dataframe])
        else:
            self.tables[table_name] = dataframe


    # The one easy table. It's the same throughout time, extremely consistent, and pandas can find it easily
    # the one big problem with it is that it's different columns for individuals and entities
    def get_header(self):
        columns =['Authorizing Officer name','Lobbyist name','Title','Business name','Address','City, state, zip code','Country','Agent type','Phone']
        table_name = 'Headers'
        header_df = self.dfs[5][0:7].transpose() #Extract header table and orient it properly
        header_df.columns = header_df.iloc[0] #Pull the column names from the first row...
        header_df = header_df[1:] # ... and then drop that row

        empty_dataframe = pd.DataFrame(columns=columns)
        normalized_header_df = pd.concat([empty_dataframe, header_df]) #This is necessary to ensure consistent columns
        self.update_table(table_name, normalized_header_df)
        self.date_range = self.dfs[4][0][2].split('period:  ')[1]
        self.get_source_name()


    # Implement seperately for lobbyists and entities
    def get_source_name():
        pass


    # That's it for the easy stuff
    def scrape_tables(self):
        self.get_lobbying_activity()
        logging.info(f"Lobbying Activities {bool('Lobbying Activities' in self.tables.keys())}")
        self.get_campaign_contributions()
        logging.info(f"Campaign Contributions {bool('Campaign Contributions' in self.tables.keys())}")
        self.get_client_compensation()
        logging.info(f"Client Compensation {bool('Client Compensation' in self.tables.keys())}")
        #SALARIES?
        #OPERATING EXPENSES?
        #ENTERTAINMENT / ADDITIONAL EXPENSES?


    # pulls everything between each tabe_start and table_end
    # returns a list of results
    def query_page(self, table_start, table_end, string=None):
        if not string:
            string = self.soup.text
        query_string = fr"(?<={table_start}).*?(?={table_end})"
        query = re.compile(query_string,re.DOTALL)
        query_results = re.findall(query, string)
        return query_results


    def get_lobbying_activity(self, start_query):
        table_name = 'Lobbying Activities'
        columns = ['House or Senate','Bill Number or Agency Name','Bill title or activity','Agent position','Amount','Direct business association']
        table_start = 'House / SenateBill Number or Agency NameBill title or activityAgent positionAmountDirect business association'
        table_end = r'\xa0\xa0\xa0\nTotal'

        #our first query has a wider scope so we can pull the client and lobbyist name
        wide_results = self.query_page(start_query, r' amount\n')# activities_query is different for individuals and lobbyists
        for wide_result in wide_results:
            query_results = self.query_page(table_start, table_end, wide_result)
            for query_result in query_results:
                row_list = divide_text(query_result, len(columns))
                dataframe = create_table(row_list, columns)

                dataframe = self.add_identifiers_to_activities_table(wide_result, dataframe)

                self.update_table(table_name, dataframe)


    #implemented seperately for lobbyists and entities
    def add_identifiers_to_activities_table(self, query_result, dataframe):
        pass


    # Implemented seperately for lobbyists and entities
    # the sole difference currently is the columns. could we abstract that more?
    def get_campaign_contributions(self, columns = None):
        pass


    def get_client_compensation(self):
        table_name = 'Client Compensation'
        columns = ['Client Name','Amount']
        table_start = 'NameAmount'
        table_end = r'Total salaries received'

        query_results = self.query_page(table_start, table_end)
        for query_result in query_results:
            row_list = divide_text(query_result, len(columns))
            dataframe = create_table(row_list, columns)
            self.update_table(table_name, dataframe)


    # This function adds the date range and entity / lobbyist name to each table
    def add_source(self):
        for table in self.tables.keys():
            logging.debug(f'Adding identifiers to table {table}')
            self.tables[table]['Date Range'] = self.date_range
            if table != 'Headers': #the header table already has the source name
                self.tables[table]['Source name'] = self.source_name
    ## END INIT FUNCTIONS ##


    # Attempts to save each table from the page to disk
    def save(self, save_type = save_type):
        root_directory = "lobbying\data"
        match save_type:
            case 'csv':
                for table in self.tables.keys():
                    self.write_data_to_csv(f'{root_directory}\{table.replace(" ","_").lower()}.csv', self.tables[table])
            case 'psql':
                for table in self.tables.keys():
                    self.write_data_to_psql(table.replace(" ","_").lower(), self.tables[table])


    def write_data_to_csv(self, file_path, dataframe):
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


    def write_data_to_psql(self, postgres_table, dataframe):
        conn = psycopg2.connect(**params_dict)
        tuples = [tuple(x) for x in dataframe.to_numpy()]
        cols = ','.join([col.lower().replace(",","").replace(" ","_".replace('/','or')) for col in list(dataframe.columns)])
        # SQL query to execute
        query = "INSERT INTO %s(%s) VALUES %%s" % (postgres_table, cols)
        cursor = conn.cursor()
        try:
            extras.execute_values(cursor, query, tuples)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}On table {postgres_table}")
            self.has_error = True
            # columns = dataframe.columns.tolist()
            # for _, i in dataframe.iterrows():
            #     for c in columns:
            #         if i[c] and len(i[c]) > 255:
            #             print(c)
            #             print(i[c])
            conn.rollback()
            cursor.close()
            return 1
        logging.info(f"dataframe successfully inserted into table '{postgres_table}'")
        cursor.close()



    # Helper function to replace all blocks of whitespace with a single space
    # currently not used??? Probably should be!
    def clean_entry(entry):
        return re.sub("\s\s+", " ", entry)


class LobbyistDataPage(DataPage):

    def __init__(self, html, url):
        DataPage.__init__(self, html, url)


    def get_source_name(self):
        self.source_name = self.tables['Headers']['Lobbyist name'][1]

    def get_lobbying_activity(self):
        return super().get_lobbying_activity(r'Client: ')


    def get_campaign_contributions(self):
        table_name = 'Campaign Contributions'
        columns = ['Date','Recipient name','Office sought','Amount']
        table_start = r"".join(columns)
        table_end = "\xa0\xa0Total contributions"

        query_results = self.query_page(table_start, table_end)

        for query_result in query_results:
            row_list = divide_text(query_result, len(columns))
            dataframe = create_table(row_list, columns)

            dataframe['Lobbyist name'] = self.source_name

            self.update_table(table_name, dataframe)


    def add_identifiers_to_activities_table(self, query_result, dataframe):
        dataframe['Lobbyist name'] = self.source_name
        dataframe['Client name'] = query_result[0].split('\n')[0]
        return dataframe



class EntityDataPage(DataPage):

    def __init__(self, html, url):
        DataPage.__init__(self,html,url)


    def get_source_name(self):
        self.source_name = self.tables['Headers']['Business name'][1]

    def get_lobbying_activity(self):
        return super().get_lobbying_activity(r'Lobbyist: ')


    def add_identifiers_to_activities_table(self, query_result, dataframe):
        split_result = [entry for entry in query_result.split('\n') if entry]
        dataframe['Lobbyist name'] = query_result.split('\n')[0]
        dataframe['Client name'] = split_result[2]
        return dataframe


    def get_campaign_contributions(self):
        table_name = 'Campaign Contributions'
        columns = ['Date','Lobbyist name','Recipient name','Office sought','Amount']
        table_start = "".join(columns)
        table_end = "\xa0\xa0Total contributions"

        query_results = self.query_page(table_start, table_end)
        for query_result in query_results:
            row_list = divide_text(query_result, len(columns))
            dataframe = create_table(row_list, columns)
            self.update_table(table_name, dataframe)
