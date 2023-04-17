# Wesley Fegan
# CS450

# School Ranking Project

import numpy as np
import os
from pandas import DataFrame
import pandas as pd
from plotly import data
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Filesystem variables:
scardpath = "./Clean College Scorecard Data/"
usnewspath = "./usnews/"
cachepath = "./cache/"

# Data and where to find it:
datastore = {
    "scard":{
        2009:scardpath+"MERGED2009_10_PP.csv",
        2010:scardpath+"MERGED2010_11_PP.csv",
        2011:scardpath+"MERGED2011_12_PP.csv",
        2012:scardpath+"MERGED2012_13_PP.csv",
        2013:scardpath+"MERGED2013_14_PP.csv",
        2014:scardpath+"MERGED2014_15_PP.csv",
        2015:scardpath+"MERGED2015_16_PP.csv",
        2016:scardpath+"MERGED2016_17_PP.csv",
        2017:scardpath+"MERGED2017_18_PP.csv",
        2018:scardpath+"MERGED2018_19_PP.csv"
    },
    "usnews":usnewspath+"USnews_ranking_1984_2023.xlsx"
    }

yearStart = 2009
yearEnd = 2018

# Stores the data loaded from disk:
dframes = {}

# Lowest maximum degree nice names:
highestDegNice = {
    "Non-degree-granting":0,
    "Certificate degree":1,
    "Associate degree":2,
    "Bachelor's degree":3,
    "Graduate degree":4
}

# Columns we would like to use in order to investigate the relationship between economic mobility and ranking.
paramsColumnsNice = {
    "Average net price for $0-$30,000 family income (public institutions)":"NPT41_PUB",
    "Average net price for $30,001-$48,000 family income (public institutions)":"NPT42_PUB",    
    "Average net price for $48,001-$75,000 family income (public institutions)":"NPT43_PUB",
    "Average net price for $75,001-$110,000 family income (public institutions)":"NPT44_PUB",
    "Average net price for $110,000+ family income (public institutions)":"NPT45_PUB"
    }
paramsColumns = list(paramsColumnsNice.values())

# Columns that are needed for other purposes.
keyColumns = ["INSTNM", "HIGHDEG", "UNITID"]

# List of every column we will use.
usecols = paramsColumns + keyColumns

# Remove entries (schools) which don't have the required data. This is done on a per-CSV basis.
def stripbad(df: DataFrame) -> DataFrame:
    # Remove institutions where HIGHDEG is empty.
    df = df[ (df["HIGHDEG"].notnull()) ]

    # Remove institutions where the params we are interested in are blank.
    for param in paramsColumns:
        df = df[ (df[param].notnull()) ]

    return df


# Load the data from disk. Initially the entire files are loaded, the required data is pulled out and written to 
# much smaller "cache" CSVs on disk. The long read only needs to happen once unless the program is modified or the 
# dataset is updated.
def loadschema():
    print("Loading data.")

    # Make the cache directory if it does not exist.
    if not os.path.isdir(cachepath):
        os.mkdir(cachepath)

    # Load College Scorecard data for each year.
    year = yearStart
    while year <= yearEnd:
        cachefile = cachepath + str(year) + ".csv"

        if not os.path.exists(cachefile):
            # Data is not cached, build our custom stripped tables from scratch.
            df = pd.read_csv(filepath_or_buffer=datastore["scard"][year], usecols=usecols)
            df = stripbad(df)
            df.to_csv(cachefile)
            print("Loaded " + datastore["scard"][year])
        # The data is cached, or we just created it. Load it now.
        dframes[year] = pd.read_csv(cachefile)
        print("[cache] Loaded " + cachefile)
        year += 1

    # Load US News rankings data.
    year = yearStart
    df = pd.read_excel(datastore["usnews"])
    while year <= yearEnd:
        cachefile = cachepath + "usnews" + str(year) + ".csv"
        if not os.path.exists(cachefile):
            # The ranking data has not been cached for the year in question.
            newDF = pd.DataFrame({
                "University Name":df["University Name"].to_list(),
                "US News Ranking":df[year].to_list(),
                "UNITID":df["UNITID"].to_list()
            })
            newDF.to_csv(cachefile)
            print("Loaded " + datastore["usnews"] + " for " + str(year))
        # The ranking data is cached, or we just created it. Load it now.
        dframes["usnews" + str(year)] = pd.read_csv(cachefile)
        print("[cache] Loaded " + cachefile)
        year += 1


def getTopNDF(n: int, param: str, year: int, maxDeg: int, hideOutsiders: bool) -> DataFrame:
    df = dframes[year]
    df = df[ (df["HIGHDEG"] >= maxDeg) ]
    df = df.sort_values(param, 0)

    ourRankings = np.arange(start=1, stop = df["INSTNM"].count() + 1, dtype=int).tolist()
    df["Our Ranking"] = ourRankings

    if hideOutsiders:
        USNewsDF = dframes["usnews" + str(year)]
        df = df[ (df["UNITID"].isin(USNewsDF["UNITID"])) ]

    df = df.head(n)
    return df

def dashboard():
    st.set_page_config(layout="wide", initial_sidebar_state="expanded")
    st.sidebar.header("School Ranking Dashboard")

    # Year selection:
    st.sidebar.subheader("Select which year's data you would like to see:")
    selYear = st.sidebar.slider("Year", min_value=yearStart, max_value=yearEnd, step=1)

    USNewsDF = dframes["usnews" + str(selYear)]

    # Parameter selection:
    st.sidebar.subheader("Economic mobility markers:")
    selParam = st.sidebar.selectbox("Column", tuple(paramsColumnsNice.keys()))
    selParamColName = paramsColumnsNice[selParam]

    # Maximum degree selection:
    st.sidebar.subheader(
        "Filter institutions by the highest degree earnable. Institutions not offering this degree will be removed. "
        "This can be used to filter out lower level schools."
    )
    selMaxDeg = highestDegNice[st.sidebar.selectbox("Highest degree earnable", tuple(highestDegNice.keys()))]

    # How many n? Effects only how many items are displayed, not how the schools are ranked.
    # Min: 10   Max: 195    Default: 10     Step: 1
    st.sidebar.subheader("Examine top N schools. Effects only how many schools are shown, not how they are ranked.")
    selN = st.sidebar.slider("N", 10, 195, 10, 1)

    # Hide institutions not in US News' list?
    st.sidebar.subheader("Hide institutions not in US News' rankings? This will not effect our ranking.")
    hideOutsiders = st.sidebar.checkbox("Hide", False)

    # Get top N schools based on the selected parameter and year.
    df = getTopNDF(selN, selParamColName, selYear, selMaxDeg, hideOutsiders)

    # Create a scatter plot.
    fig = px.scatter(df, y=selParamColName, x="INSTNM")
    fig.update_traces(marker_size=10)
    st.plotly_chart(fig, use_container_width=True)

    # Show table of top N schools, based on our rankings:
    ourTableDF = pd.DataFrame({
        "Our Ranking":df["Our Ranking"],
        "US News Ranking":[""]*df["INSTNM"].count(),
        "University Name":df["INSTNM"].tolist(),
        "UNITID":df["UNITID"].to_list()
    })

    # Put the US News rankings into the table.
    for value in USNewsDF.iterrows():
        try:            
            usnewsrank = int(USNewsDF.query("UNITID=="+str(value[1]["UNITID"]))["US News Ranking"].to_list()[0])
            ourTableDF.loc[ourTableDF["UNITID"] == value[1]["UNITID"], "US News Ranking"] = usnewsrank
        except Exception as e: 
            #print(e)
            ourTableDF.loc[ourTableDF["UNITID"] == value[1]["UNITID"], "US News Ranking"] = ""

    # We want a dumbbell plot to show the disparity between our ranking and US News' ranking.
    dumbbell_schools = ourTableDF["University Name"]
    dumbbell_data = {"line_x": [], "line_y": [], "Our Ranking": [], "US News Ranking": [], "colors": [], "Rank": [], "schools": []}
    for school in dumbbell_schools:
        dumbbell_data["Our Ranking"].extend(ourTableDF.loc[ourTableDF["University Name"] == school]["Our Ranking"])
        dumbbell_data["US News Ranking"].extend(ourTableDF.loc[ourTableDF["University Name"] == school]["US News Ranking"])
        dumbbell_data["line_x"].extend([
            ourTableDF.query("`University Name` == \"" + str(school) + "\"")["Our Ranking"].to_list()[0],
            ourTableDF.query("`University Name` == \"" + str(school) + "\"")["US News Ranking"].to_list()[0],
            None
        ])
        dumbbell_data["line_y"].extend([school, school, None])

    dumbbell_fig = go.Figure(
        [
            go.Scatter(
                x=dumbbell_data["line_x"],
                y=dumbbell_data["line_y"],
                mode="lines",
                showlegend=False,
                marker=dict(color="grey")
            ),
            go.Scatter(
                x=dumbbell_data["Our Ranking"],
                y=dumbbell_data["schools"],
                mode="markers",
                name="Our Ranking",
                marker=dict(
                    color="green",
                    size=10
                )
            ),
            go.Scatter(
                x=dumbbell_data["US News Ranking"],
                y=dumbbell_data["schools"],
                mode="markers",
                name="US News Ranking",
                marker=dict(
                    color="blue",
                    size=10
                )
            )            
        ]
    )

    dumbbell_fig.update_layout(
        title="Rankings Disparity",
        height=1000,
        legend_itemclick=False
    )

    st.plotly_chart(dumbbell_fig, use_container_width=True)

    # Don't show index in displayed table.
    hide_table_row_index = """
                <style>
                thead tr th:first-child {display:none}
                tbody th {display:none}
                </style>
                """
    st.markdown(hide_table_row_index, unsafe_allow_html=True)

    st.table(ourTableDF)


def main():
    print("Let's do some data science!")
    loadschema()
    dashboard()

main()
