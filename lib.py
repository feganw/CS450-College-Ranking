import numpy as np
import os
from pandas import DataFrame
import pandas as pd

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

# Records whether lower is better.
lowerIsBetter = {
    "NPT41_PUB":True,
    "NPT42_PUB":True,
    "NPT43_PUB":True,
    "NPT44_PUB":True,
    "NPT45_PUB":True
}

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

# If n = 0, do not truncate the list.
def getTopNDF(n: int, param: str, year: int, maxDeg: int, hideOutsiders: bool) -> DataFrame:
    df = dframes[year]
    df = df[ (df["HIGHDEG"] >= maxDeg) ]

    if lowerIsBetter[param]: 
        df = df.sort_values(param, 0)
    else:
        df = df.sort_values(by=param, axis=0, ascending=False)

    ourRankings = np.arange(start=1, stop = df["INSTNM"].count() + 1, dtype=int).tolist()
    df["Our Ranking"] = ourRankings

    if hideOutsiders:
        USNewsDF = dframes["usnews" + str(year)]
        df = df[ (df["UNITID"].isin(USNewsDF["UNITID"])) ]

    if n != 0:
        df = df.head(n)
    return df