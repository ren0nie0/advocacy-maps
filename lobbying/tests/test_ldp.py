from lobbying.src.lobbyingDataPage import LobbyingDataPage
from test_data import *

def test_headers():
    for html in test_htmls:
        ldp = LobbyingDataPage(html)
        tables = ldp.fetch_tables()
        print('Lobbyists' in tables.keys() or 'Entities' in tables.keys())

test_headers()
