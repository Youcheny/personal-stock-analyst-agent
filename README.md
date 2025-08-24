# Value-Agent (ADK-style) — Personal Stock Research Assistant

Multi-agent scaffold for personal stock research with **AI-powered analysis**:
- Coordinator ("Value PM")
- Sector agents (tech, financials) with **LLM-enhanced insights**
- Quant/Risk agent with **intelligent risk assessment**
- SEC filings tool + Market data tool (yfinance by default; Polygon optional)
- **OpenAI integration** for intelligent financial analysis

> Personal research only. Not investment advice.

## Features

### 🤖 AI-Enhanced Analysis
- **LLM-powered sector analysis** for tech and financial companies
- **Intelligent risk assessment** based on quantitative metrics
- **Context-aware insights** using company financials and SEC filings
- **Actionable recommendations** for each checklist item

### 📊 Comprehensive Research
- Generate detailed 1-page research memos
- Run stock screening with customizable criteria
- Extract and analyze SEC filing risks
- Calculate key financial metrics (FCF Yield, ROIC, etc.)

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Generate a research memo with AI analysis
python3 src/app.py memo AAPL

# Run stock screening
python3 src/app.py screen --universe AAPL,MSFT,META,GOOGL,AMZN --min_fcf_yield 0.02 --min_roic 0.06
```

## Environment Setup

Create a `.env` file with the following variables:

```bash
# Required for LLM analysis
OPENAI_API_KEY="sk-your-openai-api-key-here"

# Required for SEC filings access
SEC_USER_AGENT="YourName/YourCompany (your.email@example.com)"

# Optional: Enhanced market data
POLYGON_API_KEY="your-polygon-api-key-here"
```

### Getting API Keys

1. **OpenAI API Key**: Sign up at [OpenAI Platform](https://platform.openai.com/api-keys)
2. **SEC User Agent**: Use your real name/company for SEC filings access
3. **Polygon API Key**: Optional, get from [Polygon.io](https://polygon.io/)

## How It Works

### 1. Data Collection
- **Market Data**: Company profiles, financial metrics via yfinance
- **SEC Filings**: Risk factors and business updates
- **Quantitative**: Price history, volatility, drawdown analysis

### 2. AI Analysis
- **Sector Specialists**: Tech and financial analysts with domain expertise
- **LLM Integration**: OpenAI-powered analysis of each checklist item
- **Context Awareness**: Uses company-specific data for tailored insights

### 3. Output Generation
- **Research Memos**: Comprehensive 1-page analysis
- **Stock Screening**: Filtered results with rejection reasons
- **Specialist Notes**: AI-enhanced insights for each sector

## Example Output

With LLM analysis enabled, you'll get insights like:

```
### Tech Analyst Checklist

**Moat: network effects / switching costs / data advantage?**
• Strong network effects through App Store ecosystem and iOS user base
• High switching costs due to data lock-in and ecosystem integration
• Data advantage from user behavior analytics and privacy controls

**Unit economics: gross margin path vs R&D/S&M intensity**
• Exceptional 46.7% gross margins with room for improvement
• R&D investment at 6.2% of revenue supports innovation pipeline
• S&M efficiency improving with digital-first customer acquisition
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Value PM      │    │  Tech Analyst   │    │ Financials     │
│  (Coordinator)  │    │  (LLM-Enhanced) │    │ Analyst        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Quant Agent    │
                    │(LLM-Enhanced)   │
                    └─────────────────┘
```

## Troubleshooting

- **LLM Analysis Unavailable**: Check your OpenAI API key in `.env`
- **SEC Access Issues**: Verify your User-Agent string format
- **Rate Limits**: LLM calls are limited to 10 per minute
- **Fallback Mode**: System gracefully degrades to basic analysis if LLM fails
