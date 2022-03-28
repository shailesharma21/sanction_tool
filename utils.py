import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import streamlit as st
from pandas_ods_reader import read_ods
from config import sanction_file_name


# load uk sanction list
@st.cache
def uk_sanction_data_load(sanctions_file):
    scrape_uk_sanctions()
    df2 = read_ods(sanctions_file)
    df2 = df2.iloc[1:]
    df2.columns = df2.iloc[0]
    df2 = df2.drop(df2.index[0])
    #uk_sanctions = df2.loc[df2['Unique ID'].str.startswith('RUS')]
    uk_sanctions = df2.loc[df2['Individual, Entity, Ship']=='Entity']
    return uk_sanctions


@st.cache
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


@st.cache
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

# load uk sanctioned data
uk_sanction_list = uk_sanction_data_load(sanction_file_name)