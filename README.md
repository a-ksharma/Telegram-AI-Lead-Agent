# Telegram AI Lead Agent

A production-ready AI agent built on Telegram that autonomously handles incoming leads — qualifying them through conversation, booking discovery calls, sending follow-up emails, and escalating to a human when needed. Built to showcase AI automation capabilities for an early-stage agency.

---

## What It Does

When a lead messages the bot on Telegram:

1. **Onboards** them with a structured qualification flow (business type, budget, timeline, goals)
2. **Qualifies** them through intelligent AI conversation powered by Groq
3. **Books discovery calls** directly on Google Calendar with an auto-generated Meet link
4. **Sends follow-up emails** via Gmail after qualification or escalation
5. **Escalates to admin** via Telegram alert when human intervention is needed
6. **Stores everything** in Supabase — leads, conversations, bookings, tool call logs
7. **Displays it all** in a Streamlit admin dashboard with filters, lead detail, and status management

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| Bot Framework | `python-telegram-bot` (async) |
| AI Provider | Groq (primary, free tier) |
| AI Fallback | Google Gemini (`google-genai`) |
| Database | Supabase (PostgreSQL) |
| Calendar | Google Calendar API (OAuth2) |
| Email | Gmail API (OAuth2) |
| Dashboard | Streamlit |
| Deployment | Render (two services) |
| Config | `python-dotenv` |

---

## Project Structure

```
lead-agent/
├── main.py                    # Entry point — webhook server + handler registration
├── config.py                  # All env vars loaded here; all modules import from here
├── requirements.txt
├── .env                       # Never committed — see Environment Variables section
├── handlers/
│   ├── message_handler.py     # Incoming message routing + AI response dispatch
│   └── onboarding_handler.py  # ConversationHandler for structured onboarding flow
├── ai_engine/
│   ├── __init__.py            # Provider switch via LLM_PROVIDER env var
│   ├── groq.py                # Groq client + tool-calling while loop
│   ├── gemini.py              # Gemini client (future use)
│   └── tools/
│       ├── __init__.py        # TOOL_REGISTRY + execute_tool() dispatcher
│       ├── schemas.py         # Groq-compatible tool JSON schemas (5 tools)
│       ├── calendar.py        # check_availability, book_call, cancel_call
│       └── gmail.py           # send_followup_email
├── database/
│   └── db.py                  # All Supabase read/write functions
└── dashboard/
    └── app.py                 # Streamlit admin dashboard (5 pages)
```

---

## Database Schema

Five tables in Supabase:

- **`leads`** — core lead record (telegram_user_id, name, email, status, priority, onboarding answers)
- **`chat_history`** — full conversation log per lead (role: user/assistant only)
- **`onboarding_history`** — structured onboarding responses
- **`bookings`** — scheduled discovery calls (calendar_event_id, meet_link, scheduled_at)
- **`tool_call_logs`** — every tool invocation with inputs, result, success flag

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_telegram_user_id

# AI Providers
LLM_PROVIDER=groq                  # or "gemini"
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key     # optional, for future use

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Deployment
RENDER_EXTERNAL_URL=https://your-bot-service.onrender.com
PORT=8000
```

---

## Google OAuth Setup

This project uses OAuth2 (not service accounts) for Calendar and Gmail — required for personal Google accounts.

**One-time local setup:**

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → enable **Google Calendar API** and **Gmail API**
3. OAuth consent screen → External user type → add your Gmail as test user
4. Create credentials → **Desktop App** type → download as `credentials.json`
5. Place `credentials.json` in the project root
6. Run the bot locally once — browser will open for authorization
7. `token.pickle` (Calendar) and `gmail_token.pickle` (Gmail) are auto-generated and auto-refreshed

**For Render deployment:** upload `credentials.json`, `token.pickle`, and `gmail_token.pickle` as **Secret Files** in your Render service settings, using their exact filenames as paths.

**Scopes used:**
- `https://www.googleapis.com/auth/calendar` — full calendar access (required for freebusy API)
- `https://www.googleapis.com/auth/gmail.send` — send-only, minimal privilege

> These files are gitignored. Never commit them.

---

## AI Tool Calling

The bot uses Groq's tool calling API with 5 registered tools:

| Tool | Trigger | External API |
|---|---|---|
| `check_calendar_availability` | Lead asks when to meet | Google Calendar freebusy |
| `book_discovery_call` | Lead confirms a slot | Google Calendar + Meet |
| `cancel_call` | Lead cancels booking | Google Calendar |
| `send_followup_email` | Lead qualified or escalated | Gmail |
| `update_lead_priority` | LLM detects high-value lead | Supabase |

Tool loop runs up to 3 iterations. If max iterations hit, bot escalates to admin automatically.

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (polling mode for local dev — switch to webhook for production)
python main.py

# Run the dashboard
streamlit run dashboard/app.py
```

> For local development, temporarily switch `run_webhook` back to `run_polling` in `main.py`.

---

## Deployment on Render

This project deploys as **two separate Render services** from the same GitHub repo.

### Service 1 — Bot Backend (Web Service)

| Setting | Value |
|---|---|
| Type | Web Service |
| Start Command | `python main.py` |
| Port | `8000` |

Environment variables: all from `.env` above, plus `RENDER_EXTERNAL_URL` set to this service's public URL.

Secret Files: `credentials.json`, `token.pickle`, `gmail_token.pickle`

### Service 2 — Dashboard (Web Service)

| Setting | Value |
|---|---|
| Type | Web Service |
| Start Command | `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0` |

Environment variables: `SUPABASE_URL`, `SUPABASE_KEY` only.

---

## Dashboard Pages

| Page | What It Shows |
|---|---|
| Overview | KPI metrics, status breakdown bar chart, recent activity |
| All Leads | Searchable/filterable lead table with status and priority |
| Lead Detail | Full profile, conversation history, bookings, tool logs per lead |
| Escalated | Leads needing human attention with quick-resolve actions |
| Bookings | All scheduled discovery calls with Google Meet links |

---

## Switching AI Providers

Zero code changes required. Set in `.env`:

```env
LLM_PROVIDER=groq     # default, free tier
LLM_PROVIDER=gemini   # when Gemini key is available
```

---

## Gitignore

Make sure these are in your `.gitignore`:

```
.env
credentials.json
token.pickle
gmail_token.pickle
__pycache__/
*.pyc
.venv/
```

---

## Milestones Completed

- [x] Echo bot
- [x] Stateful conversation
- [x] AI-powered replies
- [x] Lead capture to Supabase
- [x] Lead qualification flow
- [x] Human escalation with admin alerts
- [x] LLM provider abstraction (Groq + Gemini)
- [x] Onboarding flow
- [x] Tool calling (Calendar, Gmail, Supabase)
- [x] Streamlit admin dashboard
- [ ] Production deployment on Render
- [ ] Live end-to-end Telegram test