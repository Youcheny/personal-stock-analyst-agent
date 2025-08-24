from typing import Dict, Any

class TechAnalyst:
    CHECKLIST = [
        "Moat: network effects / switching costs / data advantage?",
        "Unit economics: gross margin path vs R&D/S&M intensity",
        "Durability: dependence on platform shifts (cloud, AI infra)?",
        "Customer concentration & churn (if available)",
        "SBC dilution trend",
    ]

    def __init__(self, tools):
        self.tools = tools

    def annotate(self, ticker: str) -> str:
        # Get company context for LLM analysis
        context = self._get_company_context(ticker)
        
        # Use LLM analyzer if available
        if "llm" in self.tools:
            try:
                analyses = self.tools["llm"].analyze_sector_checklist(ticker, self.CHECKLIST, context)
                return "### Tech Analyst Checklist\n\n" + "\n\n".join(analyses)
            except Exception as e:
                # Fallback to basic checklist if LLM fails
                bullets = [f"- {item}" for item in self.CHECKLIST]
                return "### Tech Analyst Checklist\n" + "\n".join(bullets) + f"\n\n⚠️ LLM analysis failed: {str(e)}"
        else:
            # Fallback to basic checklist if no LLM tool
            bullets = [f"- {item}" for item in self.CHECKLIST]
            return "### Tech Analyst Checklist\n" + "\n".join(bullets) + "\n\nℹ️ Enable LLM analysis by setting OPENAI_API_KEY"
    
    def _get_company_context(self, ticker: str) -> Dict[str, Any]:
        """Get company context for LLM analysis"""
        try:
            profile = self.tools.get("mkt", {}).company_profile(ticker) if hasattr(self.tools.get("mkt"), "company_profile") else {}
            facts = self.tools.get("mkt", {}).compute_quick_facts(ticker) if hasattr(self.tools.get("mkt"), "compute_quick_facts") else {}
            filings = self.tools.get("sec", {}).latest_filings(ticker, forms=["10-K", "10-Q"], limit=3) if hasattr(self.tools.get("sec"), "latest_filings") else []
            risks = self.tools.get("sec", {}).extract_risk_items(filings) if hasattr(self.tools.get("sec"), "extract_risk_items") else []
            
            # Get risk analysis if available
            risk_analysis = ""
            if "risk_analyzer" in self.tools:
                try:
                    risk_analysis = self.tools["risk_analyzer"].analyze_risks(ticker)
                except Exception:
                    risk_analysis = ""
            
            return {
                "profile": profile or {},
                "facts": facts or {},
                "risk_items": risks or [],
                "risk_analysis": risk_analysis
            }
        except Exception:
            return {"profile": {}, "facts": {}, "risk_items": [], "risk_analysis": ""}
