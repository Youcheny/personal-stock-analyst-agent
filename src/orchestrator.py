from datetime import datetime
from pathlib import Path

class Orchestrator:
    def __init__(self, coordinator, specialists):
        self.coordinator = coordinator
        self.specialists = specialists

    # --- ADK_WIRE_HERE ---
    def run_research_memo(self, ticker: str) -> str:
        base = self.coordinator.research_brief(ticker)
        addenda = []
        for key in ["tech", "fins", "quant"]:
            if key in self.specialists:
                addenda.append(self.specialists[key].annotate(ticker))
        memo = self.coordinator.compile_memo(ticker, base, addenda)
        out_dir = Path("out"); out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"memo_{ticker}_{datetime.now().date()}.md"
        out_path.write_text(memo, encoding="utf-8")
        return str(out_path)

    def run_screen(self, min_fcf_yield: float = 0.04, min_roic: float = 0.10, universe=None) -> str:
        if universe is None:
            universe = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "JPM", "BRK-B", "JNJ", "PG", "XOM"]
        rows, rejects = [], []
        for t in universe:
            facts = self.coordinator.compute_facts(t)
            if not facts:
                rejects.append((t, "no facts"))
                continue
            fy = facts.get("fcf_yield_ttm"); roic = facts.get("roic_est")
            reason = []
            if fy is None: reason.append("fcf_yield_ttm=None")
            elif fy < min_fcf_yield: reason.append(f"fcf_yield_ttm<{min_fcf_yield:.2%}")
            if roic is None: reason.append("roic_est=None")
            elif roic < min_roic: reason.append(f"roic_est<{min_roic:.2%}")
            if reason:
                rejects.append((t, "; ".join(reason)))
            else:
                rows.append({"ticker": t, "fcf_yield_ttm": fy, "roic_est": roic, "debt_to_equity": facts.get("debt_to_equity")})

        out_dir = Path("out"); out_dir.mkdir(exist_ok=True)
        out_path = out_dir / f"screen_{datetime.now().date()}.md"

        def pct(x): 
            return f"{x:.2%}" if isinstance(x, (int, float)) else "n/a"

        md = ["# Screen Results", ""]
        if rows:
            md += ["| ticker | fcf_yield_ttm | roic_est | debt_to_equity |", "|---|---:|---:|---:|"]
            for r in rows:
                md.append(f"| {r['ticker']} | {pct(r['fcf_yield_ttm'])} | {pct(r['roic_est'])} | {r.get('debt_to_equity') if r.get('debt_to_equity') is not None else 'n/a'} |")
            md.append("")
        else:
            md += ["_No symbols passed the filter._", ""]
        if rejects:
            md += ["## Rejections (debug)", ""]
            for t, why in rejects:
                md.append(f"- **{t}** → {why}")
        out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        return str(out_path)
