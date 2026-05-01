# 📊 Smart Financial Research & Portfolio Advisory System

> A locally-hosted Multi-Agent System (MAS) that automates end-to-end investment research
> using CrewAI and Ollama — **zero cloud costs, full privacy**.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/framework-CrewAI-orange.svg)](https://crewai.com/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green.svg)](https://ollama.com/)
[![React](https://img.shields.io/badge/frontend-React-61dafb.svg)](https://react.dev/)

**SE4010 – CTSE | Assignment 2 – Machine Learning | SLIIT**

---

## 🎯 Why Would You Use This Application?

### Imagine This Scenario

You have **$10,000** to invest and you're considering Apple (AAPL), Microsoft (MSFT), and Google (GOOGL). Before investing, you need to answer:

- 💲 _What are the current prices, and are they trending up or down?_
- 📰 _What's the latest news saying — is the market bullish or bearish on these stocks?_
- ⚠️ _How risky are they? What's my worst-case scenario?_
- 💼 _Which ones should I actually buy, and how should I split my money?_

**Doing this manually takes 3-4 hours:**
1. Open Yahoo Finance → check each stock → note prices, P/E ratios, 52-week ranges
2. Google financial news → read 10-15 articles → try to judge sentiment yourself
3. Open Excel → download historical data → calculate volatility, Sharpe ratio, VaR
4. Try to synthesize all of this into a coherent decision

**With this application, it takes 2-3 minutes.** Type one sentence, and 4 AI agents do all of the above automatically.

### What Exactly Does It Do?

You type a plain-English query:
```
Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio
```

And the system produces:

| Step | Agent | What It Does | Real Output |
|------|-------|-------------|-------------|
| 1 | 🎯 **Coordinator** | Parses your query, identifies tickers, fetches **live market data** from Yahoo Finance | AAPL: $195.20 (+1.3%), P/E: 28.5, Market Cap: $2.8T |
| 2 | 📊 **Market Analyst** | Scrapes financial RSS news feeds, runs **VADER NLP sentiment analysis** on each headline | AAPL: BULLISH (score: +0.45), 5 articles analyzed |
| 3 | ⚠️ **Risk Specialist** | Calculates **quantitative risk metrics** using 6 months of historical price data | AAPL: Volatility 22%, Beta 1.15, Sharpe 1.45, VaR -2.5% |
| 4 | 💼 **Portfolio Advisor** | Synthesizes everything into a **professional advisory report** with recommendations | "Allocate 40% AAPL, 35% MSFT, 25% GOOGL based on risk-adjusted returns..." |

### The Final Output

You get a **professional Markdown advisory report** that includes:
- 📈 **Market Summary** — Current prices, trends, and key financial metrics for each stock
- 💬 **Sentiment Analysis** — What the news says, with actual headlines and sentiment scores
- ⚠️ **Risk Assessment** — Volatility, beta, Sharpe ratio, VaR, max drawdown per ticker
- 💼 **Recommendations** — Specific allocation suggestions based on your risk profile
- 🔍 **Disclaimers** — Clear statement that this is AI-generated, not financial advice

The report is saved as a `.md` file in the `reports/` folder and displayed in the web dashboard.

### Who Is This For?

| User | How They Benefit |
|------|-----------------|
| 🧑‍🎓 **Students** | Learn how multi-agent AI systems work with a real, practical application |
| 📈 **Individual Investors** | Get free, instant research before making investment decisions |
| 👩‍🏫 **Finance Educators** | Demonstrate how risk metrics (VaR, Sharpe, Beta) work with live data |
| 🏢 **Small Advisory Firms** | Automate routine research reports for clients |
| 🔬 **AI Researchers** | Study multi-agent collaboration, tool-use, and observability patterns |

### Why Multi-Agent Instead of a Single Chatbot?

| Single Chatbot (e.g., ChatGPT) | This Multi-Agent System |
|--------------------------------|------------------------|
| One model tries to do everything | **4 specialists** collaborate, each with expertise |
| **Hallucinate** financial numbers | Every number comes from **real tools** — yfinance, VADER, NumPy |
| No audit trail — you can't verify | Full **SQLite database** + structured JSON logging of every action |
| Needs internet + API keys ($$$) | Runs **100% locally** via Ollama — zero cost, full privacy |
| Results are inconsistent | **Structured pipeline** ensures repeatable, verifiable output |
| Can't use external tools | Each agent has a **dedicated tool** (market data, sentiment, risk, reports) |
| No observability | You can **watch each agent work in real-time** via the dashboard |

### Key Benefits

- 🆓 **Zero Cost** — No API keys, no subscriptions, no cloud fees. Everything runs on your machine.
- 🔒 **Full Privacy** — Your financial queries never leave your computer. No data sent to OpenAI, Google, etc.
- ⚡ **Fast** — 4 agents work together in a pipeline. Results in minutes, not hours.
- 📊 **Real Data** — Every metric comes from real tools (Yahoo Finance, VADER NLP, NumPy). Nothing hallucinated.
- 🔍 **Transparent** — Watch every agent action in real-time. Every tool call is logged and auditable.
- 📄 **Professional Output** — Gets a formatted report you can actually share or reference.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  🌐 React Frontend (Vite)  —  http://localhost:5173             │
│  ├── Query Input + Sample Chips                                 │
│  ├── Animated 4-Step Agent Pipeline Visualization               │
│  ├── Market Data / Sentiment / Risk Summary Cards               │
│  ├── Advisory Report Viewer (Markdown rendered)                 │
│  ├── Real-time Agent Activity Log (SSE streaming)               │
│  └── Session History from SQLite                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP + Server-Sent Events (SSE)
┌──────────────────────▼──────────────────────────────────────────┐
│  🐍 Flask REST API  —  http://localhost:5001                    │
│  ├── POST /api/research         → Submit query                  │
│  ├── GET  /api/research/:id     → Get results                   │
│  ├── GET  /api/research/:id/stream → Live agent logs (SSE)      │
│  ├── GET  /api/sessions         → Past sessions                 │
│  └── GET  /api/health           → Ollama connectivity check     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│  🤖 CrewAI Multi-Agent Pipeline                                 │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐  │
│  │Coordinator│→ │Market Analyst│→ │Risk Specialist│→│Advisor │  │
│  │ 🔧yfinance│  │🔧 VADER+RSS   │  │🔧 NumPy/Pandas│ │🔧Report│  │
│  └───────────┘  └──────────────┘  └──────────────┘  └────────┘  │
│                        ↕                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Pydantic State │ SQLite DB │ JSON Logger │ Callbacks    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │  🧠 Ollama LLM  │
              │  llama3:8b      │
              │  (runs locally) │
              └─────────────────┘
```

---

## ⚙️ How the System Works Internally (Step-by-Step Flow)

Here's exactly what happens when you type a query and click **Analyze**:

### Overview Flow

```
User types query
       │
       ▼
┌──────────────────┐
│  React Frontend  │  1. Sends POST /api/research { query: "..." }
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Flask API       │  2. Creates a query_id, starts background thread
│  (src/api.py)    │  3. Opens SSE stream to push live updates to frontend
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  ResearchCrew    │  4. Creates 4 agents + 4 tasks
│  (research_crew) │  5. Runs Crew.kickoff() → sequential pipeline
└────────┬─────────┘
         │
         ▼
   Agent Pipeline (steps 6–9 below)
         │
         ▼
┌──────────────────┐
│  Final Report    │  10. Returned to API → sent to frontend → displayed
└──────────────────┘
```

---

### Step 1: User Submits a Query

You type into the search box:
```
Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio
```

The **React frontend** (`App.jsx`) sends a `POST` request to the Flask API:
```javascript
// frontend/src/api.js
fetch('http://localhost:5001/api/research', {
  method: 'POST',
  body: JSON.stringify({ query: "Analyze AAPL, MSFT, GOOGL..." })
})
```

The API returns a `query_id` (e.g., `"a1b2c3d4"`) and the frontend immediately opens an **SSE (Server-Sent Events) stream** to receive real-time updates.

---

### Step 2: Flask API Starts the Pipeline

In `src/api.py`, the API creates a **background thread** so it doesn't block:

```python
# A new thread runs the pipeline
thread = threading.Thread(target=run_pipeline, args=(query_id, user_query))
thread.start()
```

Inside the thread, it creates a `ResearchCrew` instance which initializes:
- **AgentObserver** — logs every agent action as structured JSON
- **DatabaseManager** — saves the session to SQLite
- **ResearchState** — Pydantic model to track all data flowing through the pipeline

---

### Step 3: CrewAI Assembles the Team

The `ResearchCrew.run()` method (`src/crew/research_crew.py`) does this:

```
1. Creates 4 Agent instances (each with its own tool)
2. Creates 4 Task instances (each assigned to an agent)
3. Creates a Crew with Process.sequential
4. Calls crew.kickoff() → starts the pipeline
```

**Sequential process** means: Task 1 runs → its output becomes context for Task 2 → Task 2 runs → its output becomes context for Task 3 → and so on.

---

### Step 4: 🎯 Coordinator Agent Runs (Task 1)

**What it receives:** The raw user query string

**What it does:**
1. The LLM (Ollama llama3:8b) reads the query and decides to call the `Market Data Fetcher` tool
2. It identifies tickers: `AAPL`, `MSFT`, `GOOGL`
3. For **each ticker**, it calls the tool:

```python
# src/tools/market_data_fetcher.py
# The tool calls Yahoo Finance API:
stock = yf.Ticker("AAPL")
info = stock.info  # Gets price, P/E, market cap, etc.
history = stock.history(period="1mo")  # Gets historical prices
```

**What the tool returns** (real data from Yahoo Finance):
```json
{
  "ticker": "AAPL",
  "current_price": 195.20,
  "price_change_pct": 1.25,
  "volume": 55000000,
  "market_cap": 2800000000000,
  "pe_ratio": 28.5,
  "week_52_high": 199.62,
  "week_52_low": 124.17,
  "historical_prices": [170.0, 172.5, 174.0, 175.5, ...],
  "fetched_at": "2026-05-01T10:30:00"
}
```

**What the Coordinator outputs:** A JSON object containing all tickers + their market data. This becomes the **context** for the next agent.

---

### Step 5: 📊 Market Analyst Agent Runs (Task 2)

**What it receives:** The Coordinator's output (tickers + market data)

**What it does:**
1. The LLM reads the context and decides to call the `News Sentiment Analyzer` tool for each ticker
2. The tool fetches RSS news feeds and runs VADER NLP analysis:

```python
# src/tools/news_sentiment.py
# Fetches Google News RSS for "AAPL stock"
feed = feedparser.parse(f"https://news.google.com/rss/search?q={ticker}+stock")

# For each article, runs VADER sentiment:
analyzer = SentimentIntensityAnalyzer()
scores = analyzer.polarity_scores(headline)
# Returns: {'neg': 0.0, 'neu': 0.4, 'pos': 0.6, 'compound': 0.65}
```

**What the tool returns:**
```json
{
  "query": "AAPL",
  "articles_analyzed": 5,
  "average_sentiment": 0.35,
  "sentiment_label": "BULLISH",
  "top_headlines": [
    "Apple Reports Record Q4 Earnings",
    "iPhone Sales Exceed Expectations"
  ],
  "sentiment_distribution": { "bullish": 3, "neutral": 1, "bearish": 1 }
}
```

**What the Market Analyst outputs:** Sentiment analysis for all tickers. This + Coordinator's data becomes context for the next agent.

---

### Step 6: ⚠️ Risk Specialist Agent Runs (Task 3)

**What it receives:** Context from both previous agents (market data + sentiment)

**What it does:**
1. The LLM calls the `Risk Calculator` tool with all tickers
2. The tool downloads 6 months of historical prices and computes risk metrics using NumPy/Pandas:

```python
# src/tools/risk_calculator.py
# Downloads historical data
history = yf.Ticker("AAPL").history(period="6mo")
returns = history['Close'].pct_change().dropna()

# Calculates 5 key metrics:
volatility = returns.std() * np.sqrt(252)      # Annualized volatility
beta = cov(stock, market) / var(market)         # Market sensitivity
sharpe = (mean_return - risk_free) / std        # Risk-adjusted return
var_95 = np.percentile(returns, 5)              # 5% worst-case daily loss
max_drawdown = max peak-to-trough decline       # Worst historical drop
```

**What the tool returns:**
```json
{
  "individual_metrics": [
    {
      "ticker": "AAPL",
      "volatility": "22.00%",
      "beta": 1.15,
      "sharpe_ratio": 1.45,
      "var_95": "-2.50%",
      "max_drawdown": "-18.00%",
      "risk_category": "MEDIUM",
      "confidence": 0.85
    }
  ],
  "portfolio_summary": {
    "avg_volatility": "20.50%",
    "avg_beta": 1.10,
    "avg_sharpe": 1.54,
    "highest_risk_ticker": "GOOGL",
    "lowest_risk_ticker": "MSFT"
  }
}
```

**Risk categories are determined by a composite score:**
| Composite Score | Category |
|----------------|----------|
| < 0.3 | 🟢 LOW |
| 0.3 – 0.5 | 🟡 MEDIUM |
| 0.5 – 0.7 | 🟠 HIGH |
| > 0.7 | 🔴 CRITICAL |

---

### Step 7: 💼 Portfolio Advisor Agent Runs (Task 4)

**What it receives:** ALL context from the 3 previous agents (market data + sentiment + risk metrics)

**What it does:**
1. The LLM synthesizes all the data and formulates recommendations
2. It calls the `Report Generator` tool to create a formatted Markdown report:

```python
# src/tools/report_generator.py
# Builds a structured report with sections:
report = f"""
# 📊 Financial Advisory Report
## Executive Summary
{llm_generated_summary}

## 📈 Market Analysis
{formatted_market_data_tables}

## 💬 Sentiment Analysis
{formatted_sentiment_results}

## ⚠️ Risk Assessment
{formatted_risk_metrics_with_emoji_categories}

## 💼 Portfolio Recommendations
{llm_generated_recommendations}

## ⚖️ Disclaimer
> This report is AI-generated and does NOT constitute financial advice.
"""
```

3. The report is **saved to disk** at `reports/advisory_AAPL_MSFT_GOOGL_20260501.md`

---

### Step 8: Results Flow Back to the User

```
Report Generator saves .md file to reports/
       │
       ▼
CrewAI returns the report text as the crew result
       │
       ▼
ResearchCrew.run() packages everything:
  - result (report text)
  - state_summary (counts of data collected)
  - execution_summary (agents used, tools called, errors)
  - total_duration_ms
       │
       ▼
Flask API pushes a "complete" SSE event to the frontend
       │
       ▼
React frontend receives the event and renders:
  ✅ Pipeline steps all turn green
  ✅ Market Data / Sentiment / Risk cards populate
  ✅ Advisory Report viewer shows the formatted report
  ✅ Agent activity log shows all tool calls
```

---

### What Gets Saved (Persistence)

Every research session is permanently stored:

| Storage | What's Saved | Location |
|---------|-------------|----------|
| **SQLite Database** | Session ID, query, tickers, status, timestamps | `data/research.sqlite` |
| **SQLite Database** | Agent logs (every tool call, input/output, duration) | `data/research.sqlite` |
| **JSON Log Files** | Structured event logs with full execution trace | `logs/` directory |
| **Markdown Reports** | The final advisory report | `reports/` directory |

This means you can:
- View **past sessions** in the dashboard's Session History
- **Audit** exactly what each agent did (which tools it called, what data it received)
- **Compare** reports across different dates to see how analysis changes over time

---

### Real-Time Observability

While the pipeline runs, every agent action is logged and streamed:

```json
{"timestamp": "10:30:01", "agent": "Coordinator",       "event": "TOOL_CALL",    "tool": "Market Data Fetcher",      "input": "AAPL"}
{"timestamp": "10:30:03", "agent": "Coordinator",       "event": "TOOL_RESULT",  "output": "{price: 195.20, ...}",   "duration_ms": 1840}
{"timestamp": "10:30:04", "agent": "Coordinator",       "event": "TOOL_CALL",    "tool": "Market Data Fetcher",      "input": "MSFT"}
{"timestamp": "10:30:15", "agent": "Market Analyst",    "event": "TOOL_CALL",    "tool": "News Sentiment Analyzer",  "input": "AAPL"}
{"timestamp": "10:30:22", "agent": "Risk Specialist",   "event": "TOOL_CALL",    "tool": "Risk Calculator",          "input": "AAPL,MSFT,GOOGL"}
{"timestamp": "10:30:35", "agent": "Portfolio Advisor",  "event": "TOOL_CALL",    "tool": "Report Generator",         "input": "{all data...}"}
{"timestamp": "10:30:38", "agent": "SYSTEM",             "event": "COMPLETE",     "duration_ms": 37000}
```

You can watch this **live** in the dashboard's "Agent Activity Log" panel — each line appears in real-time as the agents work.

---

## 📋 Prerequisites

Before you start, you need **3 things** installed on your machine:

| Requirement | Version | Why |
|------------|---------|-----|
| **Python** | 3.9 or higher | Backend, agents, tools |
| **Node.js** | 18+ | React frontend |
| **Ollama** | Latest | Local LLM engine (no cloud needed) |

### Check Your Versions

```bash
python3 --version   # Should show 3.9+
node --version      # Should show 18+
npm --version       # Should show 8+
```

---

## 🚀 Complete Setup Guide (Step by Step)

### Step 1: Install Ollama (LLM Engine)

Ollama is the **brain** of the system. It runs the AI model locally on your machine.

```bash
# macOS — Install via Homebrew
brew install ollama

# OR download directly from https://ollama.com/download
```

**Start the Ollama server** (keep this terminal open):
```bash
ollama serve
```

**Pull the required AI model** (open a new terminal):
```bash
ollama pull llama3:8b
```

> ⏱️ This downloads ~4.7 GB. Only needed once.

**Verify it works:**
```bash
ollama run llama3:8b "Say hello in one word"
# Should respond with something like "Hello!"
```

---

### Step 2: Clone & Setup Python Backend

```bash
# Clone the repository
git clone <repository-url>
cd CTSE-02

# Create a Python virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate    # macOS / Linux
# venv\Scripts\activate     # Windows

# Install all Python dependencies
pip install -r requirements.txt
```

**Verify the backend works:**
```bash
python -c "from src.crew.research_crew import ResearchCrew; print('✅ Backend OK')"
```

---

### Step 3: Setup React Frontend

```bash
# Navigate to the frontend directory
cd frontend

# Install JavaScript dependencies
npm install

# Go back to project root
cd ..
```

**Verify the frontend builds:**
```bash
cd frontend && npm run build && cd ..
# Should show "✓ built in Xs" with no errors
```

---

### Step 4: Configure Environment (Optional)

Copy the example environment file:
```bash
cp .env.example .env
```

Default settings work out of the box. Edit `.env` only if you need to change:
```env
OLLAMA_BASE_URL=http://localhost:11434    # Ollama server URL
OLLAMA_MODEL=llama3:8b                   # AI model to use
LLM_TEMPERATURE=0.2                      # Lower = more focused responses
DATABASE_PATH=data/research.sqlite       # Where to store research history
```

---

## ▶️ How to Run the System

You need **3 terminals** running simultaneously:

### Terminal 1 — Ollama (LLM Server)
```bash
ollama serve
```
> Keep this running. This is the AI brain.

### Terminal 2 — Flask API (Python Backend)
```bash
cd CTSE-02
source venv/bin/activate
python -m src.api
```
> You should see:
> ```
> 📊 Financial Research MAS — API Server
> =============================================
>   API:       http://localhost:5001/api
>   Health:    http://localhost:5001/api/health
>   Frontend:  http://localhost:5173
> =============================================
> ```

### Terminal 3 — React Frontend (Vite Dev Server)
```bash
cd CTSE-02/frontend
npm run dev
```
> You should see:
> ```
>   VITE v8.x.x  ready in XXXms
>   ➜  Local:   http://localhost:5173/
> ```

### ✅ Open the Dashboard

Open your browser and go to: **http://localhost:5173**

You should see:
- ✅ **"System Online"** badge (green) in the top right
- ✅ Query input box with sample query chips
- ✅ "Ready to Analyze" empty state

---

## 💻 Using the System

### Via the Web Dashboard (Recommended)

1. Open **http://localhost:5173** in your browser
2. Type a query like: `Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio`
3. Click **🔬 Analyze**
4. Watch the **4-step pipeline animate** as each agent works
5. View real-time **agent activity logs** streaming in
6. See the final **advisory report** when complete

### Via the CLI (Alternative)

```bash
# Single query
python -m src.main "Analyze AAPL, MSFT, GOOGL"

# Interactive mode
python -m src.main --interactive

# JSON output (for scripting)
python -m src.main --json "Analyze AAPL"
```

### Sample Queries to Try

```
Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio
Research Tesla and Amazon stock performance
Evaluate NVDA and AMD for tech sector investment
Give me a risk analysis of META, NFLX, and DIS
Analyze Apple stock for long-term investment
```

---

## 🤖 How the Agents Work

### Agent 1: Research Coordinator (Student 1)
| Property | Details |
|----------|---------|
| **Role** | Parses your query, extracts stock tickers, fetches live market data |
| **Tool** | `MarketDataFetcher` — connects to Yahoo Finance API (free, no key needed) |
| **Data Fetched** | Current price, volume, P/E ratio, 52-week range, historical prices |
| **Constraint** | Never gives advice — only gathers data |

### Agent 2: Market Research Analyst (Student 2)
| Property | Details |
|----------|---------|
| **Role** | Analyzes financial news sentiment for each ticker |
| **Tool** | `NewsSentimentAnalyzer` — RSS feeds + VADER NLP sentiment scoring |
| **Output** | Sentiment score (-1 to +1), label (BULLISH/NEUTRAL/BEARISH), top headlines |
| **Constraint** | Never fabricates data — reports "no data" if feeds are empty |

### Agent 3: Risk Assessment Specialist (Student 3)
| Property | Details |
|----------|---------|
| **Role** | Calculates quantitative risk metrics for each ticker |
| **Tool** | `RiskCalculator` — NumPy/Pandas-based financial calculations |
| **Metrics** | Volatility, Beta, Sharpe Ratio, Value-at-Risk (95%), Max Drawdown |
| **Output** | Risk category (LOW/MEDIUM/HIGH/CRITICAL) with confidence level |

### Agent 4: Portfolio Advisor (Student 4)
| Property | Details |
|----------|---------|
| **Role** | Synthesizes all data into an investment advisory report |
| **Tool** | `ReportGenerator` — creates formatted Markdown reports |
| **Output** | Professional report with market summary, sentiment, risk, recommendations |
| **Constraint** | Must include disclaimer: "AI-generated, not financial advice" |

---

## 🧪 Testing

### Run All Tests (67 total)
```bash
source venv/bin/activate
pytest tests/ -v --tb=short
```

### Run Individual Student Tests
```bash
pytest tests/test_coordinator.py -v        # Student 1 (13 tests)
pytest tests/test_market_analyst.py -v     # Student 2 (12 tests)
pytest tests/test_risk_specialist.py -v    # Student 3 (15 tests)
pytest tests/test_portfolio_advisor.py -v  # Student 4 (14 tests)
pytest tests/test_harness.py -v            # Shared harness (13 tests)
```

### Run with Coverage Report
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### What Gets Tested

| Category | Examples |
|----------|---------|
| **Property-Based** | Value ranges, output structure, required JSON fields |
| **LLM-as-a-Judge** | Heuristic quality evaluation of report output |
| **Integration** | State management, database CRUD, observability logging |
| **Edge Cases** | Empty inputs, invalid tickers, boundary conditions |
| **Performance** | Tool execution time benchmarks |

---

## 📁 Project Structure

```
CTSE-02/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment config template
├── .gitignore
│
├── src/                                # Python Backend
│   ├── main.py                         # CLI entry point
│   ├── api.py                          # Flask REST API + SSE
│   ├── config.py                       # Centralized configuration
│   ├── agents/
│   │   ├── coordinator.py              # Student 1 — Research Coordinator
│   │   ├── market_analyst.py           # Student 2 — Market Analyst
│   │   ├── risk_specialist.py          # Student 3 — Risk Specialist
│   │   └── portfolio_advisor.py        # Student 4 — Portfolio Advisor
│   ├── tools/
│   │   ├── market_data_fetcher.py      # Student 1 — yfinance market data
│   │   ├── news_sentiment.py           # Student 2 — RSS + VADER sentiment
│   │   ├── risk_calculator.py          # Student 3 — Risk metrics engine
│   │   └── report_generator.py         # Student 4 — Markdown reports
│   ├── tasks/
│   │   └── research_tasks.py           # Sequential task pipeline
│   ├── crew/
│   │   └── research_crew.py            # CrewAI orchestration
│   ├── state/
│   │   └── models.py                   # Pydantic state models
│   ├── observability/
│   │   ├── logger.py                   # Structured JSON logger
│   │   └── callbacks.py                # CrewAI lifecycle callbacks
│   └── database/
│       └── db_manager.py               # SQLite persistence manager
│
├── frontend/                           # React Frontend (Vite)
│   ├── index.html                      # HTML entry with Google Fonts
│   ├── package.json                    # NPM dependencies
│   ├── vite.config.js                  # Vite configuration
│   └── src/
│       ├── main.jsx                    # React entry point
│       ├── App.jsx                     # Root component + SSE state
│       ├── api.js                      # API client module
│       ├── index.css                   # Dark theme design system
│       └── components/
│           ├── QueryInput.jsx          # Search bar + sample chips
│           ├── AgentPipeline.jsx       # Animated pipeline visualization
│           ├── MarketDataCard.jsx      # Market data summary card
│           ├── SentimentGauge.jsx      # Sentiment gauge widget
│           ├── RiskMatrix.jsx          # Risk assessment card
│           ├── ReportViewer.jsx        # Markdown report renderer
│           ├── LogStream.jsx           # Real-time agent log stream
│           └── SessionHistory.jsx      # Past research sessions
│
├── tests/                              # Test Suite (67 tests)
│   ├── conftest.py                     # Shared fixtures & mock data
│   ├── test_harness.py                 # Unified harness (state, DB, logs)
│   ├── test_coordinator.py             # Student 1 tests
│   ├── test_market_analyst.py          # Student 2 tests
│   ├── test_risk_specialist.py         # Student 3 tests
│   └── test_portfolio_advisor.py       # Student 4 tests
│
├── data/
│   └── sample_queries.json             # Example input queries
├── logs/                               # Execution logs (auto-generated)
└── reports/                            # Generated reports (auto-generated)
```

---

## 👥 Team Contributions

| Student | Agent | Custom Tool | Test File | Key Technology |
|---------|-------|-------------|-----------|----------------|
| **Student 1** | Coordinator | MarketDataFetcher | `test_coordinator.py` | yfinance API |
| **Student 2** | Market Analyst | NewsSentimentAnalyzer | `test_market_analyst.py` | VADER + RSS |
| **Student 3** | Risk Specialist | RiskCalculator | `test_risk_specialist.py` | NumPy/Pandas |
| **Student 4** | Portfolio Advisor | ReportGenerator | `test_portfolio_advisor.py` | Markdown |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM Engine** | Ollama (llama3:8b) | Local AI inference — zero cloud cost |
| **Agent Framework** | CrewAI | Multi-agent orchestration |
| **Backend API** | Flask + Flask-CORS | REST API with SSE streaming |
| **Frontend** | React (Vite, ES Module) | Interactive dashboard UI |
| **State Management** | Pydantic | Type-safe data validation |
| **Database** | SQLite | Session persistence + audit trail |
| **Market Data** | yfinance | Real-time stock data (free) |
| **NLP** | VADER Sentiment | Financial news sentiment scoring |
| **Risk Engine** | NumPy + Pandas | Quantitative risk calculations |
| **Testing** | pytest | 67 automated tests |
| **Observability** | Custom JSON Logger | Structured event tracing |

---

## 🔧 Troubleshooting

### "System Offline" in the dashboard
- Make sure Ollama is running: `ollama serve`
- Make sure Flask API is running: `python -m src.api`

### Port 5000 is in use (macOS)
- We use port **5001** to avoid the macOS AirPlay Receiver conflict
- If 5001 is also taken, change it in `src/api.py` and `frontend/src/api.js`

### "No module named 'src'"
- Make sure you're in the project root directory (`CTSE-02/`)
- Make sure the virtual environment is activated: `source venv/bin/activate`

### Pipeline takes too long
- The first run is slower because Ollama loads the model into memory
- Subsequent runs are faster (model stays cached)
- Using `llama3:8b` requires ~8 GB RAM. If you have less, try `llama3.2:3b`

### Tests fail with network errors
- Some tests fetch live data from Yahoo Finance — they need internet access
- Run offline-safe tests only: `pytest tests/test_harness.py tests/test_portfolio_advisor.py -v`

---

## 📝 License

This project is developed as part of the SE4010 – CTSE course at SLIIT.
