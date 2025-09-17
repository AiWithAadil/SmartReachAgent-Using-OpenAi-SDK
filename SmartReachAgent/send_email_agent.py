import os
import json
import csv
import asyncio
import smtplib
from dotenv import load_dotenv
from email.message import EmailMessage
from pydantic import BaseModel, Field
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    function_tool
)
from agents.run import RunConfig
from datetime import datetime
import re

# ─────────────────────────────────────────────
# 🔐 Environment Setup
# ─────────────────────────────────────────────
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY2")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in your .env file.")
if not SENDER_EMAIL or not APP_PASSWORD:
    raise ValueError("Missing sender email or app password in .env")

# ─────────────────────────────────────────────
# 🤖 Gemini Model & Config
# ─────────────────────────────────────────────
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# ─────────────────────────────────────────────
# ⚙️ User Config
# ─────────────────────────────────────────────
ENABLE_PREVIEW = False
DRY_RUN = False
DATA_PATH = "./Data/temp_contacts.csv"
LOG_FILES = [
    "./logs/email_logs.txt",
    "./logs/notification_log.txt",
    "./logs/reply_logs.txt",
    "./logs/conversation_log.json"
]

# ─────────────────────────────────────────────
# 🧹 Clear Logs Before Campaign
# ─────────────────────────────────────────────
def clear_logs():
    # Create logs directory if it doesn't exist
    os.makedirs("./logs", exist_ok=True)
    
    for log_file in LOG_FILES:
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")
            print(f"🧹 Cleared: {log_file}")
        except Exception as e:
            print(f"⚠️ Could not clear {log_file}: {e}")

# ─────────────────────────────────────────────
# 🧾 Email Tool Inputs
# ─────────────────────────────────────────────
class EmailGenInput(BaseModel):
    name: str = Field(..., description="Recipient's first name")
    offer: str = Field(..., description="Purpose of the email or offer")

@function_tool
def generate_custom_email(input: EmailGenInput) -> str:
    # Get from_name from global scope or use default
    sender_name = globals().get('from_name', 'Your Marketing Team')
    return (
    f"Write a professional marketing email for {input.name}, offering: {input.offer}. "
    f"The email should be returned as a JSON object with 'subject' and 'body' keys. "
    f"'subject' should include 1–2 relevant emojis and be eye-catching. "
    f"'body' must be valid HTML with:\n"
    f"• Offer description\n"
    f"• End with 'Best regards' and the {sender_name} name\n"
    f"• Do NOT include any buttons\n"
    f"Keep it concise, persuasive, and marketing-friendly.\n"
    f"If the user has provided any product or service details, incorporate them in the email body naturally.\n"
    f"Example:\n"
    f'{{"subject": "🎯 Adil, Your AI Discount Awaits!", "body": "<html>...</html>"}}'
    )

# ─────────────────────────────────────────────
# 🤖 Email Agent Runner
# ─────────────────────────────────────────────
async def run_email_agent(name: str, offer: str, product_info: str = "", sender_name: str = "") -> tuple[str, str]:
    try:
        with open("./Data/product_info.json", "r", encoding="utf-8") as f:
            product_data = json.load(f)
            product_info = product_data.get("description", "")
    except Exception as e:
        print(f"⚠️ Could not load product info: {e}")
        product_info = ""

    instructions = (
        f"""
        You are a professional email marketing assistant. Craft personalized marketing emails.

        Additional Info from the user:
        {product_info}

        • Use recipient's name
        • Explain the offer clearly
        • Subject: catchy + 1–2 emojis
        • Body: HTML + short, clear, persuasive
        • End with 'Best regards' and {sender_name}

        Output: JSON with 'subject' and 'body'
        """
    )

    agent = Agent(
        name="EmailWriterBot",
        instructions=instructions,
        tools=[generate_custom_email],
        model=model
    )

    result = await Runner.run(agent, f"Create a marketing email for {name} about: {offer}", run_config=config)
    raw = result.final_output.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        parsed = json.loads(raw)
        return parsed.get("subject", "📬 AI Email"), parsed.get("body", "Hi, here's your email.")
    except Exception as e:
        print(f"⚠️ Could not parse AI output: {e}")
        return "📬 AI Email", result.final_output

# ─────────────────────────────────────────────
# 📩 CSV Loader
# ─────────────────────────────────────────────
def load_recipients_from_csv(file_path):
    recipients = []
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            for row in csv.DictReader(csvfile):
                name = (row.get('name') or '').strip() or 'there'
                email = (row.get('email') or '').strip()
                if email:
                    recipients.append({'name': name, 'email': email})
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
    return recipients

# ─────────────────────────────────────────────
# 📤 Email Sender
# ─────────────────────────────────────────────
def send_email(to_email, subject, body, from_name):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{SENDER_EMAIL}>"
    msg['To'] = to_email

    msg.set_content("Your email client does not support HTML.")
    msg.add_alternative(body, subtype="html")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

# ─────────────────────────────────────────────
# 📝 Logger
# ─────────────────────────────────────────────
def log_result(status, name, email, reason="", subject=""):
    # Create logs directory if it doesn't exist
    os.makedirs("./logs", exist_ok=True)
    
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("./logs/email_logs.txt", "a", encoding="utf-8") as log:
        entry = f"[{time}] {status.upper()} | Name: {name} | Email: {email}"
        if reason:
            entry += f" | Reason: {reason}"
        if subject and status.lower() == "sent":
            entry += f" | Subject: {subject}"
        log.write(entry + "\n")

def is_valid_email(email: str) -> bool:
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

# ─────────────────────────────────────────────
# 🚀 Main Workflow
# ─────────────────────────────────────────────
async def main(from_name_param: str = None):
    # Set global from_name
    global from_name
    from_name = from_name_param or os.getenv("EMAIL_SENDER_NAME", "Default Sender")
    
    # Load other configurations
    offer = os.getenv("EMAIL_OFFER", "Limited Time Offer")
    product_description = os.getenv("EMAIL_PRODUCT_DESC", "")
    
    # Create Data directory if it doesn't exist
    os.makedirs("./Data", exist_ok=True)
    
    # Load existing product info or create new one
    try:
        with open("./Data/product_info.json", "r", encoding="utf-8") as f:
            existing_data = json.load(f)
            offer = existing_data.get("offer", offer)
            product_description = existing_data.get("description", product_description)
    except FileNotFoundError:
        # Create the file with default values
        with open("./Data/product_info.json", "w", encoding="utf-8") as f:
            json.dump({"offer": offer, "description": product_description}, f, indent=2)

    recipients = load_recipients_from_csv(DATA_PATH)
    if not recipients:
        print("❌ No recipients found in CSV file")
        return

    sent_emails = set()
    stats = {'sent': 0, 'skipped': 0, 'failed': 0, 'ai_generation_failed': 0}

    with open("./logs/email_logs.txt", "a", encoding="utf-8") as log:
        log.write(f"\n{'='*80}\nEmail Campaign Started: {datetime.now()}\n{'='*80}\n")

    for r in recipients:
        name, email = r['name'], r['email']
        print(f"\n📧 Processing: {name} ({email})")

        if not is_valid_email(email):
            print(f"⚠️ Invalid email: {email}")
            log_result("skipped", name, email, "Invalid email format")
            stats['skipped'] += 1
            continue

        # Skip duplicates
        if email in sent_emails:
            print(f"⚠️ Duplicate email: {email}")
            log_result("skipped", name, email, "Duplicate email")
            stats['skipped'] += 1
            continue

        print(f"✍️ Generating email for {name}...")
        try:
            subject, body = await run_email_agent(name, offer, product_description, from_name)
            print(f"✅ Generated successfully")
        except Exception as e:
            print(f"❌ AI generation failed: {e}")
            log_result("ai_failed", name, email, str(e))
            stats['ai_generation_failed'] += 1
            continue

        if DRY_RUN:
            print(f"🔍 DRY RUN - Would send to {email}")
            print(f"Subject: {subject}")
            if ENABLE_PREVIEW:
                print(f"Body: {body[:200]}...")
            log_result("dry_run", name, email, "Dry run mode", subject)
            stats['sent'] += 1
            sent_emails.add(email)
            continue

        try:
            send_email(email, subject, body, from_name)
            print(f"✅ Email sent successfully to {email}")
            log_result("sent", name, email, "Email sent", subject)
            stats['sent'] += 1
            sent_emails.add(email)
        except Exception as e:
            print(f"❌ Send failed: {e}")
            log_result("failed", name, email, f"Send error: {e}")
            stats['failed'] += 1

    print("\n📊 SUMMARY:")
    for k, v in stats.items():
        print(f"{k.replace('_', ' ').capitalize()}: {v}")

# ─────────────────────────────────────────────
# 🏁 Entry Point
# ─────────────────────────────────────────────
async def main_runner(from_name: str = None):
    clear_logs()
    await main(from_name)

if __name__ == "__main__":
    asyncio.run(main_runner())