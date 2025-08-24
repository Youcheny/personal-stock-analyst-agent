from flask import Flask, render_template, request, jsonify
import os
from flask_cors import CORS
import asyncio
import threading
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Import our Value Agent components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.orchestrator import Orchestrator
from src.agents.research_coordinator import ResearchCoordinator
from src.agents.sector_tech import TechAnalyst
from src.agents.sector_financials import FinancialsAnalyst
from src.agents.risk_analyzer import RiskAnalyzer
from src.tools.sec_filings import SecFilings
from src.tools.market_data import MarketData
from src.tools.llm_analyzer import LLMAnalyzer

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
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
    """Search for stocks based on query using Yahoo Finance"""
    query = request.args.get('q', '').strip()
    print(f"🔍 Search request received for query: '{query}'")
    
    if not query or len(query) < 1:
        print("❌ Empty query, returning empty results")
        return jsonify([])
    
    try:
        # Use Yahoo Finance search for real-time stock discovery
        import yfinance as yf
        print("✅ yfinance imported successfully")
        
        stocks = []
        
        # Try direct ticker lookup first
        try:
            print(f"🔍 Trying direct ticker lookup for: {query.upper()}")
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            print(f"📊 Ticker info received: {bool(info)}")
            
            if info and info.get('symbol'):
                stock_data = {
                    "symbol": info.get('symbol', ''),
                    "name": info.get('longName') or info.get('shortName') or info.get('name', ''),
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "exchange": info.get('exchange', 'N/A')
                }
                
                if stock_data["symbol"] and stock_data["name"]:
                    stocks.append(stock_data)
                    print(f"✅ Added stock: {stock_data['symbol']} - {stock_data['name']}")
                else:
                    print(f"❌ Stock data incomplete: {stock_data}")
            else:
                print(f"❌ No ticker info found for: {query.upper()}")
        except Exception as e:
            print(f"❌ Direct ticker lookup failed: {str(e)}")
            pass
        
        # Try common ticker variations
        variations = [
            query.upper() + "A",
            query.upper() + "B",
            query.upper() + "1", 
            query.upper() + "2",
            query.upper() + "3",
            query.upper() + "4",
            query.upper() + "5"
        ]
        
        for variation in variations:
            try:
                ticker = yf.Ticker(variation)
                info = ticker.info
                if info and info.get('symbol'):
                    stock_data = {
                        "symbol": info.get('symbol', ''),
                        "name": info.get('longName') or info.get('shortName') or info.get('name', ''),
                        "sector": info.get('sector', 'N/A'),
                        "industry": info.get('industry', 'N/A'),
                        "exchange": info.get('exchange', 'N/A')
                    }
                    
                    if stock_data["symbol"] and stock_data["name"]:
                        stocks.append(stock_data)
                        if len(stocks) >= 5:  # Limit to 5 results
                            break
            except:
                continue
        
        # If we still don't have results, try some common stock patterns
        if not stocks and len(query) >= 2:
            common_patterns = [
                "SPY", "QQQ", "IWM", "VTI", "VOO",  # ETFs
                "AAPL", "MSFT", "GOOGL", "AMZN", "META",  # Tech
                "JPM", "BAC", "WFC", "GS", "MS",  # Financials
                "JNJ", "PFE", "UNH", "ABBV", "MRK",  # Healthcare
                "PG", "KO", "PEP", "WMT", "HD",  # Consumer
                "TSLA", "NVDA", "NFLX", "CRM", "ADBE",  # More Tech
                "UNH", "ABT", "TMO", "DHR", "LLY",  # More Healthcare
                "MA", "V", "AXP", "COF", "DFS"  # More Financials
            ]
            
            for pattern in common_patterns:
                if query.upper() in pattern or pattern.startswith(query.upper()):
                    try:
                        ticker = yf.Ticker(pattern)
                        info = ticker.info
                        if info and info.get('symbol'):
                            stock_data = {
                                "symbol": info.get('symbol', ''),
                                "name": info.get('longName') or info.get('shortName') or info.get('name', ''),
                                "sector": info.get('sector', 'N/A'),
                                "industry": info.get('industry', 'N/A'),
                                "exchange": info.get('exchange', 'N/A')
                            }
                            
                            if stock_data["symbol"] and stock_data["name"]:
                                stocks.append(stock_data)
                                if len(stocks) >= 5:  # Limit to 5 results
                                    break
                    except:
                        continue
        
        # Final fallback: try to find stocks by partial company name match
        if not stocks and len(query) >= 3:
            # Try some known company name patterns
            company_patterns = {
                "COCA": "KO",  # Coca-Cola
                "COKE": "KO",  # Coca-Cola
                "APPLE": "AAPL",  # Apple
                "MICROSOFT": "MSFT",  # Microsoft
                "GOOGLE": "GOOGL",  # Google
                "AMAZON": "AMZN",  # Amazon
                "TESLA": "TSLA",  # Tesla
                "NVIDIA": "NVDA",  # NVIDIA
                "NETFLIX": "NFLX",  # Netflix
                "JOHNSON": "JNJ",  # Johnson & Johnson
                "PFIZER": "PFE",  # Pfizer
                "WALMART": "WMT",  # Walmart
                "HOME": "HD",  # Home Depot
                "BANK": "JPM",  # JPMorgan
                "CHASE": "JPM",  # JPMorgan Chase
                "GOLDMAN": "GS",  # Goldman Sachs
                "MORGAN": "MS",  # Morgan Stanley
            }
            
            for company_name, ticker_symbol in company_patterns.items():
                if query.upper() in company_name:
                    try:
                        ticker = yf.Ticker(ticker_symbol)
                        info = ticker.info
                        if info and info.get('symbol'):
                            stock_data = {
                                "symbol": info.get('symbol', ''),
                                "name": info.get('longName') or info.get('shortName') or info.get('name', ''),
                                "sector": info.get('sector', 'N/A'),
                                "industry": info.get('industry', 'N/A'),
                                "exchange": info.get('exchange', 'N/A')
                            }
                            
                            if stock_data["symbol"] and stock_data["name"]:
                                stocks.append(stock_data)
                                break
                    except:
                        continue
        
        print(f"🎯 Final search results: {len(stocks)} stocks found")
        for i, stock in enumerate(stocks):
            print(f"  {i+1}. {stock['symbol']} - {stock['name']}")
        
        return jsonify(stocks)
        
    except Exception as e:
        print(f"❌ Error in stock search: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to basic search if Yahoo Finance fails
        return jsonify([])

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
                    "summary": profile.get('longBusinessSummary', 'No description available')
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
            risk_analysis = orchestrator.coordinator.tools["risk_analyzer"].analyze_risks_web(symbol)
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

@app.route('/api/stock/<symbol>/price')
def get_stock_price(symbol):
    """Get current stock price and change"""
    if not orchestrator:
        return jsonify({"error": "Value Agent not initialized"}), 500
    
    try:
        # Get current price data
        profile = orchestrator.coordinator.tools["mkt"].company_profile(symbol)
        
        if not profile:
            return jsonify({"error": "Stock not found"}), 404
        
        # Extract price data
        current_price = profile.get('currentPrice')
        previous_close = profile.get('previousClose')
        
        if current_price is None or previous_close is None:
            return jsonify({"error": "Price data not available"}), 404
        
        # Calculate change and percentage
        price_change = current_price - previous_close
        price_change_percent = (price_change / previous_close) * 100
        
        # Determine change direction and styling
        change_direction = "positive" if price_change >= 0 else "negative"
        
        return jsonify({
            "symbol": symbol.upper(),
            "current_price": current_price,
            "previous_close": previous_close,
            "change": price_change,
            "change_percent": price_change_percent,
            "change_direction": change_direction
        })
            
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

# Initialize the orchestrator for Vercel deployment
try:
    initialize_orchestrator()
    if orchestrator:
        print("✅ Value Agent orchestrator initialized successfully for Vercel")
    else:
        print("❌ Failed to initialize Value Agent for Vercel")
except Exception as e:
    print(f"❌ Error initializing orchestrator for Vercel: {e}")

if __name__ == '__main__':
    # Initialize the orchestrator in a separate thread for local development
    init_thread = threading.Thread(target=initialize_orchestrator)
    init_thread.start()
    
    # Wait for initialization
    init_thread.join()
    
    if orchestrator:
        print("🚀 Starting Value Agent Web Interface...")
        app.run(debug=True, host='0.0.0.0', port=5001)
    else:
        print("❌ Failed to initialize Value Agent. Exiting.")
