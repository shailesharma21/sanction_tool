import streamlit as st
import pandas as pd
import numpy as np
import re
from fuzzywuzzy import fuzz
import jellyfish as jf 
from cleanco import basename
import requests
import itertools


st.title("Inchcape Sanction List Tool")

# Data scrapping from the uk govt website to get the latest sanction list
@st.cache
def data_scrap(url):
    filename = url.split('/')[-1]
    sl = requests.get(url, stream=True)
    f = open(filename,'wb')
    for chunk in sl.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)
    f.close()
    return

data_scrap('https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/1059386/UK_Sanctions_List.ods')


# load uk sanction list
@st.cache
def uk_sanction_data_load():
    df2 = pd.read_excel('UK_Sanctions_List.ods', engine='odf',skiprows=1,header=1)
    uk_sanctions = df2.loc[df2['Unique ID'].str.startswith('RUS')]
    uk_sanction = uk_sanctions.loc[uk_sanctions['Individual, Entity, Ship']=='Entity']
    return uk_sanction

@st.cache
def f_get_modified_str(input_str):
    # Transform to lower case
    input_str = input_str.strip().lower()
    # Replace '&' char to word 'and'
    input_str = input_str.replace(' & ', ' and ')
    # Remove all other special chars
    input_str = " ".join(re.findall("[a-zA-Z0-9]+", input_str))
    # Remove extra spaces
    input_str = " ".join(input_str.split())
    return input_str.strip()

# Function to decode any string type to unicode
@st.cache
def to_unicode(obj, encoding='utf-8'):
    if not isinstance(obj, str):
        return obj.decode(encoding, errors='ignore')
    return obj

@st.cache
def name_match(name1, name2):
    name1 = name1.split()
    name2 = name2.split()
    if name1 and name2:
        ratio1 = 0.0
        for i in range(len(name1)):
            for j in range(i, len(name2)):
                if fuzz.ratio(name1[i], name2[j]) > 90:
                    ratio1 += 1.0
                    break
        try:
            ratio1 = 100 * (ratio1 / len(name1))
        except ZeroDivisionError:
            ratio1 = 0.0
        ratio2 = 0.0
        for i in range(len(name2)):
            for j in range(i, len(name1)):
                if fuzz.ratio(name2[i], name1[j]) > 90:
                    ratio2 += 1.0
                    break
        try:
            ratio2 = 100 * (ratio2 / len(name2))
        except ZeroDivisionError:
            ratio2 = 0.0
        return int(max(ratio1, ratio2))
    return 0

# Function to calculate fuzzy match score for two given strings
@st.cache
def f_name_match_score(str1, str2):
    # Transform name
    if len(str1) > 1 and len(str2) > 1:
        str1 = f_get_modified_str(str1)
        str2 = f_get_modified_str(str2)
        # Convert to unicode to avoid error
        str1 = to_unicode(str1)
        str2 = to_unicode(str2)
        # Compute match scores
        score1 = fuzz.ratio(str1, str2)
        score2 = fuzz.token_sort_ratio(str1, str2)
        score3 = jf.levenshtein_distance(str1,str2)
        score3 = (1-(score3/max(len(str1),len(str2))))*100
        #score4 = name_match(str1, str2)
        if len(str1.split()) == 1:
            score4 = fuzz.ratio(str1.split()[0], str2.split()[0])
        s_max = max(score1, score2, score3)
    else:
        s_max = 0
    return s_max


# clean the entity names i.e. remove special character from name and legal entities
@st.cache
def clean_company_legal_entities(entity_name):
    rp = ['LLC','PJSC','CJSC','IP','GUP','OJSC','JSC','OOO','OO','Limited Liability Company','Open Joint Stock Company','Joint-Stock Company','Public Joint Stock Company','Joint Stock Company','Joint-stock company','AO']
    for k in rp:
        if k in entity_name:
            entity_name = entity_name.replace(k,'')
    # Using basename twice for better clean
    entity_name = basename(entity_name)
    entity_name = basename(entity_name)
    # Remove all other special chars
    entity_name = " ".join(re.findall("[a-zA-Z0-9]+", entity_name))
    # Remove extra spaces
    entity_name = " ".join(entity_name.split())
    return entity_name.strip()

# Entity matching based on sanction list and entered name by user
#@st.cache
def entity_matching(search_name, uk_sanction_list):    
    df = pd.DataFrame(columns=['Match','Score'])
    t_dict={}
    sorted_dict = {}
    search_name = clean_company_legal_entities(search_name)
    for j in uk_sanction_list['Name 6']:
        j = clean_company_legal_entities(j)
        if j not in t_dict.keys():
            t_dict[j] = f_name_match_score(search_name,j)
    sorted_dict = sorted(t_dict.items(),key = lambda kv: kv[1],reverse=True)
    lst = sorted_dict[:5]
    for i in range(0,len(lst)):
        df = df.append({'Match':lst[i][0],'Score':lst[i][1]},ignore_index=True)
        df = df[~df.index.duplicated(keep='first')]  
    return df

# load uk sanctioned data
uk_sanction_list = uk_sanction_data_load()

# search for the name
search_name = st.text_input("Enter Supplier Name","")
button_clicked = st.button("Search")
if button_clicked:
    matched = entity_matching(search_name,uk_sanction_list)
    top_match = matched.loc[matched['Score']>95]
    if top_match.empty == False:
        top_match = top_match.sort_values('Score',ascending=False)
        #st.header("Top Match")
        #st.write(top_match['Match'])
        st.markdown(
                    f"<h5 style='text-align: left; width:80%; padding: 20px; border-radius: 5px; color: black; background-color:rgba(173,216,230,.8); margin:0px;'> \
                        <b> Top Match </b> \
                        <ul> \
                        <li>Sanctioned Name : {top_match['Match'].iloc[0]}</li> \
                        <li>Score : {top_match['Score'].iloc[0]}</li> \
                        </ul> \
                    </h5> \
                    ",
                    unsafe_allow_html=True
                    )
    else:
        st.markdown(
                    f"<h5 style='text-align: left; width:80%; padding: 20px; border-radius: 5px; color: black; background-color:rgba(173,216,230,.8); margin:0px;'> \
                        <b> Top Match </b> \
                        <ul> \
                        <li>No Match</li> \
                        </ul> \
                    </h5> \
                    ",
                    unsafe_allow_html=True
                    )
    most_probable_match = matched.loc[(matched['Score']>20) & (matched['Score']<=100)]
    st.title("")
    if most_probable_match.empty == False:
        most_probable_match = most_probable_match.sort_values('Score',ascending=False)
        #st.header("Most Probable Match")
        #st.write(most_probable_match['Match'])
        probable_match = ''
        if len(most_probable_match.index)>10:
            for i in range(10):
                probable_match += "Name: " + most_probable_match['Match'].iloc[i] + ', Score: ' + str(most_probable_match['Score'].iloc[i]) + "<br>"
                #st.write(probable_match)
        else:
            for j in range(0,len(most_probable_match.index)):
                probable_match += "Name: " + most_probable_match['Match'].iloc[j] + ', Score: ' + str(most_probable_match['Score'].iloc[j]) + "<br>"
                #st.write(probable_match)
        st.markdown(
                    f"<h5 style='text-align: left; width:80%; padding: 20px; border-radius: 5px; color: black; background-color:#F4C2C2; margin:0px;'> \
                        <b> Probable Match </b> \
                        <ul> \
                        <li>{probable_match}</li> \
                        </ul> \
                    </h5> \
                    ",
                    unsafe_allow_html=True
                    )
    else:
        st.markdown(
                    f"<h5 style='text-align: left; width:8  0%; padding: 20px; border-radius: 5px; color: black; background-color:#F4C2C2; margin:0px;'> \
                        <b> Probable Match </b> \
                        <ul> \
                        <li>No Match</li> \
                        </ul> \
                    </h5> \
                    ",
                    unsafe_allow_html=True
                    )

# function for uploaded supplier list
#@st.cache
def entity_matching_for_streamlit(supplier_list,uk_sanction_list):
    supplier_list = supplier_list['Display Name'].tolist()
    supplier_list = [clean_company_legal_entities(x) for x in supplier_list]
    uk_sanction = uk_sanction_list['Name 6'].tolist()
    uk_sanction = [clean_company_legal_entities(x) for x in uk_sanction]
    cross_prod = list(itertools.product(supplier_list,uk_sanction))  
    t_dict={}
    for i in cross_prod:
        t_dict[i] = f_name_match_score(i[0],i[1])
    lst = list(t_dict.items())
    df1 = pd.DataFrame(lst,columns=['Supp Name','Score'])
    df1[['Supplier Name','Sanctioned Name']] = pd.DataFrame(df1['Supp Name'].tolist(),index=df1.index)
    df1['Match Found'] = np.where(df1['Score']>95,'Yes','No')
    df1['Sanctioned Org Name'] = np.where(df1['Score']>95,df1['Sanctioned Name'],'')
    df1.drop(df1.columns[[0,1,3]],axis=1,inplace=True)
    df1.drop_duplicates(keep='first',inplace=True)
    df1 = df1.set_index('Supplier Name')
    return df1.to_csv()

# Upload a supplier list
uploaded_file = st.file_uploader("Choose a file",type='csv')
if uploaded_file is not None:
    st.write("File uploaded")
    dataframe = pd.read_csv(uploaded_file)
    st.write("Wait for the result")
    out_file = entity_matching_for_streamlit(dataframe,uk_sanction_list)
    st.download_button('Download CSV', out_file,'sanctioned_list.csv', 'text/csv')
    st.write("Complete")