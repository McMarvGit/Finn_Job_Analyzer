import requests
from bs4 import BeautifulSoup
import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
import time
import random
from collections import Counter
import sqlite3

# Load .env
load_dotenv()

# List of languages
languages = [
    "python", "java", "javascript", "c#", "c++", "go", "c", "sql", "html", "r", "ruby",
    "cobol", "swift", "kotlin", "typescript", "php", "rust", "scala", 
    "perl", "haskell", "elixir", "clojure", "dart", 
]

# API-Key 
api_key = os.getenv("OPENAI_API_KEY")

# Client initialization
client = OpenAI(api_key=api_key)

# Set the scan limit for how many jobs to scrape
scan_limit = 20 

# SQLite database setup
def create_database(name):
    conn = sqlite3.connect(name + ".db")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_list (
        job_id TEXT PRIMARY KEY
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS languages (
        name TEXT PRIMARY KEY,
        count INTEGER DEFAULT 0
    )
    ''')

    for lang in languages:
        cursor.execute("INSERT OR IGNORE INTO languages (name, count) VALUES (?,0)", (lang,))
    conn.commit()
    conn.close()

# Create databases if they do not exist
create_database("jobs")
create_database("jobs_gpt")

# Function to load already analyzed job IDs from the database
def load_analyzed_job_ids(databse_name):
    conn = sqlite3.connect(databse_name)
    cursor = conn.cursor()
    cursor.execute("SELECT job_id FROM job_list")
    job_ids = {row[0] for row in cursor.fetchall()}  # Get all job IDs as a set
    conn.close()
    return job_ids

# Function to load languages and their counts from the database
def load_languages(database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name, count FROM languages")
    languages = {row[0]: row[1] for row in cursor.fetchall()}  # Get all languages and their counts as a dict
    conn.close()
    return languages

# Load existing job IDs
job_ids = load_analyzed_job_ids("jobs.db")

# Load existing languages and their counts
languages_count = load_languages("jobs.db")
languages_count_gpt = load_languages("jobs_gpt.db")

# Function to save job IDs to the databse
def save_job_ids(database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    for job_id in job_ids:
        cursor.execute("INSERT OR IGNORE INTO job_list (job_id) VALUES (?)", (job_id,))
    conn.commit()
    conn.close()
    
# Function to save language counts to the database
def save_language_counts(languages_count, database_name):
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    for lang, count in languages_count.items():
        cursor.execute("""
            INSERT INTO languages (name, count) VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET count=excluded.count
        """, (lang, count))
    conn.commit()
    conn.close()

# Function to find programming languages in the text
def find_languages(text, languages):
        found = []
        for lang in languages:
            escaped = re.escape(lang)
            # Sepcial case for avoiding mismatching "c" in "c#" or "c++"
            if lang == "c":
                pattern = r'\bc\b(?![#\+])' 
            # Special case for "c++" or "c#"
            elif any(char in lang for char in "+#"):
                # Escape special characters and ensure word boundaries
                pattern = rf'(?<!\w){escaped}(?!\w)'
            # Special case for "r" to avoid matching "&r"/"r&"    
            elif lang == "r":
                pattern = r'(?<!&)\br\b(?!&)'
            else:
                # Normal case for other languages 
                pattern = rf'\b{escaped}\b'

            if re.search(pattern, text):
                found.append(lang)
        return found

#dynamic prompt creation
def call_gpt(job_section_text):
    prompt = f"""
    Read the following job posting and extract only the mentioned programming languages, 
    which are listed in this list: {languages}.

    Answer **only** in the following JSON format. No markdown, no explanation:

    ["language1", "language2", ...]


    Here is the job posting:
    {job_section_text}
    """

    # GPT-4 Prompt 
    response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", 
               "content": prompt}])

    # Check if response is valid
    try:
        content = response.choices[0].message.content
        gpt_languages = json.loads(content)
        for lang in gpt_languages:
            languages_count_gpt[lang] = languages_count_gpt.get(lang, 0) + 1
    except Exception as e:
        print("Error while parsing JSON:", e)
        print("GPT answered with:")
        print(response.choices[0].message.content)

# Timer to measure the time of the process
work_time = time.time()
number_of_jobs_scanned_total = len(job_ids)
number_of_jobs_scanned_new = 0
page = 1

# Adjust this number to control how many jobs you want to scrape
while number_of_jobs_scanned_new < scan_limit: 
    # Sleep to avoid hitting the server too hard when loading new pages
    time.sleep(random.randint(1, 5))  
    # Finn.no Web-Scraping for {search_term} jobs, e.g. "software developer"
    if page == 1:
       # url = "https://www.finn.no/job/fulltime/search.html?q=software+developer" 
         url = "https://www.finn.no/job/fulltime/search.html?occupation=0.22&occupation=0.23&q=it"
    else:
        #url = f"https://www.finn.no/job/fulltime/search.html?page={page}&q=software+developer"
        url = f"https://www.finn.no/job/fulltime/search.html?occupation=0.22&occupation=0.23&page={page}&q=it"
        print(f"round {page}")
    page += 1
    r = requests.get(url)
    soup = BeautifulSoup(r.content, "html.parser")

    # Find all links for the individual job postings
    links = []
    for a in soup.find_all("a", href=True):
        href = a['href']
        if "finnkode=" in href:
            links.append(href)

    # Check if job links were found
    if not links:
        print("No job links were found.")
        break

    for link in links:
        # Extract the job ID from the link
        id = link.split("finnkode=")[-1]
        # Check if the job ID has already been processed
        if id in job_ids:
            continue
        # Pick one example job and scrape its details
        r = requests.get(link)  
        detail_soup = BeautifulSoup(r.content, "html.parser")
        job_section = detail_soup.find("section", attrs={"aria-label": "Jobbdetaljer"})

        # Check if job_section was found
        if not job_section:
            # Sometimes the whole job details are in a meta tag
            job_section = detail_soup.find("meta", attrs={"property": "og:description"})
            if not job_section:
                print(f"No details found for job: {link}")
                continue
            else:
                job_section_text = job_section["content"]
        else:
            # Extract text from <li> and <p> tags to ensure words are separated correctly
            li_tags = job_section.find_all("li")
            p_tags = job_section.find_all("p")
            li_texts = [li.get_text(separator=" ") for li in li_tags]
            p_texts = [p.get_text(separator=" ") for p in p_tags]
            job_section_text = " ".join(li_texts + p_texts)

        job_section_text = job_section_text.lower()
        job_section_text = job_section_text.replace("/", " ")
        # Find programming languages mentioned in the job description
        # Use regex to find whole words only
        found = find_languages(job_section_text, languages)
        call_gpt(job_section_text)
        for lang in found:
            languages_count[lang] = languages_count.get(lang, 0) + 1
        job_ids.add(id)    
        number_of_jobs_scanned_total += 1
        number_of_jobs_scanned_new += 1
        # Commented out code for debugging purposes/to compare regex results with GPT
        #bool = False
        """  for lang in set(languages_count.keys()).union(languages_count_gpt.keys()):
            count_a = languages_count.get(lang, 0)
            count_b = languages_count_gpt.get(lang, 0) """
            
        """             if count_a != count_b:
                print(f"Discrepancy found for {lang}: {count_a} (local) vs {count_b} (GPT)")
                print(link)
                bool = True
                break
        if bool:
            break """
        # Sleep to regulate requests
        time.sleep(random.randint(1,15))
    
    
# Save job IDs and languages to the database
save_job_ids("jobs.db")
save_language_counts(languages_count, "jobs.db")
save_job_ids("jobs_gpt.db")
save_language_counts(languages_count_gpt, "jobs_gpt.db")

print(f"""{number_of_jobs_scanned_total} have been processed in total 
      with {number_of_jobs_scanned_new} new jobs found. Took {round(time.time() - work_time)} seconds.""")
counter = Counter(languages_count).most_common()
for lang, count in counter:
    print(f"{lang}: {count}") 

print("\nGPT results:")
counter = Counter(languages_count_gpt).most_common()
for lang, count in counter:
    print(f"{lang}: {count}")     

