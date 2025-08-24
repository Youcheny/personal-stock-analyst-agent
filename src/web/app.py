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

# Configure logging to show up in Vercel
import logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

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

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files explicitly"""
    print(f"📁 Static file request: {filename}")
    try:
        return app.send_static_file(filename)
    except Exception as e:
        print(f"❌ Error serving static file {filename}: {e}")
        return f"File not found: {filename}", 404

@app.route('/api/search_stocks')
def search_stocks():
    """Search for stocks based on query using Yahoo Finance with proper logging"""
    query = request.args.get('q', '').strip()
    app.logger.info(f"🔍 Search request received for query: '{query}'")
    
    if not query or len(query) < 1:
        app.logger.warning("❌ Empty query, returning empty results")
        return jsonify([])
    
    try:
        # Use Yahoo Finance search for real-time stock discovery
        import yfinance as yf
        app.logger.info("✅ yfinance imported successfully")
        
        stocks = []
        
        # Try direct ticker lookup first
        try:
            app.logger.info(f"🔍 Trying direct ticker lookup for: {query.upper()}")
            ticker = yf.Ticker(query.upper())
            info = ticker.info
            app.logger.info(f"📊 Ticker info received: {bool(info)}")
            
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
                    app.logger.info(f"✅ Added stock: {stock_data['symbol']} - {stock_data['name']}")
                else:
                    app.logger.warning(f"❌ Stock data incomplete: {stock_data}")
            else:
                app.logger.warning(f"❌ No ticker info found for: {query.upper()}")
        except Exception as e:
            app.logger.error(f"❌ Direct ticker lookup failed: {str(e)}")
            app.logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
            
            # Check if it's a rate limit error
            if "429" in str(e) or "Too Many Requests" in str(e):
                app.logger.warning("⚠️ Rate limit detected, falling back to hardcoded results")
                # Don't pass, continue to fallback logic
            else:
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
                        app.logger.info(f"✅ Added variation stock: {stock_data['symbol']} - {stock_data['name']}")
                        if len(stocks) >= 5:  # Limit to 5 results
                            break
            except Exception as e:
                app.logger.debug(f"Variation {variation} failed: {str(e)}")
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
                                app.logger.info(f"✅ Added pattern stock: {stock_data['symbol']} - {stock_data['name']}")
                                if len(stocks) >= 5:  # Limit to 5 results
                                    break
                    except Exception as e:
                        app.logger.debug(f"Pattern {pattern} failed: {str(e)}")
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
                                app.logger.info(f"✅ Added company name stock: {stock_data['symbol']} - {stock_data['name']}")
                                break
                    except Exception as e:
                        app.logger.debug(f"Company name {company_name} failed: {str(e)}")
                        continue
        
        # If we still don't have results, try hardcoded fallback
        if not stocks:
            app.logger.info("🔄 No yfinance results, trying hardcoded fallback")
            hardcoded_results = {
                # Major Tech Companies
                "nvda": [{"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology", "industry": "Semiconductors", "exchange": "NMS"}],
                "nvd": [{"symbol": "NVD", "name": "Graniteshares 2x Short NVDA Daily ETF", "sector": "ETF", "industry": "Leveraged ETF", "exchange": "NMS"}],
                "aapl": [{"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "industry": "Consumer Electronics", "exchange": "NMS"}],
                "msft": [{"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "goog": [{"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Content", "exchange": "NMS"}],
                "googl": [{"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "industry": "Internet Content", "exchange": "NMS"}],
                "amzn": [{"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "industry": "Internet Retail", "exchange": "NMS"}],
                "tsla": [{"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical", "industry": "Auto Manufacturers", "exchange": "NMS"}],
                "meta": [{"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "industry": "Internet Content", "exchange": "NMS"}],
                "nflx": [{"symbol": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services", "industry": "Entertainment", "exchange": "NMS"}],
                "adbe": [{"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "crm": [{"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "orcl": [{"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "intc": [{"symbol": "INTC", "name": "Intel Corporation", "sector": "Technology", "industry": "Semiconductors", "exchange": "NMS"}],
                "amd": [{"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "sector": "Technology", "industry": "Semiconductors", "exchange": "NMS"}],
                "qcom": [{"symbol": "QCOM", "name": "QUALCOMM Incorporated", "sector": "Technology", "industry": "Semiconductors", "exchange": "NMS"}],
                "avgo": [{"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology", "industry": "Semiconductors", "exchange": "NMS"}],
                "csco": [{"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology", "industry": "Communication Equipment", "exchange": "NMS"}],
                "ibm": [{"symbol": "IBM", "name": "International Business Machines", "sector": "Technology", "industry": "Information Technology Services", "exchange": "NMS"}],
                "hpq": [{"symbol": "HPQ", "name": "HP Inc.", "sector": "Technology", "industry": "Computer Hardware", "exchange": "NMS"}],
                "dell": [{"symbol": "DELL", "name": "Dell Technologies Inc.", "sector": "Technology", "industry": "Computer Hardware", "exchange": "NMS"}],
                "len": [{"symbol": "LEN", "name": "Lenovo Group Limited", "sector": "Technology", "industry": "Computer Hardware", "exchange": "NMS"}],
                "snow": [{"symbol": "SNOW", "name": "Snowflake Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "mdb": [{"symbol": "MDB", "name": "MongoDB Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "pltr": [{"symbol": "PLTR", "name": "Palantir Technologies Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "uber": [{"symbol": "UBER", "name": "Uber Technologies Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "lyft": [{"symbol": "LYFT", "name": "Lyft Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "shop": [{"symbol": "SHOP", "name": "Shopify Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "sq": [{"symbol": "SQ", "name": "Block Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "pypl": [{"symbol": "PYPL", "name": "PayPal Holdings Inc.", "sector": "Technology", "industry": "Software", "exchange": "NMS"}],
                "ma": [{"symbol": "MA", "name": "Mastercard Incorporated", "sector": "Financial Services", "industry": "Credit Services", "exchange": "NMS"}],
                "v": [{"symbol": "V", "name": "Visa Inc.", "sector": "Financial Services", "industry": "Credit Services", "exchange": "NMS"}],
                "axp": [{"symbol": "AXP", "name": "American Express Company", "sector": "Financial Services", "industry": "Credit Services", "exchange": "NMS"}],
                
                # Financial Services
                "jpm": [{"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services", "industry": "Banks", "exchange": "NMS"}],
                "bac": [{"symbol": "BAC", "name": "Bank of America Corp.", "sector": "Financial Services", "industry": "Banks", "exchange": "NMS"}],
                "wfc": [{"symbol": "WFC", "name": "Wells Fargo & Company", "sector": "Financial Services", "industry": "Banks", "exchange": "NMS"}],
                "gs": [{"symbol": "GS", "name": "Goldman Sachs Group Inc.", "sector": "Financial Services", "industry": "Capital Markets", "exchange": "NMS"}],
                "ms": [{"symbol": "MS", "name": "Morgan Stanley", "sector": "Financial Services", "industry": "Capital Markets", "exchange": "NMS"}],
                "c": [{"symbol": "C", "name": "Citigroup Inc.", "sector": "Financial Services", "industry": "Banks", "exchange": "NMS"}],
                "usb": [{"symbol": "USB", "name": "U.S. Bancorp", "sector": "Financial Services", "industry": "Banks", "exchange": "NMS"}],
                "pnc": [{"symbol": "PNC", "name": "PNC Financial Services Group", "sector": "Financial Services", "industry": "Banks", "exchange": "NMS"}],
                "tru": [{"symbol": "TRU", "name": "TransUnion", "sector": "Financial Services", "industry": "Specialty Business Services", "exchange": "NMS"}],
                "cof": [{"symbol": "COF", "name": "Capital One Financial Corp.", "sector": "Financial Services", "industry": "Credit Services", "exchange": "NMS"}],
                "dfs": [{"symbol": "DFS", "name": "Discover Financial Services", "sector": "Financial Services", "industry": "Credit Services", "exchange": "NMS"}],
                
                # Consumer Companies
                "aa": [{"symbol": "AA", "name": "Alcoa Corporation", "sector": "Basic Materials", "industry": "Aluminum", "exchange": "NMS"}],
                "wmt": [{"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive", "industry": "Discount Stores", "exchange": "NMS"}],
                "ko": [{"symbol": "KO", "name": "The Coca-Cola Company", "sector": "Consumer Defensive", "industry": "Beverages", "exchange": "NMS"}],
                "hd": [{"symbol": "HD", "name": "The Home Depot Inc.", "sector": "Consumer Cyclical", "industry": "Home Improvement Retail", "exchange": "NMS"}],
                "pg": [{"symbol": "PG", "name": "Procter & Gamble Company", "sector": "Consumer Defensive", "industry": "Household & Personal Products", "exchange": "NMS"}],
                "pep": [{"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Defensive", "industry": "Beverages", "exchange": "NMS"}],
                "mcd": [{"symbol": "MCD", "name": "McDonald's Corporation", "sector": "Consumer Cyclical", "industry": "Restaurants", "exchange": "NMS"}],
                "sbux": [{"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "Consumer Cyclical", "industry": "Restaurants", "exchange": "NMS"}],
                "nke": [{"symbol": "NKE", "name": "NIKE Inc.", "sector": "Consumer Cyclical", "industry": "Footwear & Accessories", "exchange": "NMS"}],
                "dis": [{"symbol": "DIS", "name": "Walt Disney Company", "sector": "Communication Services", "industry": "Entertainment", "exchange": "NMS"}],
                "cmcsa": [{"symbol": "CMCSA", "name": "Comcast Corporation", "sector": "Communication Services", "industry": "Telecom Services", "exchange": "NMS"}],
                "t": [{"symbol": "T", "name": "AT&T Inc.", "sector": "Communication Services", "industry": "Telecom Services", "exchange": "NMS"}],
                "vz": [{"symbol": "VZ", "name": "Verizon Communications Inc.", "sector": "Communication Services", "industry": "Telecom Services", "exchange": "NMS"}],
                
                # Healthcare & Pharmaceuticals
                "jnj": [{"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "industry": "Drug Manufacturers", "exchange": "NMS"}],
                "pfe": [{"symbol": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare", "industry": "Drug Manufacturers", "exchange": "NMS"}],
                "unh": [{"symbol": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare", "industry": "Healthcare Plans", "exchange": "NMS"}],
                "abbv": [{"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare", "industry": "Drug Manufacturers", "exchange": "NMS"}],
                "mrk": [{"symbol": "MRK", "name": "Merck & Co. Inc.", "sector": "Healthcare", "industry": "Drug Manufacturers", "exchange": "NMS"}],
                "abt": [{"symbol": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare", "industry": "Medical Devices", "exchange": "NMS"}],
                "tmo": [{"symbol": "TMO", "name": "Thermo Fisher Scientific Inc.", "sector": "Healthcare", "industry": "Medical Devices", "exchange": "NMS"}],
                "dhr": [{"symbol": "DHR", "name": "Danaher Corporation", "sector": "Healthcare", "industry": "Medical Devices", "exchange": "NMS"}],
                "lly": [{"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare", "industry": "Drug Manufacturers", "exchange": "NMS"}],
                "bmy": [{"symbol": "BMY", "name": "Bristol-Myers Squibb Company", "sector": "Healthcare", "industry": "Drug Manufacturers", "exchange": "NMS"}],
                "amgn": [{"symbol": "AMGN", "name": "Amgen Inc.", "sector": "Healthcare", "industry": "Biotechnology", "exchange": "NMS"}],
                "gild": [{"symbol": "GILD", "name": "Gilead Sciences Inc.", "sector": "Healthcare", "industry": "Biotechnology", "exchange": "NMS"}],
                "regn": [{"symbol": "REGN", "name": "Regeneron Pharmaceuticals Inc.", "sector": "Healthcare", "industry": "Biotechnology", "exchange": "NMS"}],
                
                # ETFs
                "spy": [{"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "qqq": [{"symbol": "QQQ", "name": "Invesco QQQ Trust", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "vti": [{"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "voo": [{"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "iwm": [{"symbol": "IWM", "name": "iShares Russell 2000 ETF", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "dia": [{"symbol": "DIA", "name": "SPDR Dow Jones Industrial Average ETF", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "schb": [{"symbol": "SCHB", "name": "Schwab U.S. Broad Market ETF", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                "schx": [{"symbol": "SCHX", "name": "Schwab U.S. Large-Cap ETF", "sector": "ETF", "industry": "ETF", "exchange": "NMS"}],
                
                # Energy & Industrial
                "xom": [{"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy", "industry": "Oil & Gas Integrated", "exchange": "NMS"}],
                "cvx": [{"symbol": "CVX", "name": "Chevron Corporation", "sector": "Energy", "industry": "Oil & Gas Integrated", "exchange": "NMS"}],
                "cop": [{"symbol": "COP", "name": "ConocoPhillips", "sector": "Energy", "industry": "Oil & Gas E&P", "exchange": "NMS"}],
                "eog": [{"symbol": "EOG", "name": "EOG Resources Inc.", "sector": "Energy", "industry": "Oil & Gas E&P", "exchange": "NMS"}],
                "ba": [{"symbol": "BA", "name": "Boeing Company", "sector": "Industrials", "industry": "Aerospace & Defense", "exchange": "NMS"}],
                "cat": [{"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "Industrials", "industry": "Farm & Heavy Construction Machinery", "exchange": "NMS"}],
                "ge": [{"symbol": "GE", "name": "General Electric Company", "sector": "Industrials", "industry": "Specialty Industrial Machinery", "exchange": "NMS"}],
                "hon": [{"symbol": "HON", "name": "Honeywell International Inc.", "sector": "Industrials", "industry": "Specialty Industrial Machinery", "exchange": "NMS"}],
                "mmc": [{"symbol": "MMC", "name": "Marsh & McLennan Companies Inc.", "sector": "Financial Services", "industry": "Insurance Brokers", "exchange": "NMS"}],
                "ajg": [{"symbol": "AJG", "name": "Arthur J. Gallagher & Co.", "sector": "Financial Services", "industry": "Insurance Brokers", "exchange": "NMS"}],
                
                # Real Estate & Utilities
                "eqr": [{"symbol": "EQR", "name": "Equity Residential", "sector": "Real Estate", "industry": "REIT - Residential", "exchange": "NMS"}],
                "pld": [{"symbol": "PLD", "name": "Prologis Inc.", "sector": "Real Estate", "industry": "REIT - Industrial", "exchange": "NMS"}],
                "duk": [{"symbol": "DUK", "name": "Duke Energy Corporation", "sector": "Utilities", "industry": "Utilities - Regulated Electric", "exchange": "NMS"}],
                "nee": [{"symbol": "NEE", "name": "NextEra Energy Inc.", "sector": "Utilities", "industry": "Utilities - Regulated Electric", "exchange": "NMS"}],
                "so": [{"symbol": "SO", "name": "Southern Company", "sector": "Utilities", "industry": "Utilities - Regulated Electric", "exchange": "NMS"}],
                
                # Additional Popular Stocks
                "cost": [{"symbol": "COST", "name": "Costco Wholesale Corporation", "sector": "Consumer Defensive", "industry": "Discount Stores", "exchange": "NMS"}],
                "tgt": [{"symbol": "TGT", "name": "Target Corporation", "sector": "Consumer Defensive", "industry": "Discount Stores", "exchange": "NMS"}],
                "lmt": [{"symbol": "LMT", "name": "Lockheed Martin Corporation", "sector": "Industrials", "industry": "Aerospace & Defense", "exchange": "NMS"}],
                "rtx": [{"symbol": "RTX", "name": "Raytheon Technologies Corporation", "sector": "Industrials", "industry": "Aerospace & Defense", "exchange": "NMS"}],
                "de": [{"symbol": "DE", "name": "Deere & Company", "sector": "Industrials", "industry": "Farm & Heavy Construction Machinery", "exchange": "NMS"}],
                "unp": [{"symbol": "UNP", "name": "Union Pacific Corporation", "sector": "Industrials", "industry": "Railroads", "exchange": "NMS"}],
                "ups": [{"symbol": "UPS", "name": "United Parcel Service Inc.", "sector": "Industrials", "industry": "Integrated Freight & Logistics", "exchange": "NMS"}],
                "fedex": [{"symbol": "FDX", "name": "FedEx Corporation", "sector": "Industrials", "industry": "Integrated Freight & Logistics", "exchange": "NMS"}],
                "fdx": [{"symbol": "FDX", "name": "FedEx Corporation", "sector": "Industrials", "industry": "Integrated Freight & Logistics", "exchange": "NMS"}]
            }
            
            query_lower = query.lower()
            
            # First, try exact matches
            for key, results in hardcoded_results.items():
                if query_lower == key:
                    stocks.extend(results)
                    app.logger.info(f"✅ Added hardcoded exact match: {results}")
                    break
            
            # If no exact match, try partial matches
            if not stocks:
                for key, results in hardcoded_results.items():
                    if query_lower in key or key.startswith(query_lower):
                        stocks.extend(results)
                        app.logger.info(f"✅ Added hardcoded partial match: {results}")
                        if len(stocks) >= 5:  # Limit results
                            break
            
            # If still no results, try some variations
            if not stocks and len(query) >= 2:
                variations = [query.upper() + "A", query.upper() + "1", query.upper() + "2"]
                for var in variations:
                    if var in hardcoded_results:
                        stocks.extend(hardcoded_results[var])
                        app.logger.info(f"✅ Added hardcoded variation: {hardcoded_results[var]}")
                        if len(stocks) >= 5:
                            break
        
        app.logger.info(f"🎯 Final search results: {len(stocks)} stocks found")
        for i, stock in enumerate(stocks):
            app.logger.info(f"  {i+1}. {stock['symbol']} - {stock['name']}")
        
        # Debug: log the exact data being returned
        app.logger.info(f"🔍 Returning JSON data: {stocks}")
        app.logger.info(f"🔍 JSON data type: {type(stocks)}")
        app.logger.info(f"🔍 JSON data length: {len(stocks)}")
        
        response = jsonify(stocks)
        app.logger.info(f"🔍 Response object created successfully")
        
        return response
        
    except Exception as e:
        app.logger.error(f"❌ Error in stock search: {e}")
        app.logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        app.logger.error(f"❌ Traceback: {traceback.format_exc()}")
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
