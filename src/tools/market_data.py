import datetime as dt
import pandas as pd
import yfinance as yf
from typing import Optional

class MarketData:
    def __init__(self, polygon_api_key: Optional[str]):
        self.polygon_api_key = polygon_api_key

    def last_price_link(self, ticker: str) -> str:
        return f"https://finance.yahoo.com/quote/{ticker}"

    def company_profile(self, ticker: str) -> dict | None:
        try:
            info = yf.Ticker(ticker).info
            return info or {}
        except Exception:
            return {}

    def history(self, ticker: str, period_days: int = 365) -> pd.DataFrame | None:
        end = dt.date.today()
        start = end - dt.timedelta(days=period_days + 7)
        try:
            df = yf.download(ticker, start=start.isoformat(), end=end.isoformat(), progress=False, auto_adjust=True)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df = df.rename(columns=str.title)
                return df
            return None
        except Exception:
            return None

    def compute_quick_facts(self, ticker: str) -> dict | None:
        """Robust fundamentals with layered fallbacks."""
        try:
            t = yf.Ticker(ticker)
            info = t.info or {}

            def ig(key):
                v = info.get(key)
                try:
                    return float(v) if v is not None else None
                except Exception:
                    return None

            # Market cap (prefer info, else fast_info)
            mcap = ig("marketCap")
            if not mcap:
                try:
                    fi = getattr(t, "fast_info", {})
                    mcap = float(fi.get("market_cap")) if fi and fi.get("market_cap") else None
                except Exception:
                    mcap = None

            # Primary fields
            fcf = ig("freeCashflow")
            gross_margin = ig("grossMargins")
            op_margin = ig("operatingMargins")
            total_debt = ig("totalDebt")
            total_equity = ig("totalStockholderEquity")
            cash = ig("totalCash")
            ebit = ig("ebit")
            if ebit is None:
                ebitda = ig("ebitda")
                if ebitda is not None:
                    ebit = 0.85 * ebitda  # rough proxy

            # Statements for backfill
            cf = getattr(t, "cashflow", None)
            fin = getattr(t, "financials", None)
            bs = getattr(t, "balance_sheet", None)

            def _safe_df(df): return (df is not None) and hasattr(df, "empty") and (not df.empty)

            def sget(df, *names):
                if not _safe_df(df):
                    return None
                idx = df.index
                for nm in names:
                    if nm in idx:
                        try:
                            val = df.loc[nm].iloc[0]
                            return float(val)
                        except Exception:
                            pass
                return None

            if fcf is None:
                fcf = sget(cf, "Free Cash Flow", "FreeCashFlow")
                if fcf is None:
                    cfo = sget(cf, "Total Cash From Operating Activities", "Operating Cash Flow", "Net Cash Provided By Operating Activities")
                    capex = sget(cf, "Capital Expenditures", "CapitalExpenditures")
                    if (cfo is not None) and (capex is not None):
                        fcf = cfo - capex

            if total_debt is None:
                total_debt = sget(bs, "Total Debt", "Short Long Term Debt", "Long Term Debt")
            if total_equity is None:
                total_equity = sget(bs, "Total Stockholder Equity", "Total Equity")
            if cash is None:
                cash = sget(bs, "Cash", "Cash And Cash Equivalents")

            if ebit is None:
                ebit = sget(fin, "Ebit", "EBIT")

            # Compute metrics
            fcf_yield = None
            if fcf is not None and mcap and mcap > 0:
                fcf_yield = fcf / mcap
            if fcf_yield is None:
                trailing_pe = ig("trailingPE")
                if trailing_pe and trailing_pe > 0:
                    fcf_yield = 1.0 / trailing_pe  # earnings yield proxy

            invested_capital = None
            if any(v is not None for v in [total_debt, total_equity, cash]):
                d = total_debt or 0.0
                e = total_equity or 0.0
                c = cash or 0.0
                invested_capital = max(d + e - c, 1e-6)

            roic_est = None
            if ebit is not None and invested_capital:
                nopat = ebit * (1.0 - 0.21)
                roic_est = nopat / invested_capital

            def norm_pct(x):
                if x is None:
                    return None
                try:
                    x = float(x)
                    return x / 100.0 if x > 1.5 else x
                except Exception:
                    return None

            gross_margin = norm_pct(gross_margin)
            op_margin = norm_pct(op_margin)

            debt_to_equity = None
            if total_debt is not None and total_equity not in (None, 0):
                debt_to_equity = total_debt / total_equity

            return {
                "fcf_yield_ttm": fcf_yield,
                "roic_est": roic_est,
                "gross_margin": gross_margin,
                "operating_margin": op_margin,
                "debt_to_equity": debt_to_equity,
            }
        except Exception:
            return None
