import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
import re


#supported save types:
# csv
#
save_type = 'csv'

def create_table(query_result, columns):
    def divide_chunks(some_list,chunk_size):
            for i in range(0, len(some_list), chunk_size):
                yield some_list[i:i+chunk_size]
    split_text=[line.strip() for line in query_result.split('\n') if line.strip()]
    divided_text = list(divide_chunks(split_text, len(columns)))
    table_df = pd.DataFrame(divided_text, columns=columns)
    return table_df


class DataPage:
    table_columns = {}
    activities_query = ""
    def __init__(self, html):
        self.tables = {} # A dictionary that will hold all the tables as they are extracted
        self.soup = bs(html, 'html.parser')
        self.dfs = pd.read_html(html)

        if self.check_validity():
            self.get_header()
            self.get_date_range()
            self.get_source_name()
            self.scrape_tables()
            #self.add_source()


    ## BEGIN INIT FUNCTIONS ##
    # returns true if the html is valid and processable
    def check_validity(self):
        if 'An Error Occurred' in self.soup.text:
            return False
        return True


    # The one easy table. It's the same throughout time, extremely consistent, and pandas can find it easily
    def get_header(self):
        columns =['Authorizing Officer name','Lobbyist name','Title','Business name','Address','City, state, zip code','Country','Agent type','Phone']
        table_name = 'Headers'

        header_df = self.dfs[5][0:7].transpose() #Extract header table and orient it properly
        header_df.columns = header_df.iloc[0] #Pull the column names from the first row...
        header_df = header_df[1:] # ... and then drop that row
        self.update_table(table_name, header_df)

    def get_date_range(self):
        self.date_range = self.dfs[4][0][2].split('period:  ')[1]
        # query_string = r"(?<=period:).*?(\d\d\/\d\d\/\d\d\d\d - \d\d\/\d\d\/\d\d\d\d)"
        # query = re.compile(query_string,re.DOTALL)
        # query_results = re.search(query, self.soup.text)
        # self.date_range = query_results.group(1)


    # Implement seperately for lobbyists and entities
    def get_source_name():
        pass


    # That's it for the easy stuff
    def scrape_tables(self):
        self.get_lobbying_activity()
        self.get_campaign_contributions()
        self.get_client_compensation()
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


    #updates a table in the tables dictionary
    #creates the table if it does not yet exist
    def update_table(self, table_name, dataframe):
        if table_name in self.tables.keys():
            pd.concat([self.tables[table_name], dataframe])
        else:
            self.tables[table_name] = dataframe

    def get_date_range(self):
        query_string = r"(?<=period:).*?(\d\d\/\d\d\/\d\d\d\d - \d\d\/\d\d\/\d\d\d\d)"
        query = re.compile(query_string,re.DOTALL)
        query_results = re.search(query, self.soup.text)
        self.date_range = query_results.group(1)

    # Implement seperately for lobbyists and entities
    def get_source_name():
        pass

    def scrape_tables(self):
        self.get_lobbying_activity()
        self.get_campaign_contributions()
        self.get_client_compensation()
        #SALARIES?
        #OPERATING EXPENSES?
        #ENTERTAINMENT / ADDITIONAL EXPENSES?

    def get_lobbying_activity(self):
        table_name = 'Activities'
        columns = ['House / Senate','Bill Number or Agency Name','Bill title or activity','Agent position','Amount','Direct business association']
        table_start = r"".join(columns)
        table_end = r'\xa0\xa0\xa0\nTotal'

        #our first query has a wider scope so we can pull the client and lobbyist name
        query_results = self.query_page(self.activities_query, r' amount\n')# activities_query is different for individuals and lobbyists
        for query_result in query_results:
            activities_table = self.query_page(table_start, table_end, query_result)[0]

            anon_activities_df = create_table(activities_table, columns)
            activities_df = self.add_identifiers_to_activities_table(query_result, anon_activities_df)
            self.update_table(table_name,activities_df)


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
        table_start = r"".join(columns)
        table_end = r'Total salaries received'

        query_results = self.query_page(table_start, table_end)
        for query_result in query_results:
            compensation_df = create_table(query_result, columns)
            self.update_table(table_name, compensation_df)


    # The one easy table. It's the same throughout time, extremely consistent, and pandas can find it easily
    def get_header(self):
        columns =['Authorizing Officer name','Lobbyist name','Title','Business name','Address','City, state, zip code','Country','Agent type','Phone']
        table_name = 'Header'
        header_df = self.dfs[5][0:7].transpose() #Extract header table and orient it properly
        header_df.columns = header_df.iloc[0] #Pull the column names from the first row...
        header_df = header_df[1:] # ... and then drop that row
        self.update_table(table_name, header_df)


    # This function adds the date range and entity / lobbyist name to each table
    def add_source(self):
        for table in self.tables:
            table['Date Range'] = self.date_range
            table['Source'] = self.source_name
    ## END INIT FUNCTIONS ##


    # Attempts to save each table from the page to disk
    def save(self):
        root_directory = "lobbying\data"
        match save_type:
            case 'csv':
                for table in self.tables.keys():
                    self.write_data_to_csv(f'{root_directory}\{table.replace(" ","_").lower()}.csv', self.tables[table])

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

    # Helper function to replace all blocks of whitespace with a single space
    # currently not used??? Probably should be!
    def clean_entry(entry):
        return re.sub("\s\s+", " ", entry)

class LobbyistDataPage(DataPage):

    activities_query = r'Client: '


    def __init__(self, html):
        DataPage.__init__(self, html)


    def get_source_name(self):
        self.source_name = self.tables['Headers']['Lobbyist name'][1]


    def get_campaign_contributions(self):
        table_name = 'Campaign Contributions'
        columns = ['Date','Recipient name','Office sought','Amount']
        table_start = r"".join(columns)
        table_end = "\xa0\xa0Total contributions"

        query_results = self.query_page(table_start, table_end)
        for query_result in query_results:
            contributions_df = create_table(query_result, columns)
            contributions_df['Lobbyist name'] = self.source_name
            self.update_table(table_name, contributions_df)


    def add_identifiers_to_activities_table(self, query_result, dataframe):
        dataframe['Client'] = query_result[0].split('\n')[0]
        dataframe['Lobbyist'] = self.source_name
        return dataframe



class EntityDataPage(DataPage):

    activities_query = r'Lobbyist: '


    def __init__(self, html):
        DataPage.__init__(self,html)


    def get_source_name(self):
        self.source_name = self.tables['Headers']['Business name'][1]


    def add_identifiers_to_activities_table(self, query_result, dataframe):
        dataframe['Client'] = query_result.split('\n')[0]
        dataframe['Lobbyist'] = query_result.split('\n')[2]
        return dataframe


    def get_campaign_contributions(self):
        table_name = 'Campaign Contributions'
        columns = ['Date','Lobbyist name','Recipient name','Office sought','Amount']
        table_start = "".join(columns)
        table_end = "\xa0\xa0Total contributions"

        query_results = self.query_page(table_start, table_end)
        for query_result in query_results:
            contributions_df = create_table(query_result, columns)
            self.update_table(table_name, contributions_df)




## functions to build the above classes from a list of urls or html files
def convert_html_list(html_list):
    page_list = []
    for i, html in enumerate(html_list):
        print(f'converting html index {i} into data page')
        if 'Lobbyist Entity' in str(html):
            page_list.append(EntityDataPage(html))
        else:
            page_list.append(LobbyistDataPage(html))
    return page_list

def extract_and_save(html_list):
    page_list = convert_html_list(html_list)
    for page in page_list:
        page.save()

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
