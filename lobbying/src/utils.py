
from settings import *
from lobbyingDataPage import LobbyistDataPage,EntityDataPage
import re
import psycopg2
import requests
import pandas as pd


def convert_html(html):
    if 'Lobbyist Entity' in str(html):
        return EntityDataPage(html)
    else:
        return LobbyistDataPage(html)


def get_conn():
    conn = psycopg2.connect(**params_dict)
    return conn


def divide_text(query_result, columns):
    # splits a list into a list of lists,
    # with the length of each inner list
    # equal to chunk_size
    def chunk_list(some_list,chunk_size):
            for i in range(0, len(some_list), chunk_size):
                yield some_list[i:i+chunk_size]
    split_text=[line.strip() for line in query_result.split('\n') if line.strip()]
    split_text = separate_date(split_text) #TODO i guess it's fine to run this for everything? idk tho, maybe just work it into exception handling
    divided_text = list(chunk_list(split_text, len(columns)))
    return create_table(divided_text, columns)


def create_table(divided_text, columns):
    try:
        table_df = pd.DataFrame(divided_text, columns=columns)
        return table_df
    except:
        dataframe_exception(divided_text, columns)


def dataframe_exception(divided_text, columns):
    logging.exception('DATAFRAME EXCPETION')
    logging.exception(divided_text)
    logging.exception(columns)
    # for i in range(len(divided_text)):
    #     divided_text[i] = separate_date(divided_text[i])
    # create_table(divided_text, columns)


def separate_date(data_row_list):
    new_list = []
    regex_string = r"^(\d+/\d+/\d+)\s?([\w\s/.]+)$"
    regex_query = re.compile(regex_string)
    for i in range(len(data_row_list)):
        result = re.fullmatch(regex_query, data_row_list[i])
        if result:
            new_list.append(result.group(1))
            new_list.append(result.group(2))
        else:
            new_list.append(data_row_list[i])
    return new_list


## functions to build the above classes from a list of urls or html files
def save_data_from_url_list(url_list, save_type = save_type):
    for i, url in enumerate(url_list):
        logging.info(f"url index: {i}\npulling data from {url}")
        download_extract_save(url, save_type=save_type)

def save_data_from_html_list(html_list, save_type=save_type):
    for i, html in enumerate(html_list):
        logging.info(f"pulling data from list index {i}")
        convert_html(html).save(save_type=save_type)

def download_extract_save(url, save_type = save_type):
    convert_html(pull_html(url)).save(save_type = save_type)




def pull_html(url):
    headers={"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
    result = requests.get(url, headers=headers)
    result.raise_for_status()
    return result.content
