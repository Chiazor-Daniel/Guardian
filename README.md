# Guardian

A simple tool to check links and files for scams using AI.

## How it works

1. Paste a suspicious link or upload a file
2. Guardian scans it using AI (via Groq)
3. Get a risk score and advice on what to do

## Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY=your_key_here

# Run server
uvicorn app.main:app --reload --port 8005
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

## Getting a Groq API key

Sign up at https://console.groq.com/ - it's free to start.

## What it checks

- Domain age (new sites are suspicious)
- SSL certificates
- Page content for phishing keywords
- Visual analysis of screenshots
- Cross-references multiple sources

## Tech stack

- FastAPI (Python)
- React + Tailwind
- Groq LLM API
- Playwright for web scraping
