import streamlit as st
import pandas as pd
import numpy as np
from matching_utils import f_name_match_score
from utils import scrape_uk_sanctions
import requests
import itertools
from pandas_ods_reader import read_ods


st.header("Inchcape Supplier Sanctions Checker")


# load uk sanction list
@st.cache
def uk_sanction_data_load(sanctions_file):
    df2 = read_ods(sanctions_file)
    df2 = df2.iloc[1:]
    df2.columns = df2.iloc[0]
    df2 = df2.drop(df2.index[0])
    #uk_sanctions = df2.loc[df2['Unique ID'].str.startswith('RUS')]
    uk_sanctions = df2.loc[df2['Individual, Entity, Ship']=='Entity']
    return uk_sanctions

# load uk sanctioned data
scrape_uk_sanctions()
uk_sanction_list = uk_sanction_data_load("UK_Sanctions_List.ods")

# Entity matching based on sanction list and entered name by user
# @st.cache
def entity_matching(search_name, uk_sanction_list):
    df = pd.DataFrame(columns=["Match", "Score"])
    t_dict = {}
    sorted_dict = {}
    for j in uk_sanction_list["Name 6"]:
        if j not in t_dict.keys():
            t_dict[j] = f_name_match_score(search_name, j)
    sorted_dict = sorted(t_dict.items(), key=lambda kv: kv[1], reverse=True)
    lst = sorted_dict[:5]
    for i in range(0, len(lst)):
        df = df.append({"Match": lst[i][0], "Score": lst[i][1]}, ignore_index=True)
        df = df[~df.index.duplicated(keep="first")]
    return df




# search for the name
search_name = st.text_input("Enter Supplier Name", "")
button_clicked = st.button("Search")
st.markdown("---")
if button_clicked:
    matched = entity_matching(search_name, uk_sanction_list)
    top_match = matched.loc[matched["Score"] > 95]
    if top_match.empty == False:
        top_match = top_match.sort_values("Score", ascending=False)
        # st.header("Top Match")
        # st.write(top_match['Match'])
        st.markdown(
            f"<h5 style='text-align: left; width:80%; padding: 20px; border-radius: 5px; color: black; background-color:rgba(173,216,230,.8); margin:0px;'> \
                        <b> Top Match </b> \
                        <ul> \
                        <li>Sanctioned Name : {top_match['Match'].iloc[0]}</li> \
                        <li>Score : {top_match['Score'].iloc[0]}</li> \
                        </ul> \
                    </h5> \
                    ",
            unsafe_allow_html=True,
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
            unsafe_allow_html=True,
        )
    most_probable_match = matched.loc[
        (matched["Score"] > 20) & (matched["Score"] <= 100)
    ]
    st.title("")
    if most_probable_match.empty == False:
        most_probable_match = most_probable_match.sort_values("Score", ascending=False)
        # st.header("Most Probable Match")
        # st.write(most_probable_match['Match'])
        probable_match = ""
        if len(most_probable_match.index) > 10:
            for i in range(10):
                probable_match += (
                    "Name: "
                    + most_probable_match["Match"].iloc[i]
                    + ", "
                    + str(most_probable_match["Score"].iloc[i])
                    + "<br>"
                )
                # st.write(probable_match)
        else:
            for j in range(0, len(most_probable_match.index)):
                probable_match += (
                    "Name: "
                    + most_probable_match["Match"].iloc[j]
                    + ", "
                    + str(most_probable_match["Score"].iloc[j])
                    + "<br>"
                )
                # st.write(probable_match)
        st.markdown(
            f"<h5 style='text-align: left; width:80%; padding: 20px; border-radius: 5px; color: black; background-color:#F4C2C2; margin:0px;'> \
                        <b> Probable Match </b> \
                        <ul> \
                        <li>{probable_match}</li> \
                        </ul> \
                    </h5> \
                    ",
            unsafe_allow_html=True,
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
            unsafe_allow_html=True,
        )

# function for uploaded supplier list
# @st.cache
def entity_matching_for_streamlit(supplier_list, uk_sanction_list):
    supplier_list = supplier_list["Display Name"].tolist()
    uk_sanction = uk_sanction_list["Name 6"].tolist()
    cross_prod = list(itertools.product(supplier_list, uk_sanction))
    t_dict = {}
    for i in cross_prod:
        t_dict[i] = f_name_match_score(i[0], i[1])
    lst = list(t_dict.items())
    df1 = pd.DataFrame(lst, columns=["Supp Name", "Score"])
    df1[["Supplier Name", "Sanctioned Name"]] = pd.DataFrame(
        df1["Supp Name"].tolist(), index=df1.index
    )
    df1["Match Found"] = np.where(df1["Score"] > 95, "Yes", "No")
    df1["Sanctioned Org Name"] = np.where(df1["Score"] > 95, df1["Sanctioned Name"], "")
    df1.drop(df1.columns[[0, 1, 3]], axis=1, inplace=True)
    df1.drop_duplicates(keep="first", inplace=True)
    df1 = df1.set_index("Supplier Name")
    return df1.to_csv()


# Upload a supplier list

uploaded_file = st.file_uploader(
    "If you a list of suppliers in a .csv file, Please upload below", type="csv"
)
if uploaded_file is not None:
    st.write("File uploaded")
    dataframe = pd.read_csv(uploaded_file)
    st.write("Wait for the result")
    out_file = entity_matching_for_streamlit(dataframe, uk_sanction_list)
    st.download_button("Download CSV", out_file, "sanctioned_list.csv", "text/csv")
    st.write("Complete")
