"""Run the complete CogAlpha MVP pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tqdm import tqdm
from cogalpha.data.synthetic import generate_synthetic_ohlcv, save_synthetic, load_synthetic
from cogalpha.llm.mock_provider import MockLLMProvider
from cogalpha.factors.parser import FactorParser
from cogalpha.factors.quality import QualityChecker
from cogalpha.factors.leakage import LeakageDetector
from cogalpha.factors.evaluator import FactorEvaluator
from cogalpha.reports.report_writer import ReportWriter
from cogalpha.agents.agent import AgentRegistry


def main():
    print("=" * 60)
    print("CogAlpha Factor Mining MVP")
    print("DISCLAIMER: This uses synthetic data and a mock LLM provider.")
    print("Results do NOT represent real investment performance.")
    print("=" * 60)

    # 1. Synthetic data
    print("\n[1/6] Generating synthetic OHLCV data...")
    data_path = Path("data/synthetic_ohlcv.parquet")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if not data_path.exists():
        df = generate_synthetic_ohlcv()
        save_synthetic(df, str(data_path))
    else:
        df = load_synthetic(str(data_path))
    print(f"  Data: {len(df)} rows, columns={list(df.columns)}")

    # 2. Mock factor generation
    print("\n[2/6] Generating mock factors from LLM...")
    llm = MockLLMProvider()
    agents = AgentRegistry(llm_provider=llm)
    raw_outputs = agents.generate_batch(batch_size=8)
    print(f"  Generated {len(raw_outputs)} raw outputs")

    # 3. Parse
    print("\n[3/6] Parsing factors...")
    all_factors = []
    for raw in tqdm(raw_outputs, desc="Parsing"):
        parsed = FactorParser.parse_to_objects(raw, agent_id="mock")
        all_factors.extend(parsed)
    print(f"  Parsed {len(all_factors)} factors")

    # 4. Quality check
    print("\n[4/6] Quality checking...")
    qc = QualityChecker()
    valid_factors = []
    for f in tqdm(all_factors, desc="Quality"):
        if qc.check(f):
            valid_factors.append(f)
    print(f"  Valid after quality: {len(valid_factors)}")

    # 5. Leakage detection
    print("\n[5/6] Leakage detection...")
    ld = LeakageDetector()
    passed_factors = []
    for f in tqdm(valid_factors, desc="Leakage"):
        if ld.check(f):
            passed_factors.append(f)
    print(f"  Passed leakage: {len(passed_factors)}")

    # 6. Evaluate
    print("\n[6/6] Evaluating factors...")
    evaluator = FactorEvaluator(
        df=df,
        train_start="2011-01-01",
        train_end="2019-12-31",
        test_start="2020-01-01",
        test_end="2025-12-31",
    )
    for f in tqdm(passed_factors, desc="Evaluate"):
        evaluator.evaluate_factor(f)
        if f.metrics.get("composite_score", 0) > 0.15:
            f.status = "elite"
        else:
            f.status = "valid"
    print(f"  Evaluated {len(passed_factors)} factors")

    # Save reports
    output_dir = Path("results/final_factor_library")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "factor_report.md"
    csv_path = output_dir / "factor_metrics.csv"

    ReportWriter.write_factor_report(all_factors, str(report_path))
    ReportWriter.write_metrics_csv(all_factors, str(csv_path))

    print(f"\n{'=' * 60}")
    print("Pipeline complete!")
    print(f"  Report: {report_path}")
    print(f"  CSV:    {csv_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
