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

# Function to find programming skills in the text
def find_skills(text, skills):
        found = []
        for lang in skills:
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


