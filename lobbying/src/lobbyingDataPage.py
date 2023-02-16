from types import SimpleNamespace
from bs4 import BeautifulSoup as bs
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
    columns_dict =      {'campaign_contributions':
                            ['Date','Recipient name','Office Sought','Amount'],
                        'lobbying_activity':
                            ['Lobbyist name','Client name','House / Senate','Bill Number or Agency Name','Bill title or activity','Agent position','Amount','Direct business association'],
                        'client_compensation':
                            ['Client name','Amount'],
                        'pre2020_lobbying_activity':
                            ['Date','Activity or bill No and Title','Lobbyist name','Client represented'],
                        'headers':
                            ['authorizing_officer_or_lobbyist_name','agent_type_or_title','business_name','address','city_state_zip_code','country', 'phone'],
                        'all':
                            ['source_name', 'date_range', 'source_type']}

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
        if self.year >= 2020:
            tables.lobbying_activity = self.get_lobbying_activity()
        else:
            tables.pre2020_lobbying_activity = self.get_generic_table('grdvActivities', drop_last_row=False)

        tables.campaign_contributions = self.get_generic_table("grdvCampaignContribution", DataPage.columns_dict['campaign_contributions'])
        tables.client_compensation = self.get_generic_table("grdvClientPaidToEntity", DataPage.columns_dict['client_compensation'])
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
        return row_list

    def add_source_to_row(self, row_list):
        return [self.source_name, self.date_range, self.type] + row_list

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
        row_list = self.add_source_to_row(row_list)
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
        return table_list

    def assign_lobbyist_and_client_names(self, full_table):
        if self.type == 'Entity':
            return (full_table.text.replace('Lobbyist: ',""), full_table.findNext('span').text)
        else:
            return (self.header[0], full_table.text)

    def save(self, save_type='psql'):
        if save_type == 'psql':
            for table_name in self.tables.__dict__.keys():
                self.write_data_to_psql(table_name)

    def write_data_to_psql(self, table_name):
        params_dict = {
            'host'      : 'localhost',
            'port'      : '5432',
            'database'  : 'maple_lobbying',
            'user'      : 'geekc',
            'password'  : 'asdf'
        }
        conn = psycopg2.connect(**params_dict)
        table = [tuple(row) for row in self.tables.__dict__[table_name]]
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
            return 1
        logging.info(f"table successfully inserted into table '{table_name}'")
        cursor.close()
