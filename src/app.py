import argparse
import os
from dotenv import load_dotenv

from orchestrator import Orchestrator
from agents.research_coordinator import ResearchCoordinator
from agents.sector_tech import TechAnalyst
from agents.sector_financials import FinancialsAnalyst
from agents.risk_analyzer import RiskAnalyzer
from tools.sec_filings import SecFilings
from tools.market_data import MarketData
from tools.llm_analyzer import LLMAnalyzer

def build_orchestrator():
    load_dotenv()
    sec = SecFilings(user_agent=os.getenv("SEC_USER_AGENT", "ValueAgent/0.1 (contact@example.com)"))
    mkt = MarketData(polygon_api_key=os.getenv("POLYGON_API_KEY"))
    llm = LLMAnalyzer(api_key=os.getenv("OPENAI_API_KEY"))
    risk_analyzer = RiskAnalyzer(tools={"sec": sec, "mkt": mkt, "llm": llm})

    research_coordinator = ResearchCoordinator(tools={"sec": sec, "mkt": mkt, "llm": llm, "risk_analyzer": risk_analyzer})
    tech = TechAnalyst(tools={"sec": sec, "mkt": mkt, "llm": llm})
    fins = FinancialsAnalyst(tools={"sec": sec, "mkt": mkt, "llm": llm})

    return Orchestrator(coordinator=research_coordinator, specialists={"tech": tech, "fins": fins})

def main():
    parser = argparse.ArgumentParser(description="Value-Agent (ADK-style) CLI")
    sub = parser.add_subparsers(dest="cmd")

    memo = sub.add_parser("memo", help="Generate a 1-pager research memo")
    memo.add_argument("ticker", type=str)

    screen = sub.add_parser("screen", help="Run a simple screener")
    screen.add_argument("--min_fcf_yield", type=float, default=0.04)
    screen.add_argument("--min_roic", type=float, default=0.10)
    screen.add_argument("--universe", type=str, help="Comma-separated tickers, e.g. AAPL,MSFT,META")

    args = parser.parse_args()
    orch = build_orchestrator()

    if args.cmd == "memo":
        out_path = orch.run_research_memo(args.ticker.upper())
        print(f"Memo written to: {out_path}")
    elif args.cmd == "screen":
        universe = [s.strip() for s in args.universe.split(",")] if args.universe else None
        out_path = orch.run_screen(min_fcf_yield=args.min_fcf_yield, min_roic=args.min_roic, universe=universe)
        print(f"Screen results written to: {out_path}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
