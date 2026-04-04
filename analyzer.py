from database import load_skills, get_job_infos, save_job_skills
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

def create_client():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

def analyze_jobs(client):
    skill_map = load_skills()
    job_infos = get_job_infos()
    for job_id, description in job_infos:
        call_gpt(client, job_id, description, skill_map)

# Function to call GPT-4 and extract skills from the job description
def call_gpt(client, job_id, job_section_text, skill_map):
    prompt = f"""
    Read the following job posting and extract only the mentioned tech skills (e.g. programming languages
    or technologies), 
    which are listed in this list: {list(skill_map.keys())}.

    Answer **only** in the following JSON format. No markdown, no explanation:

    ["skill1", "skill2", ...]


    Here is the job posting:
    {job_section_text}
    """

    # GPT-4 Prompt 
    response = client.chat.completions.create(
    # model="gpt-4o-mini",
    model="gpt-5-nano",
    messages=[{"role": "user", 
               "content": prompt}])

    # Check if response is valid
    try:
        content = response.choices[0].message.content
        gpt_skills = json.loads(content)
        for skill in gpt_skills:
            skill_id = skill_map.get(skill)
            # Add skill to database together with id many-to-many
            save_job_skills(job_id, skill_id)
    except Exception as e:
        print("Error while parsing JSON:", e)
        print("GPT answered with:")
        print(response.choices[0].message.content)


