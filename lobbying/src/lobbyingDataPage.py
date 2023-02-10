from settings import *
from utils import *
import os
import pandas as pd
from bs4 import BeautifulSoup as bs
import psycopg2
import psycopg2.extras as extras
import numpy as np



class DataPage:
    table_columns = {}
    activities_query = ""
    def __init__(self, html):
        self.has_error = False
        self.tables = {} # A dictionary that will hold all the tables as they are extracted
        self.soup = bs(html, 'html.parser')
        self.dfs = pd.read_html(html)

        if self.is_valid():
            self.get_header()
            self.get_date_range()
            self.get_source_name()
            logging.info(f'Got Header {self.source_name} {self.date_range}')
            self.scrape_tables()
            self.add_source()


    ## BEGIN INIT FUNCTIONS ##
    # returns true if the html is valid and processable
    def is_valid(self):
        if 'An Error Occurred' in self.soup.text:
            logging.exception('Page Error')
            return False
        return True


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
        logging.info(f"Lobbying Activity {bool('Activities' in self.tables.keys())}")
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


    def get_lobbying_activity(self):
        table_name = 'Activities'
        columns = ['House or Senate','Bill Number or Agency Name','Bill title or activity','Agent position','Amount','Direct business association']
        table_start = 'House / SenateBill Number or Agency NameBill title or activityAgent positionAmountDirect business association'
        table_end = r'\xa0\xa0\xa0\nTotal'

        #our first query has a wider scope so we can pull the client and lobbyist name
        query_results = self.query_page(self.activities_query, r' amount\n')# activities_query is different for individuals and lobbyists
        for query_result in query_results:
            activities_table = self.query_page(table_start, table_end, query_result)[0]
            anon_activities_df = divide_text(activities_table, columns)
            activities_df = self.add_identifiers_to_activities_table(query_result, anon_activities_df)
            self.update_table(table_name, activities_df)


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
            compensation_df = divide_text(query_result, columns)
            self.update_table(table_name, compensation_df)


    # This function adds the date range and entity / lobbyist name to each table
    def add_source(self):
        for table in self.tables.keys():
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
        conn = get_conn()
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
            contributions_df = divide_text(query_result, columns)
            contributions_df['Lobbyist name'] = self.source_name
            self.update_table(table_name, contributions_df)


    def add_identifiers_to_activities_table(self, query_result, dataframe):
        dataframe['Lobbyist name'] = self.source_name
        dataframe['Client name'] = query_result[0].split('\n')[0]
        return dataframe



class EntityDataPage(DataPage):

    activities_query = r'Lobbyist: '


    def __init__(self, html):
        DataPage.__init__(self,html)


    def get_source_name(self):
        self.source_name = self.tables['Headers']['Business name'][1]


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
            contributions_df = divide_text(query_result, columns)
            self.update_table(table_name, contributions_df)
