import requests
from lobbyingDataPage import LobbyingDataPage
from lobbyingScraper import extract_disclosures, extract_client_links

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
    extract_and_save(download_html_list(url_list))

if __name__ == "__main__":
    #disclosure_links = extract_disclosures(extract_client_links())
    #html_list = download_html_list(disclosure_links)
    extract_and_save(download_html_list(extract_disclosures(extract_client_links())))
