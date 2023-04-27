# Wesley Fegan
# CS450

# School Ranking Project

import streamlit as st


def dashboard():
    st.write("# College Ranking Dashboard")
    st.sidebar.success("Select a activity above.")
    st.markdown(
        """
        ### Purpose  
        The purpose of this dashboard is to help researchers investigate how college rankings are made. The long term
        goal is to be able to make the college ranking system more open.  

        ### This Dashboard  
        This dashboard will help investigate how rankings are produced and specifically how our hypothetical rankings
        compare to US News' rankings.
        """
    )

def main():
    print("Let's do some data science!")
    st.set_page_config(
        layout="wide", 
        initial_sidebar_state="expanded", 
        page_title="College Ranking Dashboard"
    )
    dashboard()

main()
