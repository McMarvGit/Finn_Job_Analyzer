import time
import random
import requests
from bs4 import BeautifulSoup
from database import save_job, load_job_ids

def scrape_jobs(limit):
    page = 1
    jobs_scraped = 0
    scraped_job_ids = load_job_ids()
    # Timer to measure the time of the process
    work_time = time.time()
    # Adjust this number to control how many jobs you want to scrape
    while jobs_scraped < limit: 
    # Sleep to avoid hitting the server too hard when loading new pages
        time.sleep(random.randint(1, 5))  
    # Finn.no Web-Scraping for {search_term} jobs, e.g. "software developer"
        if page == 1:
            # All positions in the category IT utvikling. Often around 700-1000 jobs
            url = "https://www.finn.no/job/search?location=0.20001&occupation=0.23"
        else:
            url = f"https://www.finn.no/job/search?location=0.20001&occupation=0.23&page={page}"
        print(f"round {page}")
        page += 1
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")

        # Find all links for the individual job postings
        links = []
        for job in soup.find_all("a", class_="job-card-link"):
            link = job['href']
            links.append(link)

        # Check if job links were found
        if not links:
            print("No job links were found.")
            break

        for link in links:
            if jobs_scraped >= limit:
                break
        # Extract the job ID from the link
        id = link.split("ad/")[-1]
        # Check if the job ID has already been processed
        if id in scraped_job_ids:
            continue
        # Pick one example job and scrape its details
        r = requests.get(link)  
        detail_soup = BeautifulSoup(r.content, "html.parser")
        # Get the title
        if detail_soup.head and detail_soup.head.find("title"):
            title = detail_soup.head.find("title").get_text(strip=True).split(" | FINN.no")[0]
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
        # Add to database with job ID, link, title and description 
        # TODO : Check if it would be better to write all jobs at once to the database
        save_job(id, link, title, job_section_text)
        jobs_scraped += 1
        print("scanned job:", title)
        # Sleep to regulate requests
        time.sleep(random.randint(1,10))