import os
import json
import asyncio
import smtplib
from dotenv import load_dotenv
from datetime import datetime, timedelta
from email.message import EmailMessage
from pydantic import BaseModel, Field
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from agents.run import RunConfig

# 🔐 Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY2")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not gemini_api_key or not SENDER_EMAIL or not APP_PASSWORD:
    raise ValueError("Missing required environment variables")

# 🤖 Model setup
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

# 📁 File paths
REPLIES_JSON = "./Data/replies.json"
PRODUCT_INFO_JSON = "./Data/product_info.json"
CONVERSATION_LOG = "./logs/conversation_log.json"
PROCESSED_REPLIES = "./Data/processed_replies.json"
NOTIFICATION_LOG = "./logs/notification_log.txt"
REPLY_LOG_FILE = "./logs/reply_logs.txt"

# 🧠 AI tool
class ResponseInput(BaseModel):
    customer_message: str = Field(..., description="Customer's message")
    customer_name: str = Field(..., description="Customer's name")
    conversation_history: str = Field(..., description="Previous context")



# 📦 Utilities

def log_reply_status(email, status, detail=""):
    """Log each reply's outcome"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs(os.path.dirname(REPLY_LOG_FILE), exist_ok=True)
    with open(REPLY_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {status} | Customer: {email} | {detail}\n")


def load_json_file(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"⚠️ Load error {filepath}: {e}")
        return []

def save_json_file(filepath, data):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Save error {filepath}: {e}")

def load_product_info():
    try:
        with open(PRODUCT_INFO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load product info: {e}")
        return {"offer": "", "description": ""}

def get_conversation_history(customer_email):
    conversations = load_json_file(CONVERSATION_LOG)
    history = [c for c in conversations if c.get('customer_email') == customer_email]
    if history:
        return "\n".join([  # FIXED
            f"Previous: {c.get('customer_message', '')} | Response: {c.get('ai_response', '')}"
            for c in history[-3:]
        ])
    return "No previous conversation history."

def was_manually_handled(customer_email, hours=24):
    try:
        with open(NOTIFICATION_LOG, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            cutoff = datetime.now() - timedelta(hours=hours)
            for line in lines:
                if customer_email in line and "MANUAL_HANDLED" in line:
                    timestamp_str = line.split('[')[1].split(']')[0]
                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    if log_time > cutoff:
                        return True
        return False
    except:
        return False

def mark_as_manually_handled(customer_email):
    os.makedirs(os.path.dirname(NOTIFICATION_LOG), exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(NOTIFICATION_LOG, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] MANUAL_HANDLED | Customer: {customer_email}\n")  # FIXED

@function_tool
def generate_response(input: ResponseInput) -> str:
    return (
        f"Analyze the customer message: '{input.customer_message}' from {input.customer_name}. "
        f"Context: {input.conversation_history}. "
        f"Use available product info. If unknown, respond with: 'NEEDS_HUMAN_INTERVENTION: [reason]'. "
        f"Return JSON with 'response' and 'needs_human' (true/false)."
    )

# 🤖 AI Generator
async def generate_ai_response(message, name, email, product_info):
    history = get_conversation_history(email)
    instructions = f"""\"\"\"
        You are a professional customer service assistant.

        PRODUCT/SERVICE INFO:
        Offer: {product_info.get('offer', '')}
        Description: {product_info.get('description', '')}

        RULES:
        1. If the customer's question can be answered using this info, respond clearly.
        2. DO NOT provide multiple-choice options like Yes, No, Maybe.
        3. If details are missing, respond with "NEEDS_HUMAN_INTERVENTION: [reason]".
        4. Use JSON: 'response' and 'needs_human' fields.
        \"\"\""""

    agent = Agent(name="CustomerSupportBot", instructions=instructions, tools=[generate_response], model=model)
    query = f"Customer {name} asked: '{message}'."
    try:
        result = await Runner.run(agent, query, run_config=config)
        output = result.final_output.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(output)
        resp = parsed.get("response", "")
        if "NEEDS_HUMAN_INTERVENTION" in resp:
            return None, resp.split("NEEDS_HUMAN_INTERVENTION:")[1].strip()
        return resp, None if not parsed.get("needs_human", False) else "Complex query"
    except Exception as e:
        return None, str(e)

# 📤 Email
def send_email_response(to_email, subject, body, message_id=None):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Re: {subject}" if not subject.startswith("Re:") else subject
        msg['From'] = f"Customer Service <{SENDER_EMAIL}>"
        msg['To'] = to_email
        if message_id:
            msg['In-Reply-To'] = message_id
            msg['References'] = message_id
        msg.set_content("Your email client does not support HTML.")
        msg.add_alternative(body, subtype="html")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ Failed to send: {e}")
        return False

def send_notification_to_user(email, name, subject, body, gmail_link, reason):
    try:
        msg = EmailMessage()
        msg['Subject'] = f"🚨 Customer Needs Attention: {name}"
        msg['From'] = f"AI Assistant <{SENDER_EMAIL}>"
        msg['To'] = SENDER_EMAIL
        html = f"""
        <html><body><h2>🚨 Manual Intervention Required</h2>
        <p><b>Customer:</b> {name} ({email})</p>
        <p><b>Reason:</b> {reason}</p>
        <p>{body}</p>
        <a href="{gmail_link}">📧 Open in Gmail</a>
        </body></html>
        """
        msg.set_content("Customer needs attention.")
        msg.add_alternative(html, subtype="html")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(NOTIFICATION_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] NOTIFICATION_SENT | Customer: {email} | Reason: {reason}\n")  # FIXED
        return True
    except Exception as e:
        print(f"❌ Notification failed: {e}")
        return False

def log_conversation(email, name, msg, response, needs_human, reason):
    conversations = load_json_file(CONVERSATION_LOG)
    conversations.append({
        "timestamp": datetime.now().isoformat(),
        "customer_email": email,
        "customer_name": name,
        "customer_message": msg,
        "ai_response": response,
        "needs_human": needs_human,
        "escalation_reason": reason
    })
    save_json_file(CONVERSATION_LOG, conversations)

# 🚀 Main logic
async def process_customer_replies():
    replies = load_json_file(REPLIES_JSON)
    product_info = load_product_info()
    stats = {'ai_responded': 0, 'escalated_to_human': 0, 'skipped_manual': 0, 'failed': 0}

    for reply in replies[:]:  # Iterate safely
        email = reply.get('from_email', '').lower()
        name = email.split('@')[0].title()
        subject = reply.get('subject', 'No Subject')
        body = reply.get('body', '')
        gmail_link = reply.get('gmail_link', '')
        timestamp = reply.get('timestamp', '')

        if was_manually_handled(email, hours=24):
            stats['skipped_manual'] += 1
            log_reply_status(email, "SKIPPED_MANUAL", "Handled within last 24 hours")
            continue

        ai_response, reason = await generate_ai_response(body, name, email, product_info)
        if ai_response:
            html = f"<html><body><p>Hi {name},</p><p>{ai_response}</p><p>Regards,<br>Customer Service Team</p></body></html>"
            if send_email_response(email, subject, html):
                log_conversation(email, name, body, ai_response, False, None)
                stats['ai_responded'] += 1
                log_reply_status(email, "AI_RESPONDED", f"Subject: {subject}")
                replies.remove(reply)
        else:
            if send_notification_to_user(email, name, subject, body, gmail_link, reason):
                mark_as_manually_handled(email)
                log_conversation(email, name, body, None, True, reason)
                stats['escalated_to_human'] += 1
                log_reply_status(email, "ESCALATED", f"Reason: {reason}")
                replies.remove(reply)
            else:
                stats['failed'] += 1
                log_reply_status(email, "NOTIFICATION_FAILED", reason)

    save_json_file(REPLIES_JSON, replies)
    print("📊 SUMMARY:", stats)

# 🧪 Entry
# 🚀 Main logic
async def run_responder():
    await process_customer_replies()

# 🧪 Standalone run
if __name__ == "__main__":
    try:
        asyncio.run(run_responder())
    except Exception as e:
        print(f"❌ Error: {e}")

