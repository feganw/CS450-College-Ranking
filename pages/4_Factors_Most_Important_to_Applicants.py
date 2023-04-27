import plotly.express as px
import pandas as pd
import streamlit as st

# K-score:
#     * affordability
#         - % of aid + loans
#         - inverse of cost of attendance
#     * academic quality
#         - % degrees awarded in sum(cs, math, premed, biomed, science, health, engineering)
#         - sat performance
#         - graduation rate
#     * diversity
#          
# https://edvoy.com/articles/highest-paying-majors-usa/

full_dataset = pd.read_csv('./tyresedata/rankings.csv', low_memory=False)
# output = full_dataset[full_dataset['COSTT4_A'] > 100_000]
# print(output)

PDEG_CS = 'PCIP11'
PDEG_ENG = 'PCIP14'
PDEG_LAW = 'PCIP22'
PDEG_BIO = 'PCIP26'
PDEG_MATH = 'PCIP27'
PDEG_DOC = 'PCIP51'
PDEG_SCI = 'PCIP40'

P_DEGS = [PDEG_CS, PDEG_BIO, PDEG_MATH, PDEG_ENG, PDEG_LAW, PDEG_SCI, PDEG_DOC]

HAS_CS = 'CIP11BACHL'
HAS_ENG = 'CIP14BACHL'
HAS_LAW = 'CIP22BACHL'
HAS_BIO = 'CIP26BACHL'
HAS_MATH = 'CIP27BACHL'
HAS_DOC = 'CIP51BACHL'
HAS_SCI = 'CIP40BACHL'
HAS_BIZ = 'CIP52BACHL'

SAT_MATH = 'SATMT75'
SAT_READ = 'SATVR75'
SAT_AVG = 'SAT_AVG'
ADM_RATE = 'ADM_RATE'
COST = 'COSTT4_A'
# LOANS = 'FTFTPCTFLOAN'
# GRANTS = 'FTFTPCTPELL'
COMPLETION = 'C100_4_POOLED_SUPP'
DIV_GROUPS = ['UGDS_WHITE', 'UGDS_BLACK', 'UGDS_ASIAN', 'UGDS_AIAN', 'UGDS_NHPI']

work_set = full_dataset.loc[
    (full_dataset[HAS_CS] > 0.0) & (full_dataset[HAS_ENG] > 0.0) & (full_dataset[HAS_BIO] > 0.0) &
    (full_dataset[HAS_MATH] > 0.0) & (full_dataset[HAS_SCI] > 0.0) &
    (full_dataset[ADM_RATE] <= 0.12)]

for idx, row in work_set.iterrows():
    try:
        work_set.at[idx, COMPLETION] = float(work_set.at[idx, COMPLETION])
    except:
        work_set.at[idx, COMPLETION] = 0.0


work_set['K_SCORE'] = 0
work_set['High-Paying Degrees'] = 0
work_set['SAT Scores'] = 0
work_set['Affordability'] = 0
work_set['Completion Rate (4 Years)'] = 0
work_set['Academics'] = 0
work_set['Diversity'] = 0


def rank_normal():
    for idx, row in work_set.iterrows():
        k = 0
        degrees = 0
        diversity = 0

        for deg in P_DEGS:  # calc degree coverage
            degrees += (work_set.at[idx, deg] * 100) % 10


        for race in DIV_GROUPS:  # calc racial spread
            diversity = -diversity + work_set.at[idx, race]

        diversity = abs(diversity) - (1/10) * work_set.at[idx, 'UGDS_HISP']
        diversity = (1/abs(diversity)) * 3

        sats = (work_set.at[idx, SAT_AVG] + 4*(work_set.at[idx, SAT_MATH] + work_set.at[idx, SAT_READ])) % 60
        affordability = 1_000_000 / (work_set.loc[idx, COST])
        completion = work_set.loc[idx, COMPLETION] * 40

        k += degrees + sats + affordability + completion + diversity

        work_set.loc[idx, 'K_SCORE'] = k
        work_set.loc[idx, 'High-Paying Degrees'] = degrees
        work_set.loc[idx, 'SAT Scores'] = sats
        work_set.loc[idx, 'Affordability'] = affordability
        work_set.loc[idx, 'Completion Rate (4 Years)'] = completion
        work_set.loc[idx, 'Academics'] = degrees + sats + completion
        work_set.loc[idx, 'Diversity'] = diversity

def rank_controversial():
    for idx, row in work_set.iterrows():
        k = 0
        degrees = 0
        diversity = 0

        for deg in P_DEGS:  # calc degree coverage
            degrees += (work_set.at[idx, deg] * 100) % 10

        for race in DIV_GROUPS:  # calc racial spread
            diversity = -diversity + work_set.at[idx, race]

        diversity = abs(diversity) - (1/10) * work_set.at[idx, 'UGDS_HISP']
        diversity = (1/abs(diversity)) * 25

        sats = (work_set.at[idx, SAT_AVG] + 2*(work_set.at[idx, SAT_MATH] + work_set.at[idx, SAT_READ])) % 200
        affordability = 4_000_000 / (work_set.loc[idx, COST])
        completion = work_set.loc[idx, COMPLETION] * 40

        k += degrees + sats + affordability + completion + diversity

        work_set.loc[idx, 'K_SCORE'] = k
        work_set.loc[idx, 'High-Paying Degrees'] = degrees
        work_set.loc[idx, 'SAT Scores'] = sats
        work_set.loc[idx, 'Affordability'] = affordability
        work_set.loc[idx, 'Completion Rate (4 Years)'] = completion
        work_set.loc[idx, 'Academics'] = degrees + sats + completion
        work_set.loc[idx, 'Diversity'] = diversity



rank_normal()



def dashboard():
    stacked_bar = px.bar(work_set.nlargest(10, 'K_SCORE'),
                    x="INSTNM", y=["Academics", 'Affordability', 'Diversity'],
                    title="TOP 10 UNIVERSITIES 2019, by Factors Most Important to Applicants ",
                    labels={
                        "value": "K-SCORE", "INSTNM": "SCHOOL",
                        "High-Paying Degrees": "Degrees",
                        "SAT Scores": "SAT Scores Scores", "variable":"Factor (most to least important)"},
                    template="plotly_dark")

    st.plotly_chart(stacked_bar, use_container_width=True)
    


def main():
    print("Ranking with Unbiased Attribute Combinations")
    dashboard()

main()

