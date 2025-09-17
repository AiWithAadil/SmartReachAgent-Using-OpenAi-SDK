# 🚀 SmartReach Agent

![SmartReach Agent Banner](./assets/banner.png)

*An AI-powered email marketing automation system that streamlines outreach, tracks replies, and responds intelligently - perfect for startups and lean marketing teams.*

## ✨ Features

- 🎯 **Personalized Campaigns**: AI-powered email personalization using Google Gemini API
- 📊 **CSV Bulk Upload**: Upload hundreds of leads effortlessly
- 🔄 **Automatic Reply Tracking**: IMAP integration monitors responses in real-time
- 🤖 **Intelligent AI Responses**: Automated customer reply handling with escalation
- 📈 **Performance Dashboard**: Clean Next.js interface with campaign analytics
- 📧 **Smart Notifications**: Email alerts for new replies and escalations
- 🎨 **Modern UI**: Dark-mode first design with Tailwind CSS and shadcn/ui

## 🏗️ Architecture

```
smartreach-agent/
├── backend/                    # FastAPI Python backend
│   ├── main.py                # Application entry point
│   ├── send_email_agent.py    # Email campaign management
│   ├── read_reply_tracker.py  # IMAP reply monitoring
│   ├── responder_agent.py     # AI response generation
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   ├── Data/                  # JSON/CSV storage
│   │   ├── temp_contacts.csv  # Contact uploads
│   │   ├── replies.json       # Customer replies
│   │   └── product_info.json  # Campaign data
│   └── logs/                  # System logs
│       ├── email_logs.txt
│       ├── reply_logs.txt
│       └── conversation_log.json
└── frontend/                   # Next.js 14 + TypeScript
    ├── components/            # Reusable UI components
    ├── pages/                 # Application pages
    ├── lib/                   # API utilities
    └── styles/                # Tailwind CSS
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | FastAPI, Python, OpenAI SDK |
| **Frontend** | Next.js 14 + TypeScript |
| **AI** | Google Gemini SDK |
| **Email** | Gmail SMTP/IMAP |
| **Styling** | Tailwind CSS + shadcn/ui |
| **Storage** | JSON/CSV files (lightweight) |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- Gmail account with App Password
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartreach-agent.git
   cd smartreach-agent
   ```

2. **Setup Backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials:
   # - Gmail SMTP/IMAP settings
   # - Google Gemini API key
   # - Notification email settings
   ```

4. **Setup Frontend**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Run the Application**
   
   Backend (Terminal 1):
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   
   Frontend (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

6. **Access Dashboard**
   Open [http://localhost:3000](http://localhost:3000)

## 📝 Usage Example

Here's how a startup founder might use SmartReach Agent:

1. **Upload Leads**: Drop a CSV file with 500 conference contacts
2. **Create Campaign**: Write a personalized product offer email
3. **Launch & Track**: Send campaigns and monitor replies automatically  
4. **AI Responses**: Let the system handle 120+ customer inquiries about pricing
5. **Analyze Results**: View response rates to identify hot leads

## 🔧 Configuration

### Environment Variables

```env
# Gmail Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-app-password

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Notification Settings  
NOTIFICATION_EMAIL=alerts@yourcompany.com

# API Settings
FASTAPI_URL=http://localhost:8000
```

### CSV Format

Your contact CSV should include these columns:

```csv
name,email,company,custom_field_1,custom_field_2
John Doe,john@example.com,Acme Corp,Software,Manager
Jane Smith,jane@startup.com,Tech Inc,AI,Founder
```

## 🔄 How It Works

### Email Campaign Flow
1. **CSV Upload** → Process contacts and validate emails
2. **Personalization** → Gemini AI customizes each email
3. **SMTP Delivery** → Send via Gmail with tracking
4. **IMAP Monitoring** → Scan inbox every 15 minutes for replies

### AI Response System
1. **Reply Detection** → Identify customer responses using headers
2. **Context Analysis** → Gemini processes reply content and intent
3. **Smart Response** → Generate appropriate replies automatically
4. **Human Escalation** → Flag complex queries for manual review

### Notification System
- 📩 **New Reply Alerts**: Instant email notifications
- ⚠️ **Escalation Warnings**: When AI needs human intervention
- 📊 **Daily Summaries**: Campaign performance reports

## 🎯 Core Features Deep Dive

### Dashboard Overview
- **Campaign Metrics**: Total sent, replies received, AI responses
- **Performance Charts**: Response rates and engagement analytics
- **Quick Actions**: Launch campaigns, view recent replies

### Campaign Management
- **Drag & Drop CSV**: Easy contact list uploads
- **Live Email Preview**: See personalized content before sending
- **Template Library**: Reusable campaign templates

### Reply Intelligence
- **Auto-Classification**: Categorize replies by intent and priority
- **Response Approval**: Review AI responses before sending
- **Conversation Threading**: Maintain context across exchanges

## 🔮 Roadmap

### Phase 1 (Current)
- ✅ Core email automation
- ✅ AI reply system
- ✅ Next.js dashboard

### Phase 2 (Next 3 months)
- 🔄 OAuth2 authentication
- 🔄 PostgreSQL database integration
- 🔄 Apache Airflow scheduling

### Phase 3 (6+ months)
- 📋 Advanced analytics dashboard
- 👥 Team collaboration features
- 🔐 Enterprise security features
- 📱 Mobile application

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Google Gemini](https://ai.google.dev/) for AI capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the robust backend framework
- [Next.js](https://nextjs.org/) for the modern frontend experience
- [Tailwind CSS](https://tailwindcss.com/) & [shadcn/ui](https://ui.shadcn.com/) for beautiful UI components

## 📞 Support

- 📧 **Email**: support@smartreach-agent.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/smartreach-agent/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/smartreach-agent/discussions)

---

<div align="center">
  <p>Built with ❤️ for modern marketing teams</p>
  <p>⭐ Star this repo if you find it useful!</p>
</div>
