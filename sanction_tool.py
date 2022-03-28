import streamlit as st
import pandas as pd
import numpy as np
from matching_utils import f_name_match_score
from utils import uk_sanction_list
import itertools

st.header("Inchcape Supplier Sanctions Checker")


# Entity matching based on sanction list and entered name by user
@st.cache
def entity_matching(search_name, uk_sanction_list):
    t_dict = {}
    for j,cc in zip(uk_sanction_list['Name 6'],uk_sanction_list['Unique ID']):
        if j not in t_dict.keys():
            t_dict[j,cc] = int(f_name_match_score(search_name, j))
    
    lst = list(t_dict.items())
    df = pd.DataFrame(lst,columns=["sanction name","Score"])
    df[["Match","Country Code"]] = pd.DataFrame(
        df["sanction name"].tolist(),
        index=df.index
    )
    df.drop(df.columns[0],axis=1,inplace=True)
    df.drop_duplicates(keep="first",inplace=True)
    return df




# search for the name
search_name = st.text_input("Enter Supplier Name", "")
button_clicked = st.button("Search")
st.markdown("---")
if button_clicked:
    matched = entity_matching(search_name, uk_sanction_list)
    top_match = matched.loc[matched["Score"] >= 95]
    if top_match.empty == False:
        top_match = top_match.sort_values("Score", ascending=False)
        # st.header("Top Match")
        # st.write(top_match['Match'])
        st.markdown(
            f"<h5 style='text-align: left; width:80%; padding: 20px; border-radius: 5px; color: black; background-color:rgba(173,216,230,.8); margin:0px;'> \
                        <b> Top Match </b> \
                        <ul> \
                        <li>Sanctioned Name : {top_match['Match'].iloc[0]}</li> \
                        <li>Country Code : {top_match['Country Code'].iloc[0]}</li> \
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
        (matched["Score"] >= 60) & (matched["Score"] < 95)
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
                    + most_probable_match["Country Code"].iloc[i]
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
                    + most_probable_match["Country Code"].iloc[j]
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
# 25th march updated code for upload function
def entity_matching_for_upload(supplier_list, uk_sanction_data):
    def join_with_space(x): 
        return("$".join(x))
    
    supplier_list = supplier_list["Display Name"].tolist()
    uk_sanction = list(zip(uk_sanction_data["Name 6"].tolist(),uk_sanction_data["Unique ID"].tolist()))
    cross_prod = list(itertools.product(supplier_list, uk_sanction))
    t_dict = {}
    
    for i in cross_prod:
        t_dict[i] = int(f_name_match_score(i[0], i[1][0]))
    print("Score calculation time")
    lst = list(t_dict.items())
    df1 = pd.DataFrame(lst, columns=["Supp Name", "Score"])
    df1[["Supplier Name", "Sanctioned and Country Code"]] = pd.DataFrame(
        df1["Supp Name"].tolist(), 
        index=df1.index
    )
    df1[["Sanctioned Name", "Country Code"]] = pd.DataFrame(
        df1["Sanctioned and Country Code"].tolist(), 
        index=df1.index
    )
    df1.drop(df1.columns[[0,3]],axis=1,inplace=True)
    #df1.to_csv('test100.csv')
    df1 = df1.sort_values(['Supplier Name','Score'],ascending=False).groupby('Supplier Name').head(5)
    
    
    df1['All data'] = np.where(df1['Score']>95,
                               df1['Sanctioned Name'] + "!" + df1['Country Code'] + "!" + df1['Score'].astype(str),
                               "! !")
    
    df1 = df1.groupby("Supplier Name")["All data"].agg(join_with_space)
    df1 = df1.reset_index()
    
    final_res = df1.join(df1['All data'].str.split('$', expand=True).rename(
            columns={0:'A', 1:'B', 2:'C', 3:'D', 4:'E'}
        )
    )
    
    final_res.drop("All data", axis=1, inplace=True)
    
    # Match1
    final_res = final_res.join(final_res['A'].str.split('!', expand=True).rename(
            columns={0:'Sanctioned Name 1', 1:'Country Code 1', 2:'Score 1'}
        )
    )
    final_res.drop("A", axis=1, inplace=True)
    
    # Match2
    final_res = final_res.join(final_res['B'].str.split('!', expand=True).rename(
            columns={0:'Sanctioned Name 2', 1:'Country Code 2', 2:'Score 2'}
        )
    )
    final_res.drop("B", axis=1, inplace=True)
    
    # Match3
    final_res = final_res.join(final_res['C'].str.split('!', expand=True).rename(
            columns={0:'Sanctioned Name 3', 1:'Country Code 3', 2:'Score 3'}
        )
    )
    final_res.drop("C", axis=1, inplace=True)
    
    # Match4
    final_res = final_res.join(final_res['D'].str.split('!', expand=True).rename(
            columns={0:'Sanctioned Name 4', 1:'Country Code 4', 2:'Score 4'}
        )
    )
    final_res.drop("D", axis=1, inplace=True)
    
    # Match5
    final_res = final_res.join(final_res['E'].str.split('!', expand=True).rename(
            columns={0:'Sanctioned Name 5', 1:'Country Code 5', 2:'Score 5'}
        )
    )
    final_res.drop("E", axis=1, inplace=True)
    final_res = final_res.set_index("Supplier Name")
    
    return final_res.to_csv()


# Upload a supplier list

uploaded_file = st.file_uploader(
    "If you have a list of suppliers in a .csv file, Please upload below", type="csv"
)
if uploaded_file is not None:
    st.write("File uploaded")
    dataframe = pd.read_csv(uploaded_file)
    st.write("Wait for the result")
    out_file = entity_matching_for_upload(dataframe, uk_sanction_list)
    st.download_button("Download CSV", out_file, "sanctioned_list.csv", "text/csv")
    st.write("Complete")
