"""End-to-end smoke test for the CogAlpha MVP pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from cogalpha.data.synthetic import generate_synthetic_ohlcv
from cogalpha.llm.mock_provider import MockLLMProvider
from cogalpha.factors.parser import FactorParser
from cogalpha.factors.quality import QualityChecker
from cogalpha.factors.leakage import LeakageDetector
from cogalpha.factors.evaluator import FactorEvaluator
from cogalpha.reports.report_writer import ReportWriter
from cogalpha.agents.agent import AgentRegistry


def test_pipeline_smoke():
    # 1. Generate synthetic data
    df = generate_synthetic_ohlcv(n_symbols=2, n_days=100, start_date="2020-01-01")
    assert len(df) > 0

    # 2. Mock LLM provider
    llm = MockLLMProvider()
    agents = AgentRegistry(llm_provider=llm)
    raw_outputs = agents.generate_batch(batch_size=6)
    assert len(raw_outputs) > 0

    # 3. Parse all factors
    all_factors = []
    for raw in raw_outputs:
        parsed = FactorParser.parse_to_objects(raw, agent_id="mock")
        all_factors.extend(parsed)
    assert len(all_factors) > 0

    # 4. Quality check
    qc = QualityChecker()
    valid_factors = [f for f in all_factors if qc.check(f)]
    assert len(valid_factors) > 0

    # 5. Leakage check
    ld = LeakageDetector()
    passed_factors = [f for f in valid_factors if ld.check(f)]
    assert len(passed_factors) > 0

    # 6. Evaluate all valid ones
    evaluator = FactorEvaluator(
        df=df,
        train_start="2020-01-01",
        train_end="2020-06-01",
        test_start="2020-06-02",
        test_end="2020-12-31",
    )
    for f in passed_factors:
        evaluator.evaluate_factor(f)
        f.status = "elite" if f.metrics.get("composite_score", 0) > 0.15 else "valid"

    # At least one factor passes all checks and has metrics
    elite_or_valid = [f for f in passed_factors if f.status in ("elite", "valid")]
    assert len(elite_or_valid) >= 1
    assert all(f.metrics for f in elite_or_valid)

    # 7. Report files created
    output_dir = Path("results/final_factor_library")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "factor_report.md"
    csv_path = output_dir / "factor_metrics.csv"

    ReportWriter.write_factor_report(all_factors, str(report_path))
    ReportWriter.write_metrics_csv(all_factors, str(csv_path))

    assert report_path.exists()
    assert csv_path.exists()
    assert report_path.read_text(encoding="utf-8")
    assert csv_path.read_text(encoding="utf-8")

    print("Smoke test passed!")
