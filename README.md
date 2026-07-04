# TradingAgents-jpn: JP Equity Research Copilot

## Product Source

The canonical product definition is [docs/prd.md](docs/prd.md). This README is the usage and implementation guide derived from that PRD.

Release history and upstream framework changes are tracked in [CHANGELOG.md](CHANGELOG.md).

<div align="center">

🚀 [Product Positioning](#product-positioning) | 📋 [PRD](docs/prd.md) | 📁 [Project Structure](#project-structure) | ⚡ [Installation & CLI](#installation-and-cli) | 📦 [Package Usage](#tradingagents-package) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)

</div>

## Product Positioning

TradingAgents-jpn is a Japan-oriented equity research copilot designed for investment committees, advisory teams, and internal research workflows. Instead of positioning the system as an auto-trading bot, this version packages the multi-agent framework as a structured Japanese research assistant.

The product scope, non-goals, data-layer status, and acceptance criteria are defined in [docs/prd.md](docs/prd.md).

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;">
</p>

> `投資助言ではありません`. TradingAgents-jpn is designed for research support and internal review workflows. It does not provide investment advice and does not automatically execute real trades.

### What It Produces

- Japanese-language investment committee reports for names such as `7203.T`, `6758.T`, or `9984.T`
- A fixed recommendation structure including `投資判断`, `確信度`, `主要根拠`, `反対意見`, `最大リスク`, and `次に確認すべき材料`
- An internal audit trail with the input ticker, analysis date, model/provider, benchmark, and final reasoning
- A saved report header that reflects the actual runtime benchmark, including explicit overrides such as `^TOPX`

### Who It Fits

- Japanese small-to-mid-sized asset managers
- Internal investment committees inside operating companies or family offices
- Advisory and research support teams that need explainable first-pass analysis
- Fintech products that want a Japan-market research layer before execution tooling

### Why This Packaging

- It matches Japanese business communication better than a plain `BUY / SELL signal`
- It makes risk, counterarguments, and next checkpoints first-class outputs
- It keeps the boundary clear between research assistance and trade execution

## Project Structure

```
TradingAgents-jpn/
├── README.md                 # Installation, CLI, and package usage
├── CHANGELOG.md              # Release history
├── LICENSE
├── pyproject.toml            # Package metadata and dependencies
├── main.py                   # Minimal programmatic example
├── Dockerfile
├── docker-compose.yml
├── .env.example              # API key template
├── assets/                   # Architecture and CLI screenshots
├── cli/                      # Interactive CLI (`tradingagents` entry point)
├── docs/                     # Product and engineering documentation
│   ├── prd.md                # Product requirements (source of truth)
│   ├── plan.md               # Japan customization roadmap
│   ├── jp_product_onepager.md
│   └── e2e_verification_checklist.md
├── scripts/                  # Dev and smoke-test utilities
├── tests/                    # Unit, integration, and E2E tests
└── tradingagents/            # Core multi-agent framework
    ├── agents/               # Analysts, researchers, risk, portfolio manager
    ├── dataflows/            # Market data providers and JP data layer
    ├── graph/                # LangGraph workflow orchestration
    └── llm_clients/          # LLM provider adapters
```

See [docs/README.md](docs/README.md) for the full documentation index.

The system decomposes complex equity-research tasks into specialized roles.

### Analyst Team
- Fundamentals Analyst: Evaluates company financials and performance metrics, identifying intrinsic values and potential red flags.
- Sentiment Analyst: Aggregates news headlines, StockTwits, and Reddit chatter into a single sentiment read to gauge short-term market mood.
- News Analyst: Monitors global news and macroeconomic indicators, interpreting the impact of events on market conditions.
- Technical Analyst: Utilizes technical indicators (like MACD and RSI) to detect trading patterns and forecast price movements.

<p align="center">
  <img src="assets/analyst.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Researcher Team
- Comprises both bullish and bearish researchers who critically assess the insights provided by the Analyst Team. Through structured debates, they balance potential gains against inherent risks.

<p align="center">
  <img src="assets/researcher.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Trader Agent
- Translates the research view into a research-only transaction proposal, clarifying action, entry logic, and sizing guidance without implying automatic execution.

<p align="center">
  <img src="assets/trader.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Risk Management and Portfolio Manager
- Continuously evaluates portfolio risk by assessing market volatility, liquidity, and other risk factors. The risk management team evaluates and adjusts the proposed stance before a final committee-style recommendation is produced.
- The Portfolio Manager produces the final research recommendation. In the Japan-oriented profile, the default mode is research-only: no real order is executed automatically, and every decision is logged for internal review.

> Research-only default: `投資助言ではありません`. The framework is designed to support analysis workflows, not to provide investment advice or automatic trade execution.

<p align="center">
  <img src="assets/risk.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

## Installation and CLI

### Installation

Use the existing checkout:
```bash
cd TradingAgents-jpn
```

Create a virtual environment in any of your favorite environment managers:
```bash
conda create -n tradingagents python=3.13
conda activate tradingagents
```

Install the package and its dependencies:
```bash
pip install .
```

### Docker

Alternatively, run with Docker:
```bash
cp .env.example .env  # add your API keys
docker compose run --rm tradingagents
```

For local models with Ollama:
```bash
docker compose --profile ollama run --rm tradingagents-ollama
```

### Upstream

TradingAgents-jpn is packaged from the open-source `TradingAgents` framework and adapted here for a Japan-oriented, research-only workflow. Keep upstream attribution in release notes or internal documentation when redistributing this fork.

### Required APIs

TradingAgents supports multiple LLM providers. Set the API key for your chosen provider:

```bash
export OPENAI_API_KEY=...          # OpenAI (GPT)
export GOOGLE_API_KEY=...          # Google (Gemini)
export ANTHROPIC_API_KEY=...       # Anthropic (Claude)
export XAI_API_KEY=...             # xAI (Grok)
export DEEPSEEK_API_KEY=...        # DeepSeek
export DASHSCOPE_API_KEY=...       # Qwen — International (dashscope-intl.aliyuncs.com)
export DASHSCOPE_CN_API_KEY=...    # Qwen — China (dashscope.aliyuncs.com)
export ZHIPU_API_KEY=...           # GLM via Z.AI (international)
export ZHIPU_CN_API_KEY=...        # GLM via BigModel (China, open.bigmodel.cn)
export MINIMAX_API_KEY=...         # MiniMax — Global (api.minimax.io, M2.x, 204K ctx)
export MINIMAX_CN_API_KEY=...      # MiniMax — China (api.minimaxi.com, M2.x, 204K ctx)
export OPENROUTER_API_KEY=...      # OpenRouter
export ALPHA_VANTAGE_API_KEY=...   # Alpha Vantage
```

For enterprise providers (e.g. Azure OpenAI, AWS Bedrock), copy `.env.enterprise.example` to `.env.enterprise` and fill in your credentials.

For local models, configure Ollama with `llm_provider: "ollama"`. The default endpoint is `http://localhost:11434/v1`; set `OLLAMA_BASE_URL` to point at a remote `ollama-serve`. Pull models with `ollama pull <name>`, and pick "Custom model ID" in the CLI for any model not listed by default.

Alternatively, copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### CLI Usage

Launch the interactive CLI:
```bash
tradingagents          # installed command
python -m cli.main     # alternative: run directly from source
```
You will see a screen where you can select Japanese or global tickers, the analysis date, the LLM provider, and the research depth. In the Japan-oriented profile, the output defaults to a Japanese investment-committee report.

### Markets and tickers

TradingAgents works with any market Yahoo Finance covers, using the exchange-suffixed ticker. Company identity and the alpha benchmark resolve automatically per market.

- US: `AAPL`, `SPY`
- Hong Kong: `0700.HK` · Tokyo: `7203.T` · London: `AZN.L`
- India: `RELIANCE.NS`, `.BO` · Canada: `.TO` · Australia: `.AX`
- China A-shares: Shanghai `.SS`, Shenzhen `.SZ` (e.g. `600519.SS` for Kweichow Moutai)
- Crypto: `BTC-USD`, `ETH-USD`

<p align="center">
  <img src="assets/cli/cli_init.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

An interface will appear showing results as they load, letting you track the agent's progress as it runs.

<p align="center">
  <img src="assets/cli/cli_news.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

<p align="center">
  <img src="assets/cli/cli_transaction.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

## TradingAgents Package

### Japan Profile

The default profile in this repository is `jp_equity`.

- Default language: `Japanese`
- Default Tokyo suffix completion: `7203 -> 7203.T`
- Default benchmark: `^N225`
- Optional Japan benchmark family: `^TOPX`
- Default execution mode: `research_only`
- Audit trail: enabled through result logs plus JSONL audit entries

### Audit Trail

Each completed run produces two parallel review artifacts:

- A human-readable report with a localized header showing the actual benchmark used for the run
- A JSONL audit record containing:
  - ticker
  - trade date
  - model/provider
  - benchmark
  - final signal
  - `投資判断`
  - `確信度`
  - `主要根拠`
  - `反対意見`
  - `最大リスク`
  - `次に確認すべき材料`

Multi-line committee sections are preserved in the audit log so internal reviewers do not lose bullet points or wrapped rationale.

### Japan Data Layer

The repository now includes extension points for a Japan-specific research layer.

- Macro context: BOJ policy, `USD/JPY`, `JGB` yields, `TOPIX / Nikkei` relative framing
- Disclosure context: `TDnet`, `EDINET`, local filing and report adapters
- Earnings digest context: `決算短信` summary extraction

These adapters are wired as explicit provider interfaces with source labels and timestamps so future live connectors can be added without changing the analyst workflow shape.

At the current stage, these Japan-market connectors are framework-level extension points rather than live production feeds. The repository now includes both placeholder adapters and an explicit offline `phase4_yfinance_mock` provider for routed JP-workflow validation: analysts can call the tools, the outputs carry `source_label` and `fetched_at_utc`, and reports/audit trails can preserve that provenance.

The authoritative data-layer status is maintained in [docs/prd.md#8-japan-data-layer-requirements](docs/prd.md#8-japan-data-layer-requirements).

For offline validation support:

- E2E checklist: [docs/e2e_verification_checklist.md](docs/e2e_verification_checklist.md)
- Phase 4 offline fixtures: [tests/fixtures/phase4_yfinance_mock/README.md](tests/fixtures/phase4_yfinance_mock/README.md)

### Implementation Details

We built TradingAgents with LangGraph to ensure flexibility and modularity. The framework supports multiple LLM providers: OpenAI, Google, Anthropic, xAI, DeepSeek, Qwen (Alibaba DashScope, international and China endpoints), GLM (Zhipu), MiniMax (global + China), OpenRouter, Ollama for local models, and Azure OpenAI for enterprise.

### Python Usage

To use TradingAgents-jpn inside your code, you can import the `tradingagents` module and initialize a `TradingAgentsGraph()` object. The `.propagate()` function returns the final research recommendation and the parsed signal. You can run `main.py`, here's also a quick example:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())

# forward propagate
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

You can also adjust the default configuration to set your own choice of LLMs, debate rounds, etc.

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"        # openai, google, anthropic, xai, deepseek, qwen, qwen-cn, glm, glm-cn, minimax, minimax-cn, openrouter, ollama, azure
config["deep_think_llm"] = "gpt-5.5"     # Model for complex reasoning
config["quick_think_llm"] = "gpt-5.4-mini" # Model for quick tasks
config["max_debate_rounds"] = 2

ta = TradingAgentsGraph(debug=True, config=config)
_, decision = ta.propagate("NVDA", "2026-01-15")
print(decision)
```

See `tradingagents/default_config.py` for all configuration options.

## Persistence and Recovery

TradingAgents persists two kinds of state across runs.

### Decision log

The decision log is always on. Each completed run appends its decision to `~/.tradingagents/memory/trading_memory.md`. On the next run for the same ticker, TradingAgents fetches the realised return (raw and alpha vs SPY), generates a one-paragraph reflection, and injects the most recent same-ticker decisions plus recent cross-ticker lessons into the Portfolio Manager prompt, so each analysis carries forward what worked and what didn't.

Override the path with `TRADINGAGENTS_MEMORY_LOG_PATH`.

### Checkpoint resume

Checkpoint resume is opt-in via `--checkpoint`. When enabled, LangGraph saves state after each node so a crashed or interrupted run resumes from the last successful step instead of starting over. On a resume run you will see `Resuming from step N for <TICKER> on <date>` in the logs; on a new run you will see `Starting fresh`. Checkpoints are cleared automatically on successful completion.

Per-ticker SQLite databases live at `~/.tradingagents/cache/checkpoints/<TICKER>.db` (override the base with `TRADINGAGENTS_CACHE_DIR`). Use `--clear-checkpoints` to reset all of them before a run.

```bash
tradingagents analyze --checkpoint           # enable for this run
tradingagents analyze --clear-checkpoints    # reset before running
```

```python
config = DEFAULT_CONFIG.copy()
config["checkpoint_enabled"] = True
ta = TradingAgentsGraph(config=config)
_, decision = ta.propagate("NVDA", "2026-01-15")
```

## Reproducibility

TradingAgents is LLM-driven, so two runs of the same ticker and date can differ. This is expected for a research tool built on language models, not a defect. The variation comes from a few distinct sources, and it helps to separate them.

Language model sampling is non-deterministic. Even at a fixed temperature, providers do not guarantee byte-identical output across calls, and reasoning models (the default GPT-5.x family, and any thinking-mode model) vary the most because their internal reasoning is itself sampled.

Live data moves. News, StockTwits, and Reddit return different content as time passes, so a run today sees different inputs than a run last week even for the same historical trade date. Pin the analysis date to hold the price and indicator window fixed, but the social and news sources still reflect "now".

To reduce variation you can lower the sampling temperature. Set `temperature` in your config (or `TRADINGAGENTS_TEMPERATURE` in `.env`); lower values make models that honor it more repeatable. Reasoning models largely ignore temperature, so for tighter reproducibility pair a low temperature with a non-reasoning model such as `gpt-4.1`.

```python
config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["deep_think_llm"] = "gpt-4.1"      # non-reasoning model honors temperature
config["quick_think_llm"] = "gpt-4.1"
config["temperature"] = 0.0
```

What does not vary anymore: the analyzed company identity is resolved deterministically from the ticker before any agent runs, and the market analyst grounds exact price and indicator claims in a verified data snapshot. Earlier reports of "different companies" or fabricated price levels across runs are addressed by these two mechanisms.

Backtest results are not guaranteed to match any published figure. Returns depend on the model, the temperature, the date range, data quality, and the sampling above. Treat the framework as a research scaffold for studying multi-agent analysis, not as a strategy with a fixed, replicable return.



