from typing import Dict, Any, List

class ResearchCoordinator:
    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools

    def research_brief(self, ticker: str) -> dict:
        profile = self.tools["mkt"].company_profile(ticker)
        filings = self.tools["sec"].latest_filings(ticker, forms=["10-K", "10-Q"], limit=3)
        facts = self.tools["mkt"].compute_quick_facts(ticker)
        
        # Use risk analyzer if available, otherwise fall back to basic risk extraction
        if "risk_analyzer" in self.tools:
            risk_analysis = self.tools["risk_analyzer"].analyze_risks(ticker)
        else:
            # Fallback to basic risk extraction
            risk_items = self.tools["sec"].extract_risk_items(filings)
            risk_analysis = "### Risks (from recent filings)\n" + "\n".join([f"- {r}" for r in risk_items[:5]])
        
        return {
            "profile": profile,
            "facts": facts,
            "risk_analysis": risk_analysis,
            "citations": {
                "sec": [f["url"] for f in filings],
                "prices": self.tools["mkt"].last_price_link(ticker)
            }
        }

    def compute_facts(self, ticker: str):
        return self.tools["mkt"].compute_quick_facts(ticker)

    def compile_memo(self, ticker: str, base: dict, addenda: list[str]) -> str:
        p = base.get("profile", {})
        f = base.get("facts", {})
        risk_analysis = base.get("risk_analysis", "### Risks\n- No risk analysis available")
        cites = base.get("citations", {})

        def pct(x): return f"{x:.2%}" if isinstance(x, (int, float)) else "n/a"

        memo = [
            f"# {ticker} — One‑Pager (Personal Research)",
            "",
            "## Business Overview",
            f"- Name: {p.get('longName') or p.get('name') or 'n/a'}",
            f"- Sector: {p.get('sector', 'n/a')}  |  Industry: {p.get('industry', 'n/a')}",
            f"- Summary: {(p.get('longBusinessSummary') or 'n/a')[:600]}...",
            "",
            "## Quick Facts (TTM / latest)",
            f"- FCF Yield: {pct(f.get('fcf_yield_ttm'))}",
            f"- ROIC (rough): {pct(f.get('roic_est'))}",
            f"- Debt/Equity: {f.get('debt_to_equity', 'n/a')}",
            f"- Gross Margin: {pct(f.get('gross_margin'))}  |  Op Margin: {pct(f.get('operating_margin'))}",
            "",
            risk_analysis,
            "",
            "## Specialist Notes",
            *addenda,
            "",
            "## Sources",
            f"- SEC filings: {cites.get('sec')}",
            f"- Prices/news: {cites.get('prices')}",
            "",
            "_For personal research; not investment advice._",
            "",
            "## Metrics Glossary",
            "**FCF Yield** — Free Cash Flow (Operating Cash Flow – CapEx) ÷ Market Cap. Roughly, the cash return you get on the stock price.",
            "",
            "**ROIC (Return on Invested Capital)** — After-tax operating profit ÷ (Debt + Equity – Cash). Shows how efficiently the business turns capital into profit.",
            "",
            "**Debt-to-Equity** — Total Debt ÷ Shareholders' Equity. A measure of leverage; higher values mean more debt relative to equity.",
        ]
        return "\n".join(memo)
