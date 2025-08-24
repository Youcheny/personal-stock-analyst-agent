from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import asyncio
import threading
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Import our Value Agent components
from src.orchestrator import Orchestrator
from src.agents.research_coordinator import ResearchCoordinator
from src.agents.sector_tech import TechAnalyst
from src.agents.sector_financials import FinancialsAnalyst
from src.agents.risk_analyzer import RiskAnalyzer
from src.tools.sec_filings import SecFilings
from src.tools.market_data import MarketData
from src.tools.llm_analyzer import LLMAnalyzer

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()

# Global variable to store the orchestrator
orchestrator = None

def initialize_orchestrator():
    """Initialize the Value Agent orchestrator"""
    global orchestrator
    try:
        sec = SecFilings(user_agent=os.getenv("SEC_USER_AGENT", "ValueAgent/0.1 (contact@example.com)"))
        mkt = MarketData(polygon_api_key=os.getenv("POLYGON_API_KEY"))
        llm = LLMAnalyzer(api_key=os.getenv("OPENAI_API_KEY"))
        risk_analyzer = RiskAnalyzer(tools={"sec": sec, "mkt": mkt, "llm": llm})

        research_coordinator = ResearchCoordinator(tools={"sec": sec, "mkt": mkt, "llm": llm, "risk_analyzer": risk_analyzer})
        tech = TechAnalyst(tools={"sec": sec, "mkt": mkt, "llm": llm})
        fins = FinancialsAnalyst(tools={"sec": sec, "mkt": mkt, "llm": llm})

        orchestrator = Orchestrator(coordinator=research_coordinator, specialists={"tech": tech, "fins": fins})
        print("✅ Value Agent orchestrator initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing orchestrator: {e}")
        orchestrator = None

@app.route('/')
def index():
    """Main page with stock search interface"""
    return render_template('index.html')

@app.route('/api/search_stocks')
def search_stocks():
    """Search for stocks based on query"""
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify([])
    
    # Mock stock search - in production, you'd integrate with a real stock API
    mock_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
        {"symbol": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Defensive"}
    ]
    
    # Filter stocks based on query
    filtered_stocks = [stock for stock in mock_stocks 
                      if query in stock["symbol"] or query in stock["name"].upper()]
    
    return jsonify(filtered_stocks[:5])

@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    """Get stock data and performance"""
    if not orchestrator:
        return jsonify({"error": "Value Agent not initialized"}), 500
    
    try:
        # Get basic stock info
        stock_info = {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "status": "loading"
        }
        
        return jsonify(stock_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analysis/<symbol>/<section>')
def get_analysis_section(symbol, section):
    """Get specific analysis section asynchronously"""
    if not orchestrator:
        return jsonify({"error": "Value Agent not initialized"}), 500
    
    try:
        if section == "business_overview":
            # Get business overview
            profile = orchestrator.coordinator.tools["mkt"].company_profile(symbol)
            return jsonify({
                "section": section,
                "data": {
                    "name": profile.get('longName') or profile.get('name') or 'N/A',
                    "sector": profile.get('sector', 'N/A'),
                    "industry": profile.get('industry', 'N/A'),
                    "summary": profile.get('longBusinessSummary', 'No description available')[:600] + "..." if profile.get('longBusinessSummary') else 'No description available'
                }
            })
        
        elif section == "quick_facts":
            # Get financial facts
            facts = orchestrator.coordinator.tools["mkt"].compute_quick_facts(symbol)
            return jsonify({
                "section": section,
                "data": {
                    "fcf_yield": facts.get('fcf_yield_ttm'),
                    "roic": facts.get('roic_est'),
                    "debt_to_equity": facts.get('debt_to_equity'),
                    "gross_margin": facts.get('gross_margin'),
                    "operating_margin": facts.get('operating_margin')
                }
            })
        
        elif section == "risk_analysis":
            # Get risk analysis
            risk_analysis = orchestrator.coordinator.tools["risk_analyzer"].analyze_risks(symbol)
            return jsonify({
                "section": section,
                "data": risk_analysis
            })
        
        elif section == "tech_analysis":
            # Get tech analyst insights
            tech_analysis = orchestrator.specialists["tech"].annotate(symbol)
            return jsonify({
                "section": section,
                "data": tech_analysis
            })
        
        elif section == "financials_analysis":
            # Get financials analyst insights
            financials_analysis = orchestrator.specialists["fins"].annotate(symbol)
            return jsonify({
                "section": section,
                "data": financials_analysis
            })
        
        else:
            return jsonify({"error": "Unknown section"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stock/<symbol>/performance')
def get_stock_performance(symbol):
    """Get stock performance data for charts"""
    if not orchestrator:
        return jsonify({"error": "Value Agent not initialized"}), 500
    
    try:
        # Get historical data
        df = orchestrator.coordinator.tools["mkt"].history(symbol, period_days=365)
        
        if df is None or df.empty:
            return jsonify({"error": "No performance data available"}), 404
        
        # Convert to chart-friendly format
        performance_data = []
        for date, row in df.iterrows():
            performance_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if "Volume" in row else 0
            })
        
        return jsonify({
            "symbol": symbol.upper(),
            "performance": performance_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize the orchestrator in a separate thread
    init_thread = threading.Thread(target=initialize_orchestrator)
    init_thread.start()
    
    # Wait for initialization
    init_thread.join()
    
    if orchestrator:
        print("🚀 Starting Value Agent Web Interface...")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ Failed to initialize Value Agent. Exiting.")
