import os
import pandas as pd
import requests
from bs4 import BeautifulSoup as bs

class LobbyingDataPage:
    lobbying_file = 'lobbying/data/lobbying.csv'
    compensation_file = 'lobbying/data/compensation.csv'
    contributions_file = 'lobbying/data/contributions.csv'

    def __init__(self, html):
        self.html = html
        self.soup = bs(self.html,'html.parser')

        self.is_entity = bool(self.soup.find('span', {'id': 'ContentPlaceHolder1_ERegistrationInfoReview1_lblEntityCompany'}))

        self.company_name = self.get_company_name()
        self.date_range = self.get_date_range()

        if (self.soup.find('tr', {'class': 'GridHeader'})):
            self.lobbying_data = self.extract_lobbying_data()
            self.compensation_data = self.extract_compensation_data()
            self.contributions_data = self.extract_contributions_data()

        else:
            self.lobbying_data = pd.DataFrame()
            self.compensation_data = pd.DataFrame()
            self.contributions_data = pd.DataFrame()

    def get_date_range(self):
        return self.soup.find('span', {'id': 'ContentPlaceHolder1_lblYear'}).text

    def get_company_name(self):
        if self.is_entity:
            return self.soup.find('span', {'id': 'ContentPlaceHolder1_ERegistrationInfoReview1_lblEntityCompany'}).text
        else:
            return self.soup.find('span', {'id': 'ContentPlaceHolder1_LRegistrationInfoReview1_lblLobbyistCompany'}).text

    def prep_tables(self):
        some_tables = self.soup.find_all('tr', {'style': 'vertical-align: top'})

        #Extract tables that contain the word 'lobbyist' and split at that word
        if 'Lobbyist name' in some_tables[0].text:
            split_tables = [table for table in some_tables if 'Client: ' in table.text][0].text.split('Client: ')
        else:
            split_tables = [table for table in some_tables if 'Lobbyist: ' in table.text][0].text.split('Lobbyist: ')
        #Strip out junk
        the_tables = [entry for entry in split_tables if entry.strip() and 'House / Senate' in entry]

        clean_tables = []
        for table in the_tables:
            clean_table = [line for line in table.split('\n') if line] # divide by lines and remove empties
            clean_table = clean_table[:clean_table.index('\xa0\xa0\xa0')] # Remove ending cruft
            clean_tables.append(clean_table)

        return clean_tables

    def extract_lobbying_data(self):
        if self.soup.find('span', {'id': 'ContentPlaceHolder1_LRegistrationInfoReview1_lblIncidental'}):
            return pd.DataFrame()
        clean_tables = self.prep_tables()
        row_dicts = []

        for table in clean_tables:
            lobbyist_name = table[0].strip()
            client_name = table[2].strip()
            table_start_index = table.index('House / SenateBill Number or Agency NameBill title or activityAgent positionAmountDirect business association')+1
            table_data = table[table_start_index:]

            i=0
            while i <= len(table_data)-8:
                row_dicts.append({'LobbyingEntity': self.company_name,
                                'DateRange': self.date_range,
                                'Lobbyist': lobbyist_name,
                                'Client': client_name,
                                'House/Senate': table_data[i].strip(),
                                'BillNumber':table_data[i+1].strip(),
                                'BillActivity':table_data[i+2].strip(),
                                'AgentPosition': table_data[i+3].strip(),
                                'Amount': table_data[i+5].strip(),
                                'DirectBusinessAssosciation': table_data[i+7].strip()})
                i=i+8
        return pd.DataFrame(row_dicts)

    def extract_contributions_data(self):

        bad_data = [element.split("Lobbyist: ")[0] for element in self.soup.text.split('Campaign Contributions') if "DateLobbyist nameRecipient nameOffice soughtAmount" in element]
        if not bad_data:
            print("NO DATA")
        pass1 = [element.split('Total contributions')[0] for element in bad_data]
        pass2 = [element.split('soughtAmount\n\n')[1:][0] for element in pass1]
        pass3 = "".join(pass2)
        data = [element.strip() for element in pass3.split('\n') if element.strip()]

        i = 0
        row_dicts = []
        while i < len(data):
            date = data[i].split()[0]
            lobbyist = " ".join(data[i].split()[1:])
            recipient = data[i+1]
            office = data[i+2]
            amount = data[i+3]
            row_dicts.append({  'LobbyingEntity': self.company_name,
                                'DateRange': self.date_range,
                                'Date': date,
                                'LobbyistName': lobbyist,
                                'RecipientName': recipient,
                                'OfficeSought': office,
                                'Amount': amount})
            i=i+4

        return pd.DataFrame(row_dicts)

    def extract_compensation_data(self):
        compensation_table = self.soup.find('table', {'id': 'ContentPlaceHolder1_DisclosureReviewDetail1_grdvClientPaidToEntity'})
        if not bool(compensation_table):
            return pd.DataFrame()
        temp_list = [line.strip() for line in compensation_table.text.split('\n') if line.strip()][1:-2]

        temp_dict_list = []
        for entry in temp_list:
            if entry[0] != '$':
                client_name = entry
            else:
                temp_dict_list.append({'LobbyingEntity': self.company_name, 'DateRange':self.date_range, 'Client': client_name, 'Amount':entry})
        return pd.DataFrame(temp_dict_list)

    def save(self):
        if not self.lobbying_data.empty:
            self.write_data(LobbyingDataPage.lobbying_file, self.lobbying_data)
        if not self.compensation_data.empty:
            self.write_data(LobbyingDataPage.compensation_file, self.compensation_data)
        if not self.contributions_data.empty:
            self.write_data(LobbyingDataPage.contributions_file, self.contributions_data)

    def write_data(self, file_path, dataframe):
        write = True
        if os.path.exists(file_path):
            with open(file_path, mode = 'r', encoding = 'utf-8') as f:
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

