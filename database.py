import pandas as pd
from skills import SKILLS
import sqlite3

DB_PATH = "data.db"

# Function to get a database connection
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# SQLite database setup
def create_database():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            link TEXT,
            title TEXT,
            description TEXT           
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobskills (
            job_id TEXT,
            skill_id INTEGER,
            PRIMARY KEY (job_id, skill_id),
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (skill_id) REFERENCES skills(id)          
        )
        ''')
            # Fill the skill table with the predfined skills
        for skill in SKILLS:
            cursor.execute("INSERT OR IGNORE INTO skills (name) VALUES (?)", (skill,))


# Function to save jobs to the databse
def save_job(job_id, link, title, description):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO jobs (id, link, title, description) VALUES (?, ?, ?, ?)", (job_id, link, title, description))


#  Function to save skills together with job IDs to jobskills
def save_job_skills(job_id, skill_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO jobskills (job_id, skill_id) VALUES (?, ?)", (job_id, skill_id))

# Function to load already analyzed job IDs from the database
def load_job_ids():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jobs")
        job_ids = {row[0] for row in cursor.fetchall()}  # Get all job IDs as a set
        return job_ids

def load_skills():
# Fill skills in local variable 
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM skills")
        skill_map = {name: skill_id for skill_id, name in cursor.fetchall()}
        return skill_map

def get_job_infos():
    with get_connection() as conn:
        cursor  = conn.cursor()
        cursor.execute("SELECT id, description FROM jobs")
        job_infos = cursor.fetchall()
        return job_infos

def get_jobs():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM jobs", conn)
        return df