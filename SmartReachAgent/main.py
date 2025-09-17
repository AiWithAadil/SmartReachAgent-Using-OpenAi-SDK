import os
import sys
import asyncio
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import shutil
import csv
from fastapi.responses import FileResponse
import json # Ensure this is imported for product_info.json and dashboard summary

app = FastAPI()

# ✅ Allow access from frontend (e.g., Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔁 Dynamic Import
def path_import(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# Paths to your script files
SEND_PATH = "./send_email_agent.py"
TRACK_PATH = "./read_reply_tracker.py"
RESPOND_PATH = "./responder_agent.py"

# Ensure these files exist and are correctly imported
try:
    send_agent = path_import("send_email_agent", SEND_PATH)
    track_replies = path_import("read_reply_tracker", TRACK_PATH)
    responder = path_import("responder_agent", RESPOND_PATH)
except Exception as e:
    print(f"Error importing agent scripts: {e}")
    # In a production app, you might want to raise an exception or log this more formally.

# 🧠 Validation Models
class CampaignInput(BaseModel):
    from_name: str
    offer: str
    description: Optional[str] = ""

@app.post("/send-emails")
async def send_emails(
    from_name: str = Form(...),
    offer: str = Form(...),
    description: Optional[str] = Form(""),
    csv_file: UploadFile = None
):
    if not csv_file:
        raise HTTPException(status_code=400, detail="CSV file is required.")
    if not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are allowed.")
    
    # Ensure the Data directory exists
    os.makedirs("./Data", exist_ok=True)
    save_path = "./Data/temp_contacts.csv"
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(csv_file.file, buffer)
    
    # CSV Validation
    with open(save_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if "email" not in reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV must have 'email' columns.")
    
    # Save product info
    product_info = {
        "offer": offer,
        "description": description
    }
    with open("./Data/product_info.json", "w", encoding="utf-8") as f:
        json.dump(product_info, f, indent=2)
    
    # Launch email sender
    await send_agent.main_runner(from_name=from_name)
    return {"message": "Emails sent successfully."}

@app.post("/track-replies")
async def track_replies_endpoint():
    await track_replies.find_and_save_replies()
    return {"message": "Replies tracked and saved."}

@app.post("/respond-customers")
async def respond_customers():
    await responder.process_customer_replies()
    return {"message": "Customer replies processed."}

# --- Dashboard Summary Endpoint (Refined Logic) ---
@app.get("/dashboard-summary")
async def get_dashboard_summary():
    total_campaigns = 0
    new_replies = 0
    ai_responses = 0

    # Ensure logs and Data directories exist before trying to read
    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./Data", exist_ok=True)

    # 1. Count Total Campaigns from email_logs.txt
    email_log_path = "./logs/email_logs.txt"
    if os.path.exists(email_log_path):
        try:
            with open(email_log_path, 'r', encoding='utf-8') as f:
                # Count lines that indicate a successful email send
                total_campaigns = sum(1 for line in f if "Email sent successfully" in line)
        except Exception as e:
            print(f"Error reading email_logs.txt for campaigns: {e}")

    # 2. Count New Replies from replies.json
    replies_json_path = "./Data/replies.json"
    if os.path.exists(replies_json_path):
        try:
            with open(replies_json_path, 'r', encoding='utf-8') as f:
                replies_data = json.load(f)
                # Assuming replies.json is a list of reply objects
                if isinstance(replies_data, list):
                    new_replies = len(replies_data)
                else:
                    print(f"Warning: replies.json is not a list. Content: {replies_data}")
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {replies_json_path}. It might be empty or malformed.")
        except Exception as e:
            print(f"Error reading replies.json for new replies: {e}")

    # 3. Count AI Responses from conversation_log.json
    conversation_log_path = "./logs/conversation_log.json"
    if os.path.exists(conversation_log_path):
        try:
            with open(conversation_log_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)
                # Assuming conversation_log.json is a list of dictionaries,
                # and each dict has an 'ai_responded' key (1 for AI, 0 for human/skipped)
                if isinstance(conversation_data, list):
                    ai_responses = sum(1 for entry in conversation_data if isinstance(entry, dict) and entry.get("ai_responded") == 1)
                else:
                    print(f"Warning: conversation_log.json is not a list. Content: {conversation_data}")
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {conversation_log_path}. It might be empty or malformed.")
        except Exception as e:
            print(f"Error reading conversation_log.json for AI responses: {e}")

    return {
        "total_campaigns": total_campaigns,
        "new_replies": new_replies,
        "ai_responses": ai_responses
    }

# --- File Serving Endpoints ---

@app.get("/logs/{filename}")
async def get_log_file(filename: str):
    logs_dir = "./logs"
    os.makedirs(logs_dir, exist_ok=True) # Ensure directory exists
    file_path = os.path.join(logs_dir, filename)

    if not os.path.abspath(file_path).startswith(os.path.abspath(logs_dir)):
        raise HTTPException(status_code=400, detail="Invalid log file path.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Log file '{filename}' not found at {os.path.abspath(file_path)}")
    
    return FileResponse(file_path, media_type="text/plain")

@app.get("/data/{filename}")
async def get_data_file(filename: str):
    data_dir = "./Data"
    os.makedirs(data_dir, exist_ok=True) # Ensure directory exists
    file_path = os.path.join(data_dir, filename)

    if not os.path.abspath(file_path).startswith(os.path.abspath(data_dir)):
        raise HTTPException(status_code=400, detail="Invalid data file path.")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Data file '{filename}' not found at {os.path.abspath(file_path)}")
    
    return FileResponse(file_path, media_type="application/octet-stream", filename=filename)

@app.get("/")
async def root():
    return {"message": "🚀 Email Campaign API is running!"}