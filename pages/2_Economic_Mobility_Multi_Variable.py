# Wesley Fegan
# CS450

# School Ranking Project

import numpy as np
import os
from pandas import DataFrame
import pandas as pd
import plotly as pt
from plotly import data
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import lib

dframes = lib.dframes
yearStart = lib.yearStart
yearEnd = lib.yearEnd
paramsColumnsNice = lib.paramsColumnsNice
paramsColumns = lib.paramsColumns
highestDegNice = lib.highestDegNice
lowerIsBetter = lib.lowerIsBetter

def getTopNDF(n: int, param: dict, year: int, maxDeg: int, hideOutsiders: bool) -> DataFrame:

    global dframes
    global paramsColumns
    global lowerIsBetter

    weightsTotal = 0.000001 # Don't divide by 0 on initial run.
    for key in param.keys():
        weightsTotal += param[key]

    df = dframes[year]
    df = df[ (df["HIGHDEG"] >= maxDeg) ]

    # Normalize data using min-max feature scaling.
    for column in paramsColumns:
        df[column] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())

    # If higher is better, subract 1 from normalized values to reverse the scale.
    for column in param.keys():
        if not lowerIsBetter[column]: 
            df[column] = 1.0 - df[column]

    ourRankDF = pd.DataFrame({
        "INSTNM":df["INSTNM"],
        "UNITID":df["UNITID"],
        #"Our Ranking":[0]*df["INSTNM"].count(),
        "aggregateScore":[0.0]*df["INSTNM"].count()
    })
    
    # Add the normalized columns to the output DataFrame.
    for column in param.keys():
        ourRankDF[column] = df[column]

    for school in df["UNITID"]:
        aggScoreNum = 0.0
        for key in param.keys():
            aggScoreNum += param[key] * df.query("UNITID==" + str(school))[key]
        ourRankDF.loc[ourRankDF.eval("UNITID==" + str(school)), "aggregateScore"] = aggScoreNum / weightsTotal

    ourRankDF = ourRankDF.sort_values("aggregateScore", 0, ascending=True)

    ourRankings = np.arange(start=1, stop = df["INSTNM"].count() + 1, step=1).tolist()
    ourRankDF["Our Ranking"] = ourRankings
    #print(ourRankDF["Our Ranking"])

    if hideOutsiders:
        USNewsDF = dframes["usnews" + str(year)]
        ourRankDF = ourRankDF[ (ourRankDF["UNITID"].isin(USNewsDF["UNITID"])) ]

    if n != 0:
        ourRankDF = ourRankDF.head(n)
    return ourRankDF

def dashboard():

    global dframes
    global yearStart
    global yearEnd
    global paramsColumnsNice
    global highestDegNice

    st.sidebar.header("School Ranking Dashboard")

    # Year selection:
    st.sidebar.subheader("Select which year's data you would like to see:")
    selYear = st.sidebar.number_input("Year (" + str(yearStart) + "-" + str(yearEnd) + ")", min_value=yearStart, max_value=yearEnd, value=yearEnd, step=1)

    USNewsDF = dframes["usnews" + str(selYear)]

    # Parameter selection:
    st.sidebar.subheader("Economic mobility markers:")

    paramCheck = {}
    paramWeight = {}
    colLeft, colRight = st.columns(2)
    for key in paramsColumnsNice.keys():
        attr = paramsColumnsNice[key]
        with colLeft:
            paramCheck[attr] = st.sidebar.checkbox(key)
        with colRight:
            paramWeight[attr] = st.sidebar.number_input(attr + " weight:", min_value=0.0, max_value=1.0, value=0.5, step=0.01)

    namesAndWeights = {}
    for key in paramCheck.keys():
        if paramCheck[key]:
            namesAndWeights[key] = paramWeight[key]

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

    # Get top N schools based on the selected parameters and year.
    df = getTopNDF(selN, namesAndWeights, selYear, selMaxDeg, hideOutsiders)

    # Show table of top N schools, based on our rankings:
    ourTableDF = pd.DataFrame({
        "Our Ranking":df["Our Ranking"].to_list(),
        "US News Ranking":[""]*df["INSTNM"].count(),
        "University Name":df["INSTNM"].tolist(),
        "UNITID":df["UNITID"].to_list()
    })

    parallel_coordinates_df = df.drop(columns=["UNITID", "aggregateScore"])

    # Let's draw a parallel coordinates graph.
    #parallel_coordinates_fig = px.parallel_coordinates(parallel_coordinates_df, color="Our Ranking", labels=namesAndWeights.keys())
    parallel_coordinates_fig = px.parallel_coordinates(parallel_coordinates_df, labels=namesAndWeights.keys())
    parallel_coordinates_fig.update_layout(margin=dict(l=70, r=70, t=50, b=50))
    st.plotly_chart(parallel_coordinates_fig, use_container_width=True)

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
    dumbbell_data = {"line_x": [], "line_y": [], "Our Ranking": [], "US News Ranking": [], "schools": []}
    for school in dumbbell_schools:
        dumbbell_data["Our Ranking"].extend(ourTableDF.loc[ourTableDF["University Name"] == school]["Our Ranking"])
        dumbbell_data["US News Ranking"].extend(ourTableDF.loc[ourTableDF["University Name"] == school]["US News Ranking"])
        dumbbell_data["schools"] += [school]
        dumbbell_data["line_x"].extend([
            ourTableDF.query("`University Name` == \"" + str(school) + "\"")["Our Ranking"].to_list()[0],
            ourTableDF.query("`University Name` == \"" + str(school) + "\"")["US News Ranking"].to_list()[0],
            None
        ])
        dumbbell_data["line_y"].extend([school, school, None])

    dumbbell_fig = go.Figure(
        data=[
            go.Scatter(
                x=dumbbell_data["line_x"],
                y=dumbbell_data["line_y"],
                mode="lines",
                showlegend=False,
                marker=dict(color="black")
            ),
            go.Scatter(
                x=dumbbell_data["Our Ranking"],
                y=dumbbell_data["schools"],
                mode="markers",
                name="Our Ranking",
                marker=dict(
                    color="blue",
                    size=10
                )
            ),
            go.Scatter(
                x=dumbbell_data["US News Ranking"],
                y=dumbbell_data["schools"],
                mode="markers",
                name="US News Ranking",
                marker=dict(
                    color="goldenrod",
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
    print("Economic Mobility Single Variable")
    lib.loadschema()
    st.set_page_config(
        layout="wide", 
        initial_sidebar_state="expanded",
        page_title="Economic Mobility Multi Variable"
    )
    dashboard()

main()
