import os
import requests
import json
from typing import Dict, List, Optional
from .utils import rate_limited

class LLMAnalyzer:
    """LLM integration for intelligent financial analysis"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    def analyze_checklist_item(self, ticker: str, checklist_item: str, context: Dict) -> str:
        """Analyze a specific checklist item with company context"""
        
        if not self.api_key:
            return f"⚠️ LLM analysis unavailable (no API key) - {checklist_item}"
        
        prompt = self._build_analysis_prompt(ticker, checklist_item, context)
        
        try:
            response = self._call_llm(prompt)
            return response
        except Exception as e:
            return f"⚠️ LLM analysis failed - {checklist_item}: {str(e)}"
    
    def _build_analysis_prompt(self, ticker: str, checklist_item: str, context: Dict) -> str:
        """Build a comprehensive prompt for LLM analysis"""
        
        company_info = context.get("profile", {})
        financials = context.get("facts", {})
        risks = context.get("risk_items", [])
        risk_analysis = context.get("risk_analysis", "")
        
        prompt = f"""You are a senior financial analyst specializing in {checklist_item.split(':')[0].lower()} analysis.

Company: {ticker} ({company_info.get('sector', 'Unknown sector')})
Business: {company_info.get('longBusinessSummary', 'No description available')[:500]}

Key Financial Metrics:
- FCF Yield: {financials.get('fcf_yield_ttm', 'N/A')}
- ROIC (rough): {financials.get('roic_est', 'N/A')}
- Gross Margin: {financials.get('gross_margin', 'N/A')}
- Operating Margin: {financials.get('operating_margin', 'N/A')}
- Debt/Equity: {financials.get('debt_to_equity', 'N/A')}

Recent Risk Factors: {'; '.join(risks[:3]) if risks else 'None identified'}

Comprehensive Risk Analysis:
{risk_analysis[:800] if risk_analysis else 'No detailed risk analysis available'}

Analysis Request: Provide a concise, actionable analysis of "{checklist_item}" for {ticker}.

Requirements:
1. Be specific and data-driven
2. Identify key strengths and concerns
3. Provide actionable insights
4. Consider the comprehensive risk context provided
5. Keep response under 100 words
6. Use bullet points for clarity

Analysis:"""
        
        return prompt
    
    @rate_limited(10)  # Rate limit to 10 calls per minute
    def _call_llm(self, prompt: str) -> str:
        """Make API call to OpenAI"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a senior financial analyst providing concise, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.3
        }
        
        response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    def analyze_sector_checklist(self, ticker: str, checklist_items: List[str], context: Dict) -> List[str]:
        """Analyze all checklist items for a sector analyst"""
        
        analyses = []
        for item in checklist_items:
            analysis = self.analyze_checklist_item(ticker, item, context)
            analyses.append(f"**{item}**\n{analysis}")
        
        return analyses
