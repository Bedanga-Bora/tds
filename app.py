#this is the project file
from fastapi import FastAPI, HTTPException, Query
import os
import requests
from dotenv import load_dotenv
import datetime
import json
import subprocess
from typing import List, Dict

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

AIPROXY_TOKEN = os.getenv("eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjEwMDAzOTVAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.Y9pK_iw4L4uLHYcYbjOA9WWmPj1LDLBI4S3azoFD4XM
")

# Function to interact with the LLM
def ask_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {AIPROXY_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://api.aiproxy.io/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# Task-specific logic
def install_uv_and_run_script(email: str):
    try:
        subprocess.run(["pip", "install", "uv"], check=True)
        subprocess.run(["python", "https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py", email], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to install uv or run script: {e}")

def count_wednesdays(file_path: str, output_path: str):
    with open(file_path, 'r') as file:
        dates = file.readlines()
    wednesdays = [date.strip() for date in dates if datetime.datetime.strptime(date.strip(), "%Y-%m-%d").weekday() == 2]
    with open(output_path, 'w') as file:
        file.write(str(len(wednesdays)))

def sort_contacts(file_path: str, output_path: str):
    with open(file_path, 'r') as file:
        contacts = json.load(file)
    contacts_sorted = sorted(contacts, key=lambda x: (x['last_name'], x['first_name']))
    with open(output_path, 'w') as file:
        json.dump(contacts_sorted, file, indent=4)

def extract_email_sender(file_path: str, output_path: str):
    with open(file_path, 'r') as file:
        email_content = file.read()
    sender_email = ask_llm(f"Extract the sender's email address from this email: {email_content}")
    with open(output_path, 'w') as file:
        file.write(sender_email)

# Add more task-specific functions here...
def format_markdown(file_path: str):
    try:
        subprocess.run(["npx", "prettier@3.4.2", "--write", file_path], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to format Markdown file: {e}")
    
def extract_recent_logs(log_dir: str, output_path: str):
    log_files = sorted(
        [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith(".log")],
        key=os.path.getmtime,
        reverse=True
    )
    with open(output_path, 'w') as output_file:
        for log_file in log_files[:10]:
            with open(log_file, 'r') as file:
                first_line = file.readline()
                output_file.write(first_line)

def fetch_data_from_api(api_url: str, output_path: str):
    response = requests.get(api_url)
    response.raise_for_status()
    with open(output_path, 'w') as file:
        file.write(response.text)


@app.post("/run")
async def run_task(task: str = Query(..., description="The task to execute")):
    try:
        llm_response = ask_llm(f"Parse and execute the following task: {task}")

        if "format markdown" in llm_response.lower():
            format_markdown("/data/format.md")
            return {"message": "Task A2 executed successfully"}
        elif "extract first line of recent logs" in llm_response.lower():
            extract_recent_logs("/data/logs", "/data/logs-recent.txt")
            return {"message": "Task A5 executed successfully"}
        elif "fetch data from api" in llm_response.lower():
            fetch_data_from_api("https://api.example.com/data", "/data/api-data.json")
            return {"message": "Task B3 executed successfully"}
        # Add more conditions for other tasks...
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/read")
async def read_file(path: str = Query(..., description="Path of the file to read")):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, 'r') as file:
        content = file.read()
    return {"content": content}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
