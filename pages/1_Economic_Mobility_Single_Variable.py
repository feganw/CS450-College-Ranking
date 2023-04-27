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

def dashboard():

    dframes = lib.dframes
    yearStart = lib.yearStart
    yearEnd = lib.yearEnd
    paramsColumnsNice = lib.paramsColumnsNice
    paramsColumns = lib.paramsColumns
    highestDegNice = lib.highestDegNice
    lowerIsBetter = lib.lowerIsBetter

    st.sidebar.header("School Ranking Dashboard")

    # Year selection:
    st.sidebar.subheader("Select which year's data you would like to see:")
    selYear = st.sidebar.number_input("Year (" + str(yearStart) + "-" + str(yearEnd) + ")", min_value=yearStart, max_value=yearEnd, value=yearEnd, step=1)

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
    df = lib.getTopNDF(selN, selParamColName, selYear, selMaxDeg, hideOutsiders)

    strNiceCol = ""
    for key in paramsColumnsNice.keys():
        if paramsColumnsNice[key] == selParamColName:
            strNiceCol = key
            break

    # Show scatter plot.
    scatter_fig = go.Figure(
        data=[
            go.Scatter(
                x=df["INSTNM"],
                y=df[selParamColName],
                mode="markers",
                name=strNiceCol,
                marker=dict(color="blue",size=10)
            )
        ]
    )

    if lowerIsBetter[selParamColName]:
        scatter_fig.add_annotation(x=-1, y=df[selParamColName].max(), text="Worse", showarrow=False)
        scatter_fig.add_annotation(x=-1, y=df[selParamColName].min(), text="Better", showarrow=False)
    else:
        scatter_fig.add_annotation(x=-1, y=df[selParamColName].min(), text="Worse", showarrow=False)
        scatter_fig.add_annotation(x=-1, y=df[selParamColName].max(), text="Better", showarrow=False)

    scatter_fig.update_xaxes(
        tickangle=90,
    )
    scatter_fig.update_yaxes(
        autorange="reversed"
    )

    scatter_fig.update_layout(
        xaxis_title="INSTNM",
        yaxis_title=selParamColName        
    )

    st.plotly_chart(scatter_fig, use_container_width=True)

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
        page_title="Economic Mobility Single Variable"
    )
    dashboard()

main()
