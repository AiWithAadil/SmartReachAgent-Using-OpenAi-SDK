# 🚀 SmartReach Agent

![SmartReach Agent Banner](./assets/banner.png)

*An AI-powered email marketing automation system that transforms how businesses manage email outreach*

## 📋 What is SmartReach Agent?

SmartReach Agent is an AI-powered email marketing solution designed for startups and lean marketing teams who need automated engagement without the complexity of traditional CRMs.

### ✨ What It Does

- **Sends Personalized Campaigns**: Uses Google Gemini AI to create personalized email campaigns from CSV uploads
- **Tracks Replies Automatically**: Monitors Gmail inbox via IMAP to capture customer responses
- **Responds with AI Intelligence**: Automatically generates intelligent replies to customer inquiries
- **Visualizes Performance**: Displays campaign metrics and response rates in a clean dashboard
- **Smart Notifications**: Sends email alerts for new replies and escalations

## 🔄 How It Works

### Email Campaign Flow
1. **Upload CSV**: Upload contact lists with customer information
2. **AI Personalization**: Gemini API personalizes each email based on contact data
3. **SMTP Sending**: Delivers campaigns via Gmail SMTP
4. **IMAP Monitoring**: Scans inbox every 15 minutes for replies using In-Reply-To headers
5. **AI Response Generation**: Processes replies and generates appropriate responses
6. **Human Escalation**: Flags complex queries that need manual intervention

### Example Use Case
A startup founder uses SmartReach Agent to:
1. Upload 500 leads from a conference (contacts.csv)
2. Send a personalized product offer email to each lead
3. Automatically handle 120+ customer inquiries about pricing and features
4. View response rates in the dashboard to identify hot leads
5. Get instant notifications when important replies come in

## 🏗️ Architecture

The system consists of three main components:

### Backend (FastAPI + Python)
- **Email Campaign Management**: Processes CSV uploads and sends personalized emails
- **Reply Tracking System**: IMAP integration that monitors Gmail for responses
- **AI Response Engine**: Uses Google Gemini to generate intelligent replies
- **Notification System**: Email alerts for new replies and escalations

### Frontend (Next.js + TypeScript)
- **Dashboard Overview**: Campaign performance metrics and analytics
- **Campaign Management**: CSV upload, email creation, and live preview
- **Reply Management**: View responses, approve AI replies, handle escalations
- **Logs & Data**: Access to email logs, notification reports, and reply data

### Data Storage
- **Lightweight Storage**: JSON/CSV files for contacts, replies, and campaign data
- **Structured Logs**: Comprehensive logging for email activities, replies, and AI conversations

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python, OpenAI SDK |
| **Frontend** | Next.js 14 + TypeScript |
| **AI Engine** | Google Gemini SDK |
| **Email Service** | Gmail SMTP/IMAP |
| **UI Framework** | Tailwind CSS + shadcn/ui |
| **Data Storage** | JSON/CSV files |

## 📊 Key Features

### Automated Email Campaigns
- CSV bulk upload processing
- AI-powered email personalization
- Live email preview before sending
- Campaign performance tracking

### Intelligent Reply Handling
- Automatic reply detection and classification
- AI-generated responses using conversation context
- Human escalation for complex queries
- Reply approval system with manual override

### Smart Notification System
- Instant email alerts for new customer replies
- Escalation notifications when AI needs human intervention
- Comprehensive logging and audit trail

### Clean Dashboard Interface
- Dark-mode first design
- Responsive layout with Tailwind CSS
- Real-time campaign metrics
- Easy-to-use management interface

## 🎯 Perfect For

- **Startups** looking to automate their outreach without expensive tools
- **Small Marketing Teams** that need to scale their email campaigns
- **Solo Entrepreneurs** who want AI-powered customer engagement
- **Lean Organizations** seeking efficient email marketing automation

---

<div align="center">
  <p>Built with ❤️ for modern marketing automation</p>
</div>
