# CogAlpha Factor Mining MVP

> **DISCLAIMER**: This MVP uses synthetic/mock data and a mock LLM provider. Results do NOT represent real investment performance. Real-market validation requires actual OHLCV data and a real LLM API.

## Quick Start

```bash
# 1. Clone and enter the repo
git clone https://github.com/GK0421/cogalpha-factor-mining.git
cd cogalpha-factor-mining

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Copy example config and run MVP
cp config.example.yaml config.yaml
python examples/run_mvp.py

# 5. Run tests
pytest tests/ -v
```

## CLI Usage

```bash
# Initialize project structure
python -m cogalpha.cli init

# Validate data file
python -m cogalpha.cli validate-data --config config.example.yaml

# Run MVP pipeline
python -m cogalpha.cli run-mvp --config config.example.yaml

# Generate report
python -m cogalpha.cli report
```

## Project Structure

```
cogalpha-factor-mining/
  src/cogalpha/          # Core package
    config.py             # Configuration loader & validator
    data/                 # Data loading, validation, synthetic generation
    agents/               # 21-agent registry & prompt system
    llm/                  # LLM providers (mock + OpenAI-compatible)
    factors/              # Factor object, parser, quality, leakage, evaluator
    evolution/            # Elite pool, feedback, evolution loop
    reports/              # Report writer
    cli.py                # Command-line interface
  prompts/                # 21 Jinja2 prompt templates
  tests/                  # Unit & integration tests
  examples/               # Example scripts
  docs/                   # Documentation
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/SPEC_FROM_MANUAL.md](docs/SPEC_FROM_MANUAL.md).

## License

MIT
