from types import SimpleNamespace
from bs4 import BeautifulSoup as bs
import src.settings as settings
import psycopg2
import psycopg2.extras as extras
import requests
import os
import logging


class PageFactory:
    def __new__(cls, html=None, url=None):
        if not html:
            if not url:
                logging.exception("PageFactory requires either a url string or html file")
                return
            logging.debug(f'Pulling data from URL: {url}')
            html = PageFactory.pull_html(url)

        soup = bs(html, 'html.parser')
        if PageFactory.check_validity(soup, url):
            return DataPage(soup, url)

    def pull_html(url):
        headers={"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
        result = requests.get(url, headers=headers)
        result.raise_for_status()
        return result.content

    def check_validity(soup, url):
        if soup.h1 and soup.h1.text == 'An Error Occurred':
            logging.warning("Disclosure Report Not Found")
            if url:
                logging.warning(f"URL: {url}")
            return False
        return True


class DataPage:
    columns_dict =  {'campaign_contributions':
                        ['Date','lobbyist_name','Recipient name','Office Sought','Amount'],
                    'client_compensation':
                        ['Client name','Amount'],
                    'lobbying_activity':
                        ['Lobbyist name','Client name','House / Senate','Bill Number or Agency Name','Bill title or activity','Agent position','Compensation received','Direct business association'],

                    'pre_2016_lobbying_activity':
                        ['Activity or Bill No and Title','Lobbyist name','Agent position','Direct business association','Client name','Compensation received'],

                    'pre_2010_lobbying_activity':
                        ['Date','Activity or bill No and Title','Lobbyist name','Client name'],
                    'headers':
                        ['source_name','source_type','date_range','authorizing_officer_or_lobbyist_name','agent_type_or_title','business_name','address','city_state_zip_code','country', 'phone', 'url'],
                    'all':
                        ['header_id']}

    def __init__(self, soup, url = None):
        self.soup = soup
        self.url = url
        self.type = 'Entity' if 'Lobbyist Entity' in soup.text else 'Lobbyist'
        self.date_range = soup.find('span', id = lambda tag: tag and tag.startswith("ContentPlaceHolder1_lblYear")).text
        self.year = int(self.date_range[-4:])
        self.header = self.get_header_table()
        self.tables = self.get_all_tables()

    # gets all the tables
    def get_all_tables(self):
        tables = SimpleNamespace()
        # if self.year < 2010:
        #     tables.pre_2010_lobbying_activity = self.get_pre_2010_lobbying_activity()
        # elif self.year < 2016:
        #     tables.pre_2016_lobbying_activity = self.get_pre_2016_lobbying_activity()
        # else:
        #     tables.lobbying_activity = self.get_lobbying_activity()
        if 'DateActivity or Bill No and Title' in self.soup.text:
            tables.pre_2010_lobbying_activity = self.get_pre_2010_lobbying_activity()
        if "Agent's positionDirect business association with public officialClient representedCompensation received" in self.soup.text:
            tables.pre_2016_lobbying_activity = self.get_pre_2016_lobbying_activity()
        elif "House / SenateBill Number or Agency Name" in self.soup.text:
            tables.lobbying_activity = self.get_lobbying_activity()


        tables.campaign_contributions = self.get_generic_table("grdvCampaignContribution")
        if self.type == 'Lobbyist':
            for row in tables.campaign_contributions:
                row.insert(1, self.source_name)
        tables.client_compensation = self.get_generic_table("grdvClientPaidToEntity")
        return tables

    def get_header_table(self):
        #id_char = self.type[0]
        header_table = self.soup.find('div',id=lambda tag: tag and tag.startswith("ContentPlaceHolder1_pnl"))
        rows = header_table.findAll('tr')
        row_list = []
        for row in rows[:-1]: #last row is always blank idk
            cell = " ".join([result.text for result in row.findAll('span', id=lambda tag: tag and "RegistrationInfoReview1_lbl" in tag)])
            row_list.append(cell)
        if self.type == 'Lobbyist':
            row_list.insert(1, row_list.pop(5)) # Move the 'Agent Type' table to match up with the 'Position' index for entites
            self.source_name = row_list[0]
        else:
            self.source_name = row_list[2]
        row_list = self.add_source_to_row(row_list)
        row_list.append(self.url)
        return row_list

    def add_source_to_row(self, row_list):
        return [self.source_name, self.type, self.date_range] + row_list

    def get_generic_table(self, table_tag_includes, drop_last_row=True):
        table_list = []
        tables = self.soup.findAll('table', id = lambda tag: tag and table_tag_includes in tag)
        for table in tables:
            rows = table.findAll('tr', class_=lambda tag: tag and 'Grid' in tag and 'Header' not in tag)
            rows = rows[:-1] if drop_last_row else rows
            for row in rows[:-1]: #last row is total
                table_list.append(self.process_row(row))
        return table_list

    def process_row(self, row, starting_list = None):
        row_list = starting_list if starting_list else []
        cells = row.findAll('td')
        if cells:
            for cell in cells:
                row_list.append(cell.text.strip().replace('\n', '; '))
        # row_list = self.add_source_to_row(row_list)
        return row_list

    def get_lobbying_activity(self):
        table_text = "lblLobbyistName" if self.type == 'Entity' else "lblClientName"
        full_tables = self.soup.findAll('span',id = lambda tag: tag and table_text in tag)
        table_list = []
        for full_table in full_tables:
            lobbyist_name, client_name = self.assign_lobbyist_and_client_names(full_table)
            table = full_table.findNext('table').findNext('table')
            rows = table.findAll('tr', class_=lambda tag: tag and 'Grid' in tag and 'Header' not in tag)
            for row in rows:
                table_list.append(self.process_row(row, [lobbyist_name, client_name]))
        if table_list and 'No activities were disclosed for this reporting period.' in table_list[0]:
            return []
        return table_list

    def get_pre_2010_lobbying_activity(self):
        table = self.get_generic_table('grdvActivities', drop_last_row=False)
        if self.type == 'Lobbyist':
            for i in range(len(table)):
                table[i].insert(-1, self.source_name)
        return table

    def get_pre_2016_lobbying_activity(self):
        table = self.get_generic_table('grdvActivities', drop_last_row=False)
        if self.type == 'Lobbyist':
            for i in range(len(table)):
                table[i].insert(1, self.source_name)
        return table

    def assign_lobbyist_and_client_names(self, full_table):
        if self.type == 'Entity':
            return (full_table.text.replace('Lobbyist: ',""), full_table.findNext('span').text)
        else:
            return (self.header[0], full_table.text)

    def save(self, save_type='psql'):
        if save_type == 'psql':
            conn = psycopg2.connect(**settings.psql_params_dict)
            header_id = self.write_header_to_psql(conn)
            if header_id:
                for table_name in self.tables.__dict__.keys():
                    self.write_data_to_psql(table_name, header_id)

    def write_header_to_psql(self, conn):
        table = tuple(self.header)
        cols = ','.join([col.lower().replace(",","").replace(" ","_").replace('/','or') for col in DataPage.columns_dict['headers']])
        query = "INSERT INTO headers(%s) VALUES %%s" % (cols)
        with conn.cursor() as cursor:
            try:
                cursor.execute(query, (table,))
                conn.commit()
                logging.info(f"table successfully inserted into table 'headers'")
                query = 'select count(*) from headers;'
                cursor.execute(query)
                header_id = cursor.fetchone()[0]
                return header_id
            except (Exception, psycopg2.DatabaseError) as error:
                print(f"Error: {error} On table 'headers'")
                conn.rollback()
                cursor.close()
                return False

    def write_data_to_psql(self, table_name, header_id):
        conn = psycopg2.connect(**settings.psql_params_dict)
        table_list = self.tables.__dict__[table_name]
        for row in table_list:
            row.insert(0, str(header_id))
        table = [tuple(row) for row in table_list]
        cols = ','.join([col.lower().replace(",","").replace(" ","_").replace('/','or') for col in DataPage.columns_dict['all'] + DataPage.columns_dict[table_name]])
        query = "INSERT INTO %s(%s) VALUES %%s" % (table_name, cols)
        cursor = conn.cursor()
        try:
            extras.execute_values(cursor, query, table)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}On table {table_name}")
            conn.rollback()
            cursor.close()
            print( 1)
        logging.info(f"table successfully inserted into table '{table_name}'")
        cursor.close()
