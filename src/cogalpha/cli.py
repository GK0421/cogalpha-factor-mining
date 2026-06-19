"""CLI for CogAlpha factor mining."""
import argparse
import os
import sys
from pathlib import Path

from cogalpha.config import load_config
from cogalpha.data.synthetic import generate_synthetic_ohlcv, save_synthetic, load_synthetic
from cogalpha.data.validator import DataValidator
from cogalpha.llm.mock_provider import MockLLMProvider
from cogalpha.llm.openai_provider import OpenAICompatibleProvider
from cogalpha.factors.parser import FactorParser
from cogalpha.factors.quality import QualityChecker
from cogalpha.factors.leakage import LeakageDetector
from cogalpha.factors.evaluator import FactorEvaluator
from cogalpha.reports.report_writer import ReportWriter
from cogalpha.agents.agent import AgentRegistry


def _get_llm_provider(config):
    """Create LLM provider based on config."""
    provider_name = config.api.provider.lower()
    if provider_name == "mock":
        return MockLLMProvider()
    elif provider_name in ("openai", "deepseek", "qwen"):
        # Map provider name to config section
        if provider_name == "openai":
            cfg = config.api.openai
        elif provider_name == "deepseek":
            cfg = config.api.deepseek
        elif provider_name == "qwen":
            cfg = config.api.qwen
        else:
            cfg = config.api.openai
        
        api_key = cfg.api_key
        if not api_key or api_key.startswith("${"):
            raise ValueError(
                f"API key for provider '{provider_name}' is not set. "
                f"Please set it via environment variable or in .env file."
            )
        return OpenAICompatibleProvider(
            api_key=api_key,
            base_url=cfg.base_url,
            model=cfg.model,
            max_concurrent=cfg.max_concurrent_requests,
            max_tokens=cfg.max_tokens,
            timeout=cfg.timeout,
            temperature=cfg.temperature,
        )
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def cmd_init(args):
    """Create default project directories."""
    dirs = ["data", "results", "logs", "prompts"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print("Initialized directories:", ", ".join(dirs))


def cmd_validate_data(args):
    """Load data and validate with DataValidator."""
    config = load_config(args.config)
    data_path = config.data.path
    if not Path(data_path).exists():
        print(f"Data file not found at {data_path}. Generating synthetic data...")
        df = generate_synthetic_ohlcv()
        save_synthetic(df, data_path)
    df = load_synthetic(data_path)
    validator = DataValidator(df)
    report = validator.anomaly_report()
    print("Validation report:")
    for section, details in report.items():
        print(f"  {section}: {details}")
    ok = report["ohlcv"]["has_all_columns"] and report["ohlcv"].get("high_valid", False) and report["ohlcv"].get("low_valid", False)
    sys.exit(0 if ok else 1)


def cmd_run_mvp(args):
    """Run the full MVP pipeline."""
    config = load_config(args.config)
    data_path = config.data.path

    # 1. Generate/load synthetic data
    if not Path(data_path).exists():
        print(f"Generating synthetic data -> {data_path}")
        df = generate_synthetic_ohlcv(
            symbols=config.data.symbols,
            start_date=config.data.train_start,
            end_date=config.data.test_end,
        )
        save_synthetic(df, data_path)
    else:
        df = load_synthetic(data_path)
    print(f"Loaded data: {len(df)} rows")

    # 2. Select LLM provider based on config
    print(f"Using LLM provider: {config.api.provider}")
    llm = _get_llm_provider(config)
    agents = AgentRegistry(llm_provider=llm)
    raw_outputs = agents.generate_batch(batch_size=config.evolution.initial_population_size)
    print(f"Generated {len(raw_outputs)} raw factor outputs")

    # 3. Parse factors
    all_factors = []
    for raw in raw_outputs:
        parsed = FactorParser.parse_to_objects(raw, agent_id="mock")
        all_factors.extend(parsed)
    print(f"Parsed {len(all_factors)} factors")

    # 4. Quality check + 5. Leakage check
    qc = QualityChecker()
    ld = LeakageDetector()
    valid_factors = []
    for f in all_factors:
        if qc.check(f) and ld.check(f):
            valid_factors.append(f)
    print(f"Valid factors after checks: {len(valid_factors)}")

    # 6. Evaluate valid factors
    evaluator = FactorEvaluator(
        df=df,
        train_start=config.data.train_start,
        train_end=config.data.train_end,
        test_start=config.data.test_start,
        test_end=config.data.test_end,
    )
    for f in valid_factors:
        evaluator.evaluate_factor(f)
        if f.status == "invalid":
            continue
        # Elite threshold: composite_score > 0.15
        if f.metrics.get("composite_score", 0) > 0.15:
            f.status = "elite"
        else:
            f.status = "valid"
    evaluated_count = len([f for f in valid_factors if f.status != "invalid"])
    print(f"Evaluated {evaluated_count} factors")

    # 7. Save reports
    output_dir = Path(config.paths.final_library)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "factor_report.md"
    csv_path = output_dir / "factor_metrics.csv"
    ReportWriter.write_factor_report(all_factors, str(report_path))
    ReportWriter.write_metrics_csv(all_factors, str(csv_path))
    print(f"Reports saved to {output_dir}")


def cmd_report(args):
    """Generate reports from existing results."""
    output_dir = Path("./results/final_factor_library/")
    csv_path = output_dir / "factor_metrics.csv"
    if not csv_path.exists():
        print("No existing results found. Run 'run-mvp' first.")
        sys.exit(1)
    print(f"Report would be regenerated from {csv_path}")
    print("Done.")


def main():
    parser = argparse.ArgumentParser(prog="cogalpha", description="CogAlpha factor mining CLI")
    subparsers = parser.add_subparsers(dest="command")

    # init
    p_init = subparsers.add_parser("init", help="Create default project directories")
    p_init.set_defaults(func=cmd_init)

    # validate-data
    p_validate = subparsers.add_parser("validate-data", help="Load and validate data")
    p_validate.add_argument("--config", required=True, help="Path to config YAML")
    p_validate.set_defaults(func=cmd_validate_data)

    # run-mvp
    p_run = subparsers.add_parser("run-mvp", help="Run the full MVP pipeline")
    p_run.add_argument("--config", required=True, help="Path to config YAML")
    p_run.set_defaults(func=cmd_run_mvp)

    # report
    p_report = subparsers.add_parser("report", help="Generate reports from existing results")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
