"""Report writer for CogAlpha."""
import csv
from pathlib import Path
from cogalpha.factors.object import FactorObject


class ReportWriter:
    """Write markdown and CSV reports from factor evaluation results."""

    @staticmethod
    def write_factor_report(factors: list[FactorObject], path: str):
        """Write a markdown report with factor classification and metrics."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        lines = []
        lines.append("# CogAlpha Factor Mining Report\n")
        lines.append("> **Disclaimer**: This MVP uses synthetic data and a mock LLM provider. "
                     "Results do NOT represent real investment performance.\n")
        lines.append(f"## Summary\n")
        total = len(factors)
        elites = [f for f in factors if f.status == "elite"]
        qualified = [f for f in factors if f.status == "valid"]
        invalid = [f for f in factors if f.status == "invalid"]
        lines.append(f"- Total factors: {total}")
        lines.append(f"- Elite: {len(elites)}")
        lines.append(f"- Qualified (valid): {len(qualified)}")
        lines.append(f"- Invalid: {len(invalid)}\n")
        lines.append("## Factor Details\n")
        lines.append("| factor_id | agent_id | status | ic | rankic | icir | rankicir | composite_score | long_short_return |")
        lines.append("|-----------|----------|--------|-----|--------|------|----------|-----------------|-------------------|")
        for f in factors:
            m = f.metrics or {}
            lines.append(
                f"| {f.factor_id} | {f.agent_id} | {f.status} | "
                f"{m.get('ic', '')} | {m.get('rankic', '')} | {m.get('icir', '')} | {m.get('rankicir', '')} | "
                f"{m.get('composite_score', '')} | {m.get('long_short_return', '')} |"
            )
        lines.append("")
        lines.append("## Classification\n")
        lines.append("- **Elite**: Top-performing factors with high composite scores.")
        lines.append("- **Qualified**: Factors that passed all checks but are not elite.")
        lines.append("- **Invalid**: Factors that failed syntax, quality, or leakage checks.\n")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    @staticmethod
    def write_metrics_csv(factors: list[FactorObject], path: str):
        """Write a CSV with metrics for all factors."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "factor_id", "agent_id", "status", "ic", "rankic",
                "icir", "rankicir", "composite_score", "long_short_return",
            ])
            for factor in factors:
                m = factor.metrics or {}
                writer.writerow([
                    factor.factor_id,
                    factor.agent_id,
                    factor.status,
                    m.get("ic", ""),
                    m.get("rankic", ""),
                    m.get("icir", ""),
                    m.get("rankicir", ""),
                    m.get("composite_score", ""),
                    m.get("long_short_return", ""),
                ])
