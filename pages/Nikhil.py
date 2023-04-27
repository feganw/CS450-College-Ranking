import plotly.express as px
from pandas import DataFrame
import pandas as pd
import os
import numpy as np
import streamlit as st
import matplotlib as plt

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

#Function that iterates over a pandas dataframe and removes all rows that have
#NaN/Null values in order to guarantee all calculations function correctly.

def stripbadNikhil(colArr, df: DataFrame) -> DataFrame:
    #Removes all null institutions from values specified in the usecols array
    for s in colArr:
        df = df[ (df[s].notnull()) ]

    return df


#Function that calculates the 'Combination Count', a value that is a composite
#attribute of all the attributes in the dataframe (other than the UNITID and INSTNM)
#since these are not quantitative attributes. The Combination Count is calculated by
#sorting the dataframe based on the specified top-k value provided by the user, then
#incrementing the count for each university in that top-k for each attribute. This results
#in an unbiased attribute that can be used to rank the universities on the amount of attributes
#that they fall in the top-k with. 

def calcCombinationCount(df,k,natt):
    numAttributes = natt
    result = df.copy()
    for feature_name in df.columns:
      if(feature_name not in ["UNITID","INSTNM","Combination Count"]):
        result = result.sort_values(by=[feature_name], ascending=False)
        i = 0
        for row in result.head(k).itertuples():
          result.at[row.Index,"Combination Count"] += 1/numAttributes
          i = i + 1
    return result


#Function that will normalized all entries for a column based on the average value of that column.
#This is necessary in order to keep the visualization color coding for the heatmap consistent due to
#the different ranges of each attribute. The values are then rounded to two decimal places for a
#cleaner visualization. Normalization of values for certain attributes such as 'NPT42_PUB' and 'ADM_RATE'
#are inverted since a high tuition and high admission rate is actually not good.


def normalize(df):
    result = df.copy()
    for feature_name in df.columns:
      if(feature_name not in ["UNITID","INSTNM"]):
        max_value = df[feature_name].max()
        min_value = df[feature_name].min()
        normRound = round((df[feature_name] - min_value) / (max_value - min_value),2)
        if(feature_name in ["NPT42_PUB", "ADM_RATE", "COSTT4_A", "TRANS_4"]):
          result[feature_name] = round(1 - normRound,2)
        else:
          result[feature_name] = normRound
    return result


#Utilizes the normalized values in each cell and assigns a color gradient and label
#for each number type value. For instance, if the normalized value is < .125 then it is
#in the bottom 12.5 percentile and therefore is assigned the red color gradient with a
#'Very Poor' label.


def combo_percentile(v):
    if isinstance(v,str):
        return str(v)
    elif v < .125:
        return str(v) + " Very Poor"
    elif v < .25:
        return str(v) + " Poor"
    elif v < .375:
        return str(v) + " Subpar"
    elif v < .5:
        return str(v) + " Neutral"
    elif v < .625:
        return str(v) + " Neutral"
    elif v < .75:
        return str(v) + " Good"
    elif v < .875:
        return str(v) + " Great"
    elif v <= 1:
        return str(v) + " Excellent"
    else:
        return str(v)


#Pandas dataframe make_pretty function that returns a styler object with the proper
#stylizations. This is what converts the dataframe table to a heatmap visualization.
#Utilizes the aforementioned functions as decision boundaries to format for color coding
#and labeling. Also assigns a caption.

def make_pretty(styler):
    styler.set_caption("Universities Top-K Ranking Distribution with Attribute Combinations")
    styler.format(combo_percentile)
    styler.background_gradient(axis=None, vmin=0, vmax=1, cmap="RdYlGn")
    return styler


#Main script which initializes Pandas dataframe based on the correct csv file based on
#year selected using Streamlit in final version. Also allows for user input with a slider
#to select the top-k distinction that will be used to sort the universities. This will also
#be implemented with a Streamlit input in the final version.

# Make the cache directory if it does not exist.
if not os.path.isdir(cachepath):
    os.mkdir(cachepath)

# Load College Scorecard data for each year.
usecolsArr = ["UNITID", "INSTNM", "NPT42_PUB", "SAT_AVG", "ADM_RATE", "COSTT4_A", "PFTFAC", "TRANS_4", "ACTCM25", "RET_FT4", "PCTFLOAN"]
year = yearStart
while year <= yearEnd:
    cachefile = cachepath + str(year) + ".csv"

    if not os.path.exists(cachefile):
        # Data is not cached, build our custom stripped tables from scratch.
        df = pd.read_csv(filepath_or_buffer=datastore["scard"][year], usecols=usecolsArr)
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

st.title("Ranking with Unbiased Attribute Combinations")
st.sidebar.header("School Ranking Dashboard")
# Year Selection:
st.sidebar.subheader("Select which year's data you would like to see:")
selYear = st.sidebar.number_input("Year (" + str(yearStart) + "-" + str(yearEnd) + ")", min_value=yearStart, max_value=yearEnd, value=yearEnd, step=1)


USNewsDF = dframes["usnews" + str(selYear)]
k = st.sidebar.slider("K Value for Top-K Distinction", 10, 100, 10, 1)
#usecolsArr = ["UNITID","MN_EARN_WNE_INC1_P10","MN_EARN_WNE_INC2_P10","MN_EARN_WNE_INC3_P10","FEMALE_COMP_ORIG_YR3_RT","FEMALE_COMP_4YR_TRANS_YR3_RT","FEMALE_COMP_2YR_TRANS_YR3_RT","MALE_COMP_ORIG_YR3_RT","MALE_COMP_4YR_TRANS_YR3_RT","MALE_COMP_2YR_TRANS_YR3_RT","LO_INC_DEBT_MDN","MD_INC_DEBT_MDN","HI_INC_DEBT_MDN","COMPL_RPY_7YR_N","NONCOM_RPY_7YR_N","FEMALE_RPY_7YR_N","MALE_RPY_7YR_N","LO_INC_RPY_7YR_N","MD_INC_RPY_7YR_N","HI_INC_RPY_7YR_N","PELL_RPY_7YR_N","NOPELL_RPY_7YR_N","UGDS","NPT41_PUB","NPT42_PUB","NPT43_PUB","NPT44_PUB","NPT45_PUB","NPT41_PRIV","NPT42_PRIV","NPT43_PRIV","NPT44_PRIV","NPT45_PRIV","PCT_WHITE","PCT_BLACK","PCT_ASIAN","PCT_HISPANIC","PCT_BA","PCT_GRAD_PROF","PCT_BORN_US","SAT_AVG","ACTCM25","INSTNM"]
#usecolsArr = ["UNITID", "INSTNM", "NPT42_PUB", "SAT_AVG", "ADM_RATE", "COSTT4_A", "PFTFAC", "TRANS_4"]
df = pd.read_csv(datastore["scard"][selYear], usecols = usecolsArr)
#df = dframes[selYear]
#df["Combination Count"] = np.random.rand(len(df.index),1)
df.insert(2,"Combination Count",np.zeros(len(df.index)))
df = stripbadNikhil(usecolsArr,df)
df = calcCombinationCount(df,k,len(usecolsArr)-2)
df = normalize(df)
sorted_df = df.sort_values(by=['Combination Count'], ascending=False)
#sorted_df.rename(columns={"UNITID":"Unique ID", "INSTNM":"University Name", "NPT42_PUB":"Avg. Tuition", "SAT_AVG":"Avg. SAT Score", "ADM_RATE": "Admission Rate", "COSTT4_A": "Average 4-Year Cost", "PFTFAC": "Faculty-Student Ratio", "TRANS_4": "Transfer Rate"})
display_Nikhil = sorted_df.head(100).style.pipe(make_pretty)
st.dataframe(display_Nikhil)
