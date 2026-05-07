# Nexora Electronics — WhatsApp AI Customer Service Bot

A production-ready WhatsApp chatbot that uses **Retrieval-Augmented Generation (RAG)** to answer customer questions about a computer accessories store. Built with LangChain, ChromaDB, OpenAI, and Twilio.

## Features

- **RAG pipeline** — answers are grounded in real store data (products, FAQ, policies)
- **Conversation memory** — remembers context within each user's session (per WhatsApp number)
- **Multi-language** — responds in the same language the customer uses (Indonesian or English)
- **WhatsApp integration** — powered by Twilio Messaging API
- **Persistent storage** — conversation history stored in SQLite; vector store in ChromaDB

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| RAG Framework | LangChain |
| Vector Database | ChromaDB |
| Conversation History | SQLite |
| Messaging | Twilio WhatsApp API |
| Web Framework | FastAPI |
| Deployment | Railway |

## Project Structure

```
├── app/
│   └── services/
│       ├── chat.py        # LLM response generation (RAG + history)
│       ├── database.py    # SQLite conversation history
│       ├── rag.py         # Document loading, embedding, retrieval
│       └── webhook.py     # FastAPI /webhook endpoint (Twilio)
├── data/
│   ├── produk.csv         # Product catalog (40 items)
│   ├── faq.md             # Frequently asked questions
│   ├── kebijakan_toko.md  # Store policies (shipping, returns, warranty)
│   └── info_toko.md       # Store info, hours, contact
├── main.py                # App entry point
└── pyproject.toml
```

## How It Works

```
WhatsApp message
    → Twilio webhook (POST /webhook)
    → Retrieve relevant docs from ChromaDB (RAG)
    → Load conversation history from SQLite
    → Generate response with GPT-4o-mini
    → Save new messages to SQLite
    → Return response via Twilio
```

## Setup

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key
- Twilio account with WhatsApp Sandbox

### Installation

```bash
git clone https://github.com/your-username/ai-whatsapp-rag.git
cd ai-whatsapp-rag
uv sync
```

### Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-proj-...
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Running Locally

```bash
# Terminal 1 — start the server
uv run python main.py

# Terminal 2 — expose to the internet for Twilio webhook
ngrok http 8000
```

Set the ngrok HTTPS URL + `/webhook` as the webhook URL in your [Twilio WhatsApp Sandbox settings](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn).

## Deployment (Railway)

1. Push this repo to GitHub
2. Create a new project on [Railway](https://railway.app) and connect the repo
3. Add the following environment variables in Railway dashboard:
   - `OPENAI_API_KEY`
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
4. Railway will auto-detect the start command from `Procfile`
5. Copy the Railway public URL and update the Twilio webhook to `https://your-app.railway.app/webhook`

## Knowledge Base

The bot is pre-loaded with data for **Nexora Electronics**, a fictional computer accessories store, including:

- **40 products** across 10 categories: keyboards, mice, headsets, webcams, monitors, USB hubs, power banks, SSDs, laptop accessories, cables & adapters
- **28 FAQ entries** covering products, ordering, shipping, and returns
- Store policies on shipping, returns, and warranty
- Store info including hours, contact, and payment methods

## License

MIT
