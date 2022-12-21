from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def extract_client_links(year):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = 'https://www.sec.state.ma.us/LobbyistPublicSearch/Default.aspx'

    driver.get(url)

    driver.find_element('id','ContentPlaceHolder1_rdbSearchByType').click()
    select = Select(driver.find_element(By.CLASS_NAME,'p3'))

    select.select_by_value(year)
    Select(driver.find_element('id','ContentPlaceHolder1_ucSearchCriteriaByType_drpType')).select_by_value('L')
    driver.find_element('id','ContentPlaceHolder1_btnSearch').click()

    find_table = driver.find_element(By.ID,'ContentPlaceHolder1_ucSearchResultByTypeAndCategory_grdvSearchResultByTypeAndCategory')
    links = find_table.find_elements(By.TAG_NAME,'a')
    links_list = [l.get_attribute('href') for l in links if str(l.get_attribute('href')).startswith('javascript') == False]
    driver.quit()
    return links_list

def extract_disclosures(list_of_links):
    disclosure_reports = []

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    for link in list_of_links:
    # print(link)
        driver.get(link)
        all_links = driver.find_elements(By.CLASS_NAME,'BlueLinks')
        disclosure_links = [l.get_attribute('href') for l in all_links if 'CompleteDisclosure' in l.get_attribute('href')]
        for dl in disclosure_links:
            disclosure_reports.append(dl)
    driver.quit()

    return disclosure_reports
