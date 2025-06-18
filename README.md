**Webscraping is against the TOS of Finn.no! This programm is for educational purposes only and I take no responsibility for a malicious use of it. 
The number of jobs to be scraped as well as the intervalls between each action should be set respectfully.**

### A Webscraper that lists programming languages affiliated with job postings on Finn.no.
It uses both **regex** and **ChatGPT's API** for filtering out the languages, which are given by the user. 
It then prints them as well as saving them into a sql-lite database with their unique job id, so that future look-ups jump over links that have already been analyzed.


**Generally, debugging shows, that GPT's filtering is more accurate than using regex, due to the dynamic nature of the content of job postings;**

e.g. while it is easy to distinguish between _"Java"_ and _"Javascript"_ edge cases as _"Javadeveloper"_ pose a greater challenge. 

**Especially languages like "c" and "r" require thourough patterns and even then, you may get false positives;** 

e.g. _"You should be an expert in python&r&sql."_ vs _"Our company r&d is looking for an expert in python."_
