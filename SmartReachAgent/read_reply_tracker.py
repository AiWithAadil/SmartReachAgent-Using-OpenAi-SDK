import os
import json
import asyncio
import imaplib
import email
import smtplib
from dotenv import load_dotenv
from datetime import datetime
from email.header import decode_header
from email.utils import parseaddr
from email.message import EmailMessage

# 🌍 Environment Setup
load_dotenv()
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# ✉️ Send Notification Email
def send_notification_email(replies):
    from_name = "Agent Notification"
    to_email = SENDER_EMAIL
    msg = EmailMessage()
    msg['Subject'] = f"📥 {len(replies)} New Reply Notification(s)"
    msg['From'] = f"{from_name} <{SENDER_EMAIL}>"
    msg['To'] = to_email

    html = f"<h2>You've got {len(replies)} new replies!</h2><ul>"
    for r in replies:
        html += f"<li><b>From:</b> {r['from_email']}<br>"
        html += f"<b>Subject:</b> {r['subject']}<br>"
        if r['gmail_link']:
            html += f"<a href='{r['gmail_link']}' target='_blank'>📩 View in Gmail</a><br>"
        html += "<hr></li>"
    html += "</ul><p>— SDK Agent Bot</p>"

    msg.set_content("Your client does not support HTML.")
    msg.add_alternative(html, subtype='html')

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
        print(f"✅ Notification email sent to {SENDER_EMAIL}")
    except Exception as e:
        print(f"❌ Failed to send notification email: {e}")

# 📁 Load Sent Emails
def load_sent_emails():
    sent_emails = set()
    log_path = os.path.join(os.path.dirname(__file__), "logs", "email_logs.txt")
    if not os.path.exists(log_path):
        print("⚠️ Log file not found:", log_path)
        return sent_emails

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if "SENT |" in line and "Email:" in line:
                try:
                    email_addr = line.split("Email:")[1].split("|")[0].strip()
                    sent_emails.add(email_addr.lower())
                except:
                    continue
    return sent_emails

# 📨 IMAP Utilities
def connect_imap():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(SENDER_EMAIL, APP_PASSWORD)
    return imap

def decode_subject(raw_subject):
    subject, encoding = decode_header(raw_subject)[0]
    if isinstance(subject, bytes):
        return subject.decode(encoding or 'utf-8', errors='ignore')
    return subject

def extract_email_address(from_header):
    _, addr = parseaddr(from_header)
    return addr.lower()

def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except:
                    pass
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except:
            pass
    return body.strip()

def get_gmail_link(imap, eid):
    try:
        _, msg_data = imap.fetch(eid, "(X-GM-MSGID)")
        response = msg_data[0].decode()
        if "X-GM-MSGID" in response:
            msgid = response.split("X-GM-MSGID ")[1].split(")")[0]
            msgid_hex = hex(int(msgid))[2:]
            return f"https://mail.google.com/mail/u/0/#inbox/{msgid_hex}"
    except Exception as e:
        print(f"⚠️ Error generating Gmail link: {e}")
    return ""

# Build IMAP OR query recursively
def build_or_query(emails):
    emails = list(emails)
    if not emails:
        return None
    if len(emails) == 1:
        return f'FROM "{emails[0]}"'
    elif len(emails) == 2:
        return f'OR FROM "{emails[0]}" FROM "{emails[1]}"'
    else:
        mid = len(emails) // 2
        return f'OR ({build_or_query(emails[:mid])}) ({build_or_query(emails[mid:])})'

# 🔍 Find Replies
async def find_and_save_replies():
    print("🔍 Checking Primary tab for replies to our emails...")

    contacted_emails = load_sent_emails()
    if not contacted_emails:
        print("ℹ️ No sent emails found in logs.")
        return

    try:
        imap = connect_imap()
        imap.select('"[Gmail]/Important"')

        raw_query = build_or_query(contacted_emails)
        search_query = f'(UNSEEN {raw_query})'
        print(f"📬 IMAP Search Query: {search_query}")
        print(f"📬 Looking for replies from {len(contacted_emails)} addresses...")

        status, messages = imap.search(None, search_query)
        if status != "OK":
            print("❌ Failed to fetch messages.")
            return

        email_ids = messages[0].split()
        replies = []

        for eid in email_ids:
            try:
                _, msg_data = imap.fetch(eid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                from_email = extract_email_address(msg.get("From"))

                if from_email not in contacted_emails:
                    continue

                if msg.get("In-Reply-To"):
                    gmail_link = get_gmail_link(imap, eid)
                    reply = {
                        "from_email": from_email,
                        "subject": decode_subject(msg.get("Subject", "No Subject")),
                        "body": get_email_body(msg),
                        "timestamp": datetime.now().isoformat(),
                        "gmail_link": gmail_link
                    }
                    replies.append(reply)
                    imap.store(eid, '+FLAGS', '\\Seen')
            except Exception as e:
                print(f"⚠️ Error reading message: {e}")

        if replies:
            replies_path = os.path.join(os.path.dirname(__file__), "Data", "replies.json")
            os.makedirs(os.path.dirname(replies_path), exist_ok=True)

            existing = []
            if os.path.exists(replies_path):
                with open(replies_path, "r", encoding="utf-8") as f:
                    try:
                        existing = json.load(f)
                    except json.JSONDecodeError:
                        pass

            all_replies = existing + replies
            with open(replies_path, "w", encoding="utf-8") as f:
                json.dump(all_replies, f, indent=2, ensure_ascii=False)

            print(f"📎 Saved {len(replies)} new replies. Total now: {len(all_replies)}")
            send_notification_email(replies)
        else:
            print("👭 No new replies found.")

    except Exception as e:
        print(f"❌ IMAP error: {e}")
    finally:
        try:
            imap.logout()
        except:
            pass


# 🧪 Standalone run
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(find_and_save_replies())
    except Exception as e:
        print(f"❌ Error: {e}")

