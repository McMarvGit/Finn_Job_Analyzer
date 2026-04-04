import sqlite3

conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()
cursor.execute('''
               SELECT s.name, COUNT(*) as frequency
               FROM jobskills js 
               JOIN skills s ON js.skill_id=s.id
               GROUP BY s.name
               ORDER BY frequency DESC
               ''')

result = cursor.fetchall()
conn.close()

for skill, count in result:
    print(skill, count)