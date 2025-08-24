from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
import requests # Added for explicit token limits

class RiskAnalyzer:
    """Advanced risk analysis agent using LLM for comprehensive risk assessment"""
    
    def __init__(self, tools):
        self.tools = tools
        self.risk_categories = {
            "market_risk": ["market", "volatility", "economic", "macroeconomic", "cyclical"],
            "operational_risk": ["operational", "supply chain", "production", "manufacturing", "logistics"],
            "financial_risk": ["financial", "liquidity", "credit", "debt", "interest rate", "foreign exchange"],
            "regulatory_risk": ["regulatory", "compliance", "legal", "antitrust", "privacy", "environmental"],
            "strategic_risk": ["strategic", "competitive", "technology", "innovation", "market share"],
            "reputation_risk": ["reputation", "brand", "cybersecurity", "data breach", "social media"]
        }

    def analyze_risks(self, ticker: str) -> str:
        """Comprehensive risk analysis using recent documents and LLM insights"""
        
        # Get company context and risk documents
        context = self._get_company_context(ticker)
        risk_documents = self._get_recent_risk_documents(ticker)
        
        if not risk_documents:
            return "### Risk Analysis\n⚠️ No recent risk documents available for analysis."
        
        # Use LLM analyzer if available
        if "llm" in self.tools:
            try:
                return self._generate_llm_risk_analysis(ticker, context, risk_documents)
            except Exception as e:
                return self._generate_fallback_risk_analysis(ticker, context, risk_documents, str(e))
        else:
            return self._generate_fallback_risk_analysis(ticker, context, risk_documents, "LLM not available")
    
    def _get_company_context(self, ticker: str) -> Dict[str, Any]:
        """Get comprehensive company context for risk analysis"""
        try:
            profile = self.tools.get("mkt", {}).company_profile(ticker) if hasattr(self.tools.get("mkt"), "company_profile") else {}
            facts = self.tools.get("mkt", {}).compute_quick_facts(ticker) if hasattr(self.tools.get("mkt"), "compute_quick_facts") else {}
            
            return {
                "profile": profile or {},
                "facts": facts or {},
                "ticker": ticker,
                "analysis_date": datetime.now().strftime("%Y-%m-%d")
            }
        except Exception:
            return {"profile": {}, "facts": {}, "ticker": ticker, "analysis_date": datetime.now().strftime("%Y-%m-%d")}
    
    def _get_recent_risk_documents(self, ticker: str) -> List[Dict[str, Any]]:
        """Get recent risk-related documents from multiple sources"""
        risk_docs = []
        
        try:
            # Get SEC filings
            if hasattr(self.tools.get("sec"), "latest_filings"):
                filings = self.tools["sec"].latest_filings(ticker, forms=["10-K", "10-Q", "8-K"], limit=5)
                for filing in filings:
                    risk_docs.append({
                        "source": "SEC",
                        "type": filing["form"],
                        "date": filing["date"],
                        "url": filing["url"],
                        "content": self._extract_risk_content(filing["url"])
                    })
            
            # Get market data risks
            if hasattr(self.tools.get("mkt"), "company_profile"):
                profile = self.tools["mkt"].company_profile(ticker)
                if profile:
                    risk_docs.append({
                        "source": "Market Data",
                        "type": "Company Profile",
                        "date": "Current",
                        "url": "N/A",
                        "content": self._extract_profile_risks(profile)
                    })
            
        except Exception as e:
            print(f"Warning: Error fetching risk documents: {e}")
        
        return risk_docs
    
    def _extract_risk_content(self, url: str) -> str:
        """Extract risk-related content from document URL"""
        try:
            if hasattr(self.tools.get("sec"), "_get"):
                response = self.tools["sec"]._get(url)
                if "text/html" in response.headers.get("content-type", ""):
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, "html.parser")
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text()
                    
                    # Extract risk-related sections
                    risk_sections = []
                    lines = text.split('\n')
                    in_risk_section = False
                    
                    for line in lines:
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in ["risk", "uncertainty", "challenge", "threat"]):
                            in_risk_section = True
                            risk_sections.append(line.strip())
                        elif in_risk_section and line.strip():
                            if len(line.strip()) > 10:  # Meaningful content
                                risk_sections.append(line.strip())
                            if len(risk_sections) > 20:  # Limit section size
                                break
                    
                    return '\n'.join(risk_sections[:20])  # Return first 20 lines
                else:
                    return response.text[:1000]  # Return first 1000 chars for non-HTML
        except Exception:
            return "Content extraction failed"
        
        return "No content available"
    
    def _extract_profile_risks(self, profile: Dict[str, Any]) -> str:
        """Extract risk-related information from company profile"""
        risk_info = []
        
        # Extract business summary for risk analysis
        if profile.get("longBusinessSummary"):
            summary = profile["longBusinessSummary"]
            # Look for risk indicators in business summary
            risk_keywords = ["risk", "challenge", "uncertainty", "volatility", "competition"]
            sentences = summary.split('.')
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in risk_keywords):
                    risk_info.append(sentence.strip())
        
        return '. '.join(risk_info[:5]) if risk_info else "No specific risk information in profile"
    
    def _generate_llm_risk_analysis(self, ticker: str, context: Dict[str, Any], risk_documents: List[Dict[str, Any]]) -> str:
        """Generate comprehensive risk analysis using LLM"""
        
        # Prepare risk document summaries
        doc_summaries = []
        for i, doc in enumerate(risk_documents[:3], 1):  # Limit to 3 most recent
            doc_summaries.append(f"Document {i} ({doc['source']} - {doc['date']}): {doc['content'][:300]}...")
        
        # Build comprehensive prompt
        prompt = self._build_risk_analysis_prompt(ticker, context, doc_summaries)
        
        # Get LLM analysis with explicit token limits
        try:
            # Use the LLM tool's _call_llm method with custom parameters
            headers = {
                "Authorization": f"Bearer {self.tools['llm'].api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.tools["llm"].model,
                "messages": [
                    {"role": "system", "content": "You are a senior risk analyst providing comprehensive risk assessment."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 600,  # Increased token limit for risk analysis
                "temperature": 0.2   # Lower temperature for more focused analysis
            }
            
            response = requests.post(self.tools["llm"].base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            analysis = result["choices"][0]["message"]["content"].strip()
            
            return f"### Risk Analysis\n\n{analysis}"
            
        except Exception as e:
            # Fallback to basic risk extraction if LLM fails
            return self._generate_fallback_risk_analysis(ticker, context, risk_documents, str(e))
    
    def _build_risk_analysis_prompt(self, ticker: str, context: Dict[str, Any], doc_summaries: List[str]) -> str:
        """Build sophisticated prompt for risk analysis"""
        
        company_info = context.get("profile", {})
        financials = context.get("facts", {})
        
        prompt = f"""You are a senior risk analyst. Analyze risks for {ticker} ({company_info.get('sector', 'Unknown sector')}).

BUSINESS: {company_info.get('longBusinessSummary', 'No description')[:300]}

FINANCIALS: FCF Yield: {financials.get('fcf_yield_ttm', 'N/A')}, ROIC: {financials.get('roic_est', 'N/A')}, Gross Margin: {financials.get('gross_margin', 'N/A')}, Debt/Equity: {financials.get('debt_to_equity', 'N/A')}

RECENT DOCUMENTS:
{chr(10).join(doc_summaries[:2])}

ANALYZE AND PROVIDE:

## Executive Risk Summary
[2 sentences on overall risk profile]

## Top 5 Risks by Severity
1. **[Risk Name]** - [High/Medium/Low] probability, [High/Medium/Low] impact
   - Description: [1 sentence]
   - Mitigation: [1 sentence]
   - Trend: [Increasing/Stable/Decreasing]

2. **[Risk Name]** - [High/Medium/Low] probability, [High/Medium/Low] impact
   - Description: [1 sentence]
   - Mitigation: [1 sentence]
   - Trend: [Increasing/Stable/Decreasing]

[Continue for top 5 risks...]

## Risk Monitoring
- Key metrics to watch: [3-4 specific indicators]
- Investment considerations: [2-3 sentences]

Keep total response under 400 words. Focus on most material risks."""

        return prompt
    
    def _generate_fallback_risk_analysis(self, ticker: str, context: Dict[str, Any], risk_documents: List[Dict[str, Any]], error_msg: str) -> str:
        """Generate fallback risk analysis when LLM is unavailable"""
        
        analysis = [
            "### Risk Analysis",
            "",
            f"⚠️ **LLM Analysis Unavailable**: {error_msg}",
            "",
            "**Fallback Analysis Based on Available Data:**",
            ""
        ]
        
        if risk_documents:
            analysis.append("**Recent Risk Documents Analyzed:**")
            for i, doc in enumerate(risk_documents[:3], 1):
                analysis.append(f"{i}. **{doc['source']} - {doc['type']}** ({doc['date']})")
                analysis.append(f"   Content: {doc['content'][:200]}...")
                analysis.append("")
        else:
            analysis.append("No recent risk documents available for analysis.")
        
        # Add basic risk assessment based on financial metrics
        financials = context.get("facts", {})
        if financials:
            analysis.append("**Financial Risk Indicators:**")
            if financials.get("debt_to_equity"):
                analysis.append(f"- Debt/Equity: {financials['debt_to_equity']} (Higher values indicate more leverage risk)")
            if financials.get("fcf_yield_ttm"):
                analysis.append(f"- FCF Yield: {financials['fcf_yield_ttm']:.2%} (Lower values may indicate cash flow risk)")
            if financials.get("roic_est"):
                analysis.append(f"- ROIC: {financials['roic_est']:.2%} (Lower values may indicate capital efficiency risk)")
        
        analysis.append("")
        analysis.append("ℹ️ **Enable LLM Analysis**: Set OPENAI_API_KEY in .env file for comprehensive risk assessment.")
        
        return "\n".join(analysis)
