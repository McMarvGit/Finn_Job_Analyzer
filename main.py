import streamlit as st
from database import create_database, get_jobs
from scraper import scrape_jobs
from analyzer import analyze_jobs, create_client

 # Create database if they do not exist
create_database()

st.title("Job Analyzer")

job_limit = st.number_input(
    "Anzahl Jobs zum Scrapen",
    min_value=1,
    max_value=1000,
    step=10
)

if st.button("Scrape Jobs"):
    scrape_jobs(job_limit)
    st.success("Done")

if st.button("Analyze"):
    client = create_client()
    analyze_jobs(client)

if st.button("Show jobs"):
    df = get_jobs()
    st.dataframe(df)
