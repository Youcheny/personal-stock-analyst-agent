# Value-Agent (ADK-style) — Personal Stock Research Assistant

Multi-agent scaffold for personal stock research with **AI-powered analysis**:
- Coordinator ("Value PM") orchestrating comprehensive analysis
- Sector agents (tech, financials) with **LLM-enhanced insights**
- **Advanced Risk Analyzer** with intelligent risk assessment
- SEC filings tool + Market data tool (yfinance by default; Polygon optional)
- **OpenAI integration** for intelligent financial analysis

> Personal research only. Not investment advice.

## 🚀 Latest Features

### 🤖 **Advanced Risk Analyzer**
- **Comprehensive risk assessment** using recent SEC filings and market data
- **Intelligent categorization** of risks by type and severity
- **Probability-impact analysis** with trend assessment
- **Actionable mitigation strategies** and monitoring recommendations

### 🧠 **Enhanced LLM Integration**
- **Context-aware analysis** using company financials, risks, and market data
- **Sector-specific insights** for tech and financial companies
- **Intelligent fallbacks** when LLM is unavailable
- **Rate-limited API calls** (10 per minute) for cost optimization

### 📊 **Streamlined Output**
- **Clean, focused analysis** without quantitative noise
- **Professional-grade memos** with executive summaries
- **Risk-adjusted insights** for investment decision making
- **Modular architecture** for easy extension

## Quickstart

```bash
# Clone and setup
git clone <your-repo-url>
cd value-agent-adk

# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OpenAI API key

# Generate a research memo with AI analysis
python3 src/app.py memo AAPL

# Run stock screening
python3 src/app.py screen --universe AAPL,MSFT,META,GOOGL,AMZN --min_fcf_yield 0.02 --min_roic 0.06

# Or use the convenience script
./run.sh memo AAPL
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

### 1. **Data Collection & Processing**
- **Market Data**: Company profiles, financial metrics via yfinance
- **SEC Filings**: Intelligent extraction of risk factors and business updates
- **Risk Documents**: Multi-source risk analysis from filings and company profiles

### 2. **AI-Powered Analysis**
- **Risk Analyzer**: Comprehensive risk assessment with LLM insights
- **Sector Specialists**: Tech and financial analysts with domain expertise
- **Context Integration**: Cross-referencing risks, financials, and market data

### 3. **Output Generation**
- **Research Memos**: Professional 1-page analysis with executive summaries
- **Risk Assessment**: Categorized risks with probability-impact analysis
- **Specialist Notes**: AI-enhanced insights for each sector

## 📋 Real Output Examples

### **Executive Risk Summary**
```
Apple Inc. (AAPL) faces a moderate overall risk profile, characterized by strong 
financial fundamentals but significant exposure to market volatility and supply 
chain disruptions. The company's reliance on a few flagship products, particularly 
the iPhone, adds to its vulnerability in a rapidly evolving technology landscape.
```

### **Top 5 Risks by Severity**
```
1. **Market Competition** - High probability, High impact  
   - Description: Intense competition from other technology firms, particularly 
     in the smartphone and personal computer markets, threatens Apple's market 
     share and pricing power.  
   - Mitigation: Continuous innovation and investment in R&D to enhance 
     product differentiation.  
   - Trend: Increasing  

2. **Supply Chain Disruptions** - Medium probability, High impact  
   - Description: Global supply chain issues, exacerbated by geopolitical 
     tensions and pandemics, could hinder production and delivery of products.  
   - Mitigation: Diversifying suppliers and increasing inventory levels to 
     buffer against disruptions.  
   - Trend: Increasing  
```

### **Tech Analyst Insights**
```
**Moat: network effects / switching costs / data advantage?**
- **Strengths**: 
  - Strong ecosystem with integrated hardware, software, and services 
    (iPhone, iPad, Mac, App Store) creates high switching costs for users.
  - High gross margin (46.7%) indicates pricing power, supported by brand 
    loyalty and premium product positioning.

- **Actionable Insights**: 
  - Leverage data advantage from user interactions to enhance services 
    and drive recurring revenue.
  - Consider strategic hedging to mitigate foreign exchange risks and 
    stabilize cash flows.
```

### **Financials Analyst Insights**
```
**Capital adequacy & liquidity**
- **Strengths**: 
  - Zero debt indicates strong capital adequacy and financial stability.
  - High gross margin (46.68%) supports liquidity and operational efficiency.

- **Concerns**: 
  - Low FCF yield (2.81%) suggests limited cash generation relative to 
    market value, potentially impacting liquidity.

- **Actionable Insights**: 
  - Focus on improving operational efficiency to boost free cash flow.
  - Consider strategic hedging to mitigate foreign exchange and interest 
    rate risks.
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Value PM      │    │  Tech Analyst   │    │ Financials     │
│  (Coordinator)  │    │  (LLM-Enhanced) │    │ Analyst        │
│                 │    │                 │    │ (LLM-Enhanced) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Risk Analyzer    │
                    │(LLM-Enhanced)   │
                    │                 │
                    └─────────────────┘
```

## 🔧 Key Components

### **Risk Analyzer**
- **Document Processing**: SEC filings, company profiles, market data
- **Risk Categorization**: Market, Operational, Financial, Regulatory, Strategic
- **LLM Integration**: Intelligent analysis with context awareness
- **Fallback Support**: Graceful degradation when LLM unavailable

### **Sector Analysts**
- **Tech Analyst**: Moat analysis, unit economics, platform shifts, customer concentration
- **Financials Analyst**: Credit discipline, capital adequacy, cycle sensitivity, regulatory risks
- **Context Integration**: Uses risk analysis and financial metrics for comprehensive insights

### **Data Tools**
- **Market Data**: yfinance integration with fallback to Polygon
- **SEC Filings**: Intelligent risk extraction and document processing
- **LLM Analyzer**: OpenAI integration with rate limiting and error handling

## 📈 Use Cases

### **Individual Investors**
- **Research Memos**: Comprehensive company analysis for investment decisions
- **Risk Assessment**: Understanding company-specific risks and mitigation strategies
- **Sector Analysis**: Deep insights into tech and financial company dynamics

### **Financial Analysts**
- **Due Diligence**: Quick risk assessment and financial health analysis
- **Comparative Analysis**: Consistent framework across multiple companies
- **Risk Monitoring**: Key metrics and trends to track

### **Portfolio Managers**
- **Screening**: Filter stocks based on financial criteria
- **Risk-Adjusted Analysis**: Understanding risk-reward profiles
- **Sector Allocation**: Informed decisions on tech vs financial exposure

## 🚨 Troubleshooting

- **LLM Analysis Unavailable**: Check your OpenAI API key in `.env`
- **SEC Access Issues**: Verify your User-Agent string format
- **Rate Limits**: LLM calls are limited to 10 per minute
- **Fallback Mode**: System gracefully degrades to basic analysis if LLM fails
- **Memory Issues**: Large documents are automatically truncated for LLM processing

## 🔮 Future Enhancements

- **Additional Sector Analysts**: Healthcare, Energy, Consumer Staples
- **Custom Risk Models**: Industry-specific risk assessment frameworks
- **Portfolio Integration**: Multi-stock analysis and correlation insights
- **Real-time Updates**: Live data feeds and alert systems
- **Export Formats**: PDF, Excel, and API endpoints

---

**Built with ❤️ for intelligent investment research**
