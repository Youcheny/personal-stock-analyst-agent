from typing import Dict, Any

class QuantAgent:
    def __init__(self, tools):
        self.tools = tools

    def annotate(self, ticker: str) -> str:
        # Get quantitative metrics
        df = self.tools["mkt"].history(ticker, period_days=365)
        if df is None or df.empty:
            return "### Quant Note\n- Not enough price history."
        
        ret = df["Close"].pct_change().dropna()
        vol = self.tools["quant"].annualized_vol(ret)
        dd = self.tools["quant"].max_drawdown(df["Close"])
        
        # Get company context for LLM analysis
        context = self._get_company_context(ticker)
        context["quant_metrics"] = {
            "volatility": vol,
            "max_drawdown": dd,
            "price_range": f"${df['Close'].min().iloc[0]:.2f} - ${df['Close'].max().iloc[0]:.2f}",
            "total_return": f"{((df['Close'].iloc[-1].iloc[0] / df['Close'].iloc[0].iloc[0]) - 1) * 100:.2f}%"
        }
        
        # Use LLM analyzer if available
        if "llm" in self.tools:
            try:
                analysis = self._get_quant_analysis(ticker, context)
                return f"### Quant Note\n- Annualized Vol: {vol:.2%}\n- Max Drawdown (1y lookback): {dd:.2%}\n\n**LLM Risk Assessment:**\n{analysis}"
            except Exception as e:
                # Fallback to basic metrics if LLM fails
                return f"### Quant Note\n- Annualized Vol: {vol:.2%}\n- Max Drawdown (1y lookback): {dd:.2%}\n\n⚠️ LLM analysis failed: {str(e)}"
        else:
            # Fallback to basic metrics if no LLM tool
            return f"### Quant Note\n- Annualized Vol: {vol:.2%}\n- Max Drawdown (1y lookback): {dd:.2%}\n\nℹ️ Enable LLM analysis by setting OPENAI_API_KEY"
    
    def _get_quant_analysis(self, ticker: str, context: Dict[str, Any]) -> str:
        """Get LLM analysis of quantitative metrics"""
        
        prompt = f"""You are a quantitative risk analyst. Analyze the following metrics for {ticker}:

Company: {ticker} ({context.get('profile', {}).get('sector', 'Unknown sector')})
Business: {context.get('profile', {}).get('longBusinessSummary', 'No description available')[:300]}

Quantitative Metrics:
- Volatility: {context.get('quant_metrics', {}).get('volatility', 'N/A'):.2%}
- Max Drawdown: {context.get('quant_metrics', {}).get('max_drawdown', 'N/A'):.2%}
- Price Range: {context.get('quant_metrics', {}).get('price_range', 'N/A')}
- Total Return: {context.get('quant_metrics', {}).get('total_return', 'N/A')}

Financial Health:
- FCF Yield: {context.get('facts', {}).get('fcf_yield_ttm', 'N/A')}
- ROIC: {context.get('facts', {}).get('roic_est', 'N/A')}
- Debt/Equity: {context.get('facts', {}).get('debt_to_equity', 'N/A')}

Provide a concise risk assessment focusing on:
1. Volatility implications for investors
2. Risk-reward profile analysis
3. Key risk factors to monitor
4. Investment suitability considerations

Keep response under 150 words and use bullet points for clarity."""

        return self.tools["llm"]._call_llm(prompt)
    
    def _get_company_context(self, ticker: str) -> Dict[str, Any]:
        """Get company context for LLM analysis"""
        try:
            profile = self.tools.get("mkt", {}).company_profile(ticker) if hasattr(self.tools.get("mkt"), "company_profile") else {}
            facts = self.tools.get("mkt", {}).compute_quick_facts(ticker) if hasattr(self.tools.get("mkt"), "compute_quick_facts") else {}
            
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
                "risk_analysis": risk_analysis
            }
        except Exception:
            return {"profile": {}, "facts": {}, "risk_analysis": ""}
