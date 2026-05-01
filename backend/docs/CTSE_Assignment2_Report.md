# SE4010 – CTSE Assignment 2: Technical Report

**Smart Financial Research & Portfolio Advisory System**

Sri Lanka Institute of Information Technology | SE4010 – Current Trends in Software Engineering | May 2026

GitHub Repository: `<your-repository-url>`

---

## 1. Problem Domain

Individual investors face a multi-step research challenge before making informed decisions. Analyzing even 3 stocks requires: (1) checking live prices and financial metrics, (2) reading and interpreting news sentiment, (3) computing quantitative risk measures, and (4) synthesizing everything into a recommendation. This process takes 3–4 hours manually and requires cross-domain expertise in finance, NLP, and statistics.

We automated this workflow using a **Multi-Agent System** in the Finance domain. Four specialized AI agents collaborate in a sequential pipeline — each an expert in one stage — to transform a natural language query like *"Analyze AAPL, MSFT, GOOGL"* into a professional advisory report in minutes. The system runs entirely locally using Ollama (llama3:8b) with zero cloud cost.

---

## 2. System Architecture

### 2.1 Multi-Agent Architecture

We use **CrewAI** to orchestrate 4 agents in a `Process.sequential` pipeline. Each agent has one custom tool built on LangChain's `BaseTool`. The LLM (Ollama) acts as each agent's reasoning engine, while tools perform deterministic actions — the **ReAct** (Reason + Act) pattern. This separation ensures financial data is never hallucinated.

```
User Query
    │
    ▼
┌───────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Coordinator  │────▶│  Market Analyst   │────▶│ Risk Specialist  │────▶│ Portfolio Advisor│
│  🔧 yfinance  │     │ 🔧 VADER + RSS   │     │ 🔧 NumPy/Pandas  │     │ 🔧 Report Gen    │
└───────┬───────┘     └────────┬─────────┘     └────────┬─────────┘     └────────┬────────┘
        ▼                      ▼                        ▼                        ▼
   Market Data          Sentiment Scores          Risk Metrics          Advisory Report
        │                      │                        │                        │
        └──────────────────────┴────────────────────────┴────────────────────────┘
                                        ▼
              ┌──────────────────────────────────────────┐
              │ Pydantic State │ SQLite DB │ JSON Logger  │
              └──────────────────────────────────────────┘
```

A **React (Vite) frontend** communicates with a **Flask REST API** (`src/api.py`) that runs the pipeline in a background thread and streams agent activity to the browser via **Server-Sent Events (SSE)**.

### 2.2 Agent Roles and Responsibilities

| Agent | Role | Responsibility | Output |
|-------|------|---------------|--------|
| **Coordinator** | Research Director | Parse queries, extract tickers, fetch live market data | JSON: tickers + market data |
| **Market Analyst** | Sentiment Specialist | Analyze financial news sentiment using NLP | JSON: sentiment scores + headlines |
| **Risk Specialist** | Quantitative Risk Analyst | Calculate volatility, beta, Sharpe, VaR, drawdown | JSON: risk metrics + risk categories |
| **Portfolio Advisor** | Investment Advisor | Synthesize all data into an advisory report | Markdown report with disclaimer |

### 2.3 Workflow

CrewAI's sequential process ensures automatic context injection: Task 1's output becomes Task 2's context, Task 2's output is appended for Task 3, etc. By Task 4, the Portfolio Advisor receives all prior data.

---

## 3. Agent Design

### 3.1 System Prompts

Each agent is configured with a **role** (job title), **goal** (specific instructions), and **backstory** (persona shaping LLM behavior):

**Agent 1 — Coordinator** (`src/agents/coordinator.py`):
- **Goal**: *"Orchestrate the financial research pipeline by parsing user queries, extracting stock ticker symbols, fetching initial market data using the Market Data Fetcher tool, and creating a structured research plan."*
- **Backstory**: *"Senior Financial Research Director with 20 years of experience managing analyst teams at top investment banks... You never provide financial advice directly — you coordinate the research team."*

**Agent 2 — Market Analyst** (`src/agents/market_analyst.py`):
- **Goal**: *"Gather comprehensive market intelligence by analyzing financial news sentiment for the requested stock tickers. Use the News Sentiment Analyzer tool to fetch recent news articles and compute sentiment scores."*
- **Backstory**: *"Quantitative Market Analyst with deep expertise in NLP-driven sentiment analysis... You never fabricate or assume data that wasn't provided by your tools."*

**Agent 3 — Risk Specialist** (`src/agents/risk_specialist.py`):
- **Goal**: *"Evaluate portfolio risk by calculating quantitative risk metrics... Categorize each ticker's risk level and provide a portfolio risk summary with confidence levels."*
- **Backstory**: *"Certified Risk Analyst (CRA) with 15 years of experience... You always provide confidence levels for your assessments and categorize risk as LOW, MEDIUM, HIGH, or CRITICAL."*

**Agent 4 — Portfolio Advisor** (`src/agents/portfolio_advisor.py`):
- **Goal**: *"Synthesize all research findings into actionable portfolio recommendations... Ensure all recommendations are based strictly on the data provided by prior agents — never hallucinate or assume data. Always include disclaimers."*
- **Backstory**: *"Chartered Financial Analyst (CFA)... You MUST include a disclaimer in every report stating that this is AI-generated analysis and does NOT constitute financial advice."*

### 3.2 Constraints and Reasoning Logic

| Constraint | Implementation | Purpose |
|-----------|---------------|---------|
| `allow_delegation=False` | Set on all 4 agents | Prevents agents from passing work; enforces pipeline |
| `temperature=0.2` | LLM parameter | Low creativity — essential for deterministic financial output |
| `max_iterations=10` | Prevents infinite loops | Agent gives up after 10 reasoning steps |
| `max_rpm=30` | Rate limiting | Prevents overwhelming the local Ollama server |
| JSON output format | Enforced in task descriptions | Ensures structured, parseable data between agents |
| Mandatory disclaimer | Embedded in Agent 4's goal AND backstory | Legal safety — report states it's AI-generated |

### 3.3 Interaction Strategy

Each task description (`src/tasks/research_tasks.py`) contains explicit INSTRUCTIONS and CONSTRAINTS:

- **Task 1** instructs the Coordinator to parse the query, call `Market Data Fetcher` for each ticker, and output a JSON with `tickers`, `research_plan`, and `market_data`.
- **Task 2** instructs the Market Analyst to extract tickers from Task 1's output, call `News Sentiment Analyzer` for each, and output `sentiment_results` + `overall_sentiment`.
- **Task 3** instructs the Risk Specialist to call `Risk Calculator` with all tickers as a comma-separated string, and output `risk_analysis` + `overall_risk_category`.
- **Task 4** instructs the Portfolio Advisor to synthesize all prior data and call `Report Generator` to produce the final Markdown report.

Each task explicitly states: *"Do NOT fabricate data. Use only data returned by the tool."*

---

## 4. Custom Tools

All tools extend `langchain.tools.BaseTool` with Pydantic input schemas for validated parameters.

### 4.1 Tool 1: MarketDataFetcher (`src/tools/market_data_fetcher.py`)

**API**: Yahoo Finance via `yfinance` library (free, no API key)  
**Input**: `ticker_symbol` (str), `period` (str, default "1mo")  
**Output**: JSON with 15+ fields — current_price, volume, pe_ratio, market_cap, 52-week range, historical_prices

**Example usage by the LLM**:
```
Action: Market Data Fetcher
Action Input: {"ticker_symbol": "AAPL", "period": "1mo"}
→ Returns: {"ticker": "AAPL", "current_price": 195.20, "volume": 55000000, "pe_ratio": 28.5, ...}
```

### 4.2 Tool 2: NewsSentimentAnalyzer (`src/tools/news_sentiment.py`)

**APIs**: Google News RSS (`feedparser`), VADER NLP (`vaderSentiment`)  
**Input**: `query` (str), `max_articles` (int, default 5)  
**Process**: Fetches RSS → cleans HTML (BeautifulSoup) → runs VADER on each headline → averages compound score → classifies as BEARISH (<-0.15) / NEUTRAL / BULLISH (>0.15)

**Example**:
```
Action: News Sentiment Analyzer
Action Input: {"query": "AAPL", "max_articles": 5}
→ Returns: {"sentiment_label": "BULLISH", "average_sentiment": 0.35, "articles_analyzed": 5, ...}
```

### 4.3 Tool 3: RiskCalculator (`src/tools/risk_calculator.py`)

**Libraries**: `numpy`, `pandas`, `yfinance`  
**Input**: `ticker_symbols` (comma-separated str), `period` ("6mo"), `risk_free_rate` (0.05)  
**Metrics computed**:

| Metric | Formula | Meaning |
|--------|---------|---------|
| Volatility | `σ = std(returns) × √252` | Annualized price variability |
| Beta | `Cov(stock, S&P500) / Var(S&P500)` | Market sensitivity |
| Sharpe Ratio | `(μ - rf) / σ` | Risk-adjusted return |
| VaR 95% | `percentile(returns, 5)` | Worst daily loss at 95% confidence |
| Max Drawdown | `max(peak − trough) / peak` | Worst historical decline |

**Risk classification**: Composite score → LOW (<0.3), MEDIUM (0.3–0.5), HIGH (0.5–0.7), CRITICAL (>0.7).

### 4.4 Tool 4: ReportGenerator (`src/tools/report_generator.py`)

**Output**: Markdown file saved to `reports/advisory_<tickers>_<timestamp>.md`  
**Sections generated**: Executive Summary, Market Analysis, Sentiment Analysis, Risk Assessment (with 🟢🟡🟠🔴 categories), Portfolio Recommendations, Disclaimer.

---

## 5. State Management

### 5.1 Global State Structure

A `ResearchState` Pydantic model (`src/state/models.py`) serves as the shared context:

```python
class ResearchState(BaseModel):
    query_id: str                              # UUID for this session
    user_query: str                            # Original user query
    tickers: List[str]                         # Extracted ticker symbols
    market_data: Optional[List[MarketData]]    # From Coordinator
    sentiment_results: Optional[List[SentimentResult]]  # From Market Analyst
    risk_metrics: Optional[List[RiskMetrics]]  # From Risk Specialist
    advisory_report: Optional[str]             # From Portfolio Advisor
    agent_logs: List[AgentLogEntry]            # Observability
    errors: List[str]                          # Error tracking
    status: str                                # initialized → in_progress → completed
```

### 5.2 How Context Passes Between Agents

CrewAI's sequential process handles context injection automatically: each task's output text is prepended to the next task's context. Additionally, the `ResearchCrew` orchestrator (`src/crew/research_crew.py`) maintains the `ResearchState` object across the pipeline, parsing each agent's JSON output and populating the typed fields. This dual mechanism (text context + structured state) ensures both the LLM and the system have complete information.

### 5.3 Persistence

All state is persisted to **SQLite** (`src/database/db_manager.py`) across 6 tables: `research_sessions`, `market_data`, `sentiment_results`, `risk_metrics`, `reports`, `agent_logs`. An **AgentObserver** (`src/observability/logger.py`) writes structured JSON-line logs to `logs/`.

---

## 6. Evaluation Methodology

### 6.1 Unified Testing Harness

We developed a unified test harness (`tests/conftest.py` + `tests/test_harness.py`) providing shared fixtures: `sample_market_data`, `sample_sentiment_result`, `sample_risk_metrics`, `sample_research_state`, and a temporary SQLite database.

### 6.2 Individual Test Contributions

Each student contributed test cases for their agent in a dedicated file:

| Student | Test File | Tests | Key Assertions |
|---------|-----------|-------|----------------|
| 1 | `test_coordinator.py` | 13 | Valid/invalid tickers, JSON structure, historical prices present, tool performance <10s, agent has MarketDataFetcher tool |
| 2 | `test_market_analyst.py` | 12 | Sentiment score in [-1,1], label ∈ {BULLISH,NEUTRAL,BEARISH}, headlines list, distribution counts, agent never fabricates data |
| 3 | `test_risk_specialist.py` | 15 | Volatility ≥ 0, beta within [-3,5], Sharpe within [-5,10], VaR negative, drawdown in [-1,0], risk categories validated, confidence in [0,1] |
| 4 | `test_portfolio_advisor.py` | 14 | Report contains all sections, disclaimer present, markdown/text format, empty data handling, ticker mentions, LLM-as-a-judge quality heuristic |

### 6.3 Testing Approaches

- **Property-Based**: Mathematical bounds (e.g., `volatility ≥ 0`, `sentiment ∈ [-1, 1]`)
- **Structure Validation**: Output is valid JSON with required fields
- **Edge Cases**: Invalid tickers, empty inputs, network failures
- **Performance Benchmarks**: Each tool responds within 10 seconds
- **LLM-as-a-Judge**: Heuristic scoring of report quality (sections present, disclaimer included)
- **Integration**: State → database → retrieve → verify match

### 6.4 Results

```
$ pytest tests/ -v --tb=short
67 passed, 3 warnings in 38.26s
```

---

## 7. Individual Student Contributions

### Student 1 — Research Coordinator + MarketDataFetcher

**Agent**: Coordinator (`src/agents/coordinator.py`) — parses user queries, extracts tickers, creates research plans.  
**Tool**: MarketDataFetcher (`src/tools/market_data_fetcher.py`) — integrates with Yahoo Finance via `yfinance` to retrieve real-time pricing, volume, P/E ratio, 52-week range, and historical prices.  
**Tests**: `tests/test_coordinator.py` — 13 tests covering valid fetches, invalid tickers, period handling, JSON structure, and agent configuration.  
**Challenge**: yfinance API returns inconsistent fields across tickers (some lack P/E ratio or dividend data). Solved by using `Optional` fields in the Pydantic model and defaulting missing values to `None`.

### Student 2 — Market Analyst + NewsSentimentAnalyzer

**Agent**: Market Research Analyst (`src/agents/market_analyst.py`) — analyzes financial news sentiment for each ticker.  
**Tool**: NewsSentimentAnalyzer (`src/tools/news_sentiment.py`) — fetches Google News RSS feeds, cleans HTML with BeautifulSoup, and runs VADER NLP sentiment analysis on each headline.  
**Tests**: `tests/test_market_analyst.py` — 12 tests covering sentiment scoring, label classification, headline extraction, and no-data handling.  
**Challenge**: Google News RSS sometimes returns HTML-encoded content in titles. Solved by adding a BeautifulSoup HTML cleaning step before sentiment analysis.

### Student 3 — Risk Specialist + RiskCalculator

**Agent**: Risk Assessment Specialist (`src/agents/risk_specialist.py`) — computes quantitative risk metrics and categorizes risk levels.  
**Tool**: RiskCalculator (`src/tools/risk_calculator.py`) — downloads 6 months of historical data via yfinance, computes 5 risk metrics using NumPy/Pandas (volatility, beta, Sharpe ratio, VaR, max drawdown), and classifies risk as LOW/MEDIUM/HIGH/CRITICAL.  
**Tests**: `tests/test_risk_specialist.py` — 15 tests covering metric ranges, composite scoring, category boundaries, multi-ticker portfolios, and edge cases.  
**Challenge**: Beta calculation requires a market benchmark (S&P 500). Some tickers have insufficient overlapping trading days with the benchmark. Solved by using `dropna()` on aligned series and falling back to `beta=1.0` when data is insufficient.

### Student 4 — Portfolio Advisor + ReportGenerator

**Agent**: Portfolio Advisor (`src/agents/portfolio_advisor.py`) — synthesizes all findings into investment recommendations with mandatory disclaimers.  
**Tool**: ReportGenerator (`src/tools/report_generator.py`) — accepts all research data as JSON, generates a structured Markdown report with 6 sections (Executive Summary, Market Analysis, Sentiment, Risk, Recommendations, Disclaimer), and saves it to disk.  
**Tests**: `tests/test_portfolio_advisor.py` — 14 tests covering section presence, disclaimer requirement, format options, empty data handling, ticker mentions, and output quality.  
**Challenge**: The LLM sometimes omitted the disclaimer section. Solved by embedding the disclaimer requirement in both the agent's `goal` AND `backstory` system prompts, plus a hard-coded fallback in the ReportGenerator tool itself.

---

## 8. Conclusion

We successfully built a locally-hosted Multi-Agent System demonstrating core Agentic AI principles: perception (NL query parsing), reasoning (LLM-driven tool selection), action (deterministic tool execution), collaboration (sequential context passing), and observability (full logging and audit trail). The system processes real financial data with zero hallucination, runs at zero cloud cost, and includes a real-time dashboard for pipeline visualization.
