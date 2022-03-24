import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re

def scrape_uk_sanctions():
    url = url_scrap()
    filename = "UK_Sanctions_List.ods"
    sl = requests.get(url, stream=True)
    f = open(filename, "wb")
    for chunk in sl.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
    f.close()
    return

def url_scrap():
    req = Request("https://www.gov.uk/government/publications/the-uk-sanctions-list")
    html_page = urlopen(req)
    soup = BeautifulSoup(html_page,'lxml')
    ls = []
    sanction_file = soup.findAll('div', attrs={'class':'attachment-details'})
    for div in sanction_file:
        ls.append(div.a['href'])
    r = re.compile(".*.ods")
    nw = list(filter(r.match,ls))
    return nw[0]
