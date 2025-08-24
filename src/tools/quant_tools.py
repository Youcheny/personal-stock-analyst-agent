from __future__ import annotations
import pandas as pd
import numpy as np

class QuantTools:
    """Lightweight quant helpers used by the QuantAgent and screens."""

    def max_drawdown(self, prices: pd.Series | pd.DataFrame) -> float:
        s = prices if isinstance(prices, pd.Series) else prices.iloc[:, 0]
        roll_max = s.cummax()
        dd = s / roll_max - 1.0
        return float(dd.min())

    def annualized_vol(self, returns: pd.Series, periods_per_year: int = 252) -> float:
        """Calculate annualized volatility from return series."""
        if returns.empty:
            return 0.0
        return float(returns.std(ddof=0).iloc[0] * np.sqrt(periods_per_year))

    def buy_and_hold_metrics(self, close: pd.Series) -> dict:
        ret = close.pct_change().dropna()
        vol = self.annualized_vol(ret)
        dd = self.max_drawdown(close)
        total_return = float(close.iloc[-1] / close.iloc[0] - 1.0)
        sharpe_proxy = total_return / vol if vol > 0 else np.nan
        return { "total_return": total_return, "ann_vol": vol, "max_drawdown": dd, "sharpe_proxy": sharpe_proxy }
