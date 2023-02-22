from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import datetime

def get_lobbyist_urls(year, driver):
    year = str(year)
    url = 'https://www.sec.state.ma.us/LobbyistPublicSearch/Default.aspx'

    driver.get(url)

    ##setup the parameters and run the search
    lobbyist_radio_button = driver.find_element('id','ContentPlaceHolder1_rdbSearchByType')
    lobbyist_radio_button.click
    drop_down_boxes = driver.find_elements(By.CLASS_NAME,'p3')
    Select(drop_down_boxes[0]).select_by_value(year)
    Select(drop_down_boxes[-1]).select_by_index(0)
    Select(driver.find_element('id','ContentPlaceHolder1_ucSearchCriteriaByType_drpType')).select_by_value('L')
    driver.find_element('id','ContentPlaceHolder1_btnSearch').click()

    #get the links
    find_table = driver.find_element(By.ID,'ContentPlaceHolder1_ucSearchResultByTypeAndCategory_grdvSearchResultByTypeAndCategory')
    links = find_table.find_elements(By.TAG_NAME,'a')
    links_list = [l.get_attribute('href') for l in links if str(l.get_attribute('href')).startswith('javascript') == False]
    return links_list

def get_disclosure_urls(lobbyist_url, driver):
    disclosure_report_urls = []
    driver.get(lobbyist_url)
    all_links = driver.find_elements(By.CLASS_NAME,'BlueLinks')
    disclosure_links = [l.get_attribute('href') for l in all_links if 'CompleteDisclosure' in l.get_attribute('href')]

    for disclosure_link in disclosure_links:
        disclosure_report_urls.append(disclosure_link)

    return disclosure_report_urls

def get_disclosures_by_year(year):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    lobbyist_urls = get_lobbyist_urls(year, driver)
    disclosure_urls = []
    for url in lobbyist_urls:
        results = get_disclosure_urls(url, driver)
        for result in results:
            disclosure_urls.append(result)
    return disclosure_urls

def get_latest_disclosures():
    year = datetime.date.today().year
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    lobbyist_urls = get_lobbyist_urls(year, driver)
    disclosure_urls = []
    for url in lobbyist_urls:
        results = get_disclosure_urls(url, driver)
        if results:
            disclosure_urls.append(results[-1])
    return disclosure_urls
