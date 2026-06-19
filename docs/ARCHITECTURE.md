# CogAlpha 架构文档

## 系统概述

CogAlpha是一个全自动因子挖掘框架，采用七级智能体架构驱动大语言模型生成、演化Alpha因子，并通过严格的质量检查与样本外验证筛选精英因子。

```
┌─────────────────────────────────────────────────────────────┐
│                        CogAlpha MVP                          │
├─────────────────────────────────────────────────────────────┤
│  CLI Layer (cogalpha/cli.py)                                │
│  ├── init                                                   │
│  ├── validate-data                                          │
│  ├── run-mvp                                                │
│  └── report                                                 │
├─────────────────────────────────────────────────────────────┤
│  Pipeline (examples/run_mvp.py)                             │
│  Data → Generate → Parse → Quality → Leakage → Evaluate → Report│
├─────────────────────────────────────────────────────────────┤
│  Core Modules                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  config  │  │  data    │  │  agents  │  │  llm     │   │
│  │  .py     │  │  synthetic│  │  registry│  │  base    │   │
│  │          │  │  validator│  │  renderer│  │  mock    │   │
│  │          │  │  loader  │  │  templates│  │  openai  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  factors │  │  factors │  │  factors │  │  reports │   │
│  │  object  │  │  parser  │  │  quality │  │  writer  │   │
│  │  sandbox │  │  leakage │  │  evaluator│  │          │   │
│  │  library │  │          │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐                                              │
│  │ evolution│                                              │
│  │ elite_pool│  │ feedback │  │ loop    │                 │
│  └──────────┘                                              │
├─────────────────────────────────────────────────────────────┤
│  Tests (pytest)                                              │
│  test_config, test_data_validator, test_factor_parser,      │
│  test_quality_checks, test_leakage_detection,               │
│  test_evaluator, test_llm_providers, test_agents_registry,  │
│  test_pipeline_smoke                                         │
└─────────────────────────────────────────────────────────────┘
```

## 模块详解

### 1. 配置模块 (`config.py`)

- 使用 Pydantic v2 进行模式验证
- 支持 YAML 配置文件加载
- 环境变量覆盖（`${VAR_NAME}` 语法）
- API Key 在日志输出中自动脱敏
- 字段覆盖：API、数据、演化、智能体、路径、日志

### 2. 数据模块 (`data/`)

#### `synthetic.py`
- 生成随机游走带漂移的合成OHLCV数据
- 返回 `(date, symbol)` MultiIndex DataFrame
- 支持 Parquet 保存

#### `validator.py`
- `DataValidator` 类：验证OHLCV字段、日期范围、缺失值
- 提供前向填充和异常报告

#### `loader.py`
- 读取 Parquet（或 CSV 降级）

### 3. 智能体模块 (`agents/`)

#### `registry.py`
- 定义21个 `AgentSpec` 数据类
- 覆盖Lv1-Lv7，每层3个智能体
- 提供 `get_all_agents()` 和 `get_agent_by_id()`

#### `prompt_templates.py`
- `BASE_SYSTEM_PROMPT` 和五种生成模式描述

#### `prompt_renderer.py`
- `PromptRenderer`：Jinja2 模板渲染
- 动态注入：生成模式、无效案例、精英思路
- 温度参数映射

### 4. LLM 模块 (`llm/`)

#### `base.py`
- `BaseLLMProvider` 抽象基类
- `GenerationResult` 数据类

#### `mock_provider.py`
- `MockLLMProvider`：返回预定义的3个可运行因子
- 无未来信息泄漏，无外部依赖
- **MVP默认使用此Provider**

#### `openai_provider.py`
- `OpenAICompatibleProvider`：支持OpenAI兼容API
- 使用 `tenacity` 指数退避重试
- 仅重试连接/超时/限流错误，不重试认证错误
- 并发控制：`asyncio.Semaphore`
- 需通过环境变量配置API Key

### 5. 因子模块 (`factors/`)

#### `object.py`
- `FactorObject` 数据类：factor_id, agent_id, mode, raw_code, status, errors, metrics, created_at

#### `parser.py`
- `FactorParser`：正则提取 `<function>` 标签
- 清理 markdown 代码块，标准化缩进
- 降级：正则匹配 `def` 函数
- `ast.parse` 语法验证

#### `quality.py`
- `QualityChecker`：静态扫描未来函数关键词
- `check_signature`：验证函数签名（单参数DataFrame）
- `check_runnable`：沙盒执行验证

#### `leakage.py`
- `LeakageDetector`：时序截断检测
- 随机抽样日期，全量 vs 截断数据对比
- 差异阈值：1e-10

#### `evaluator.py`
- `FactorEvaluator`：计算IC、RankIC、ICIR、RankICIR
- 分组收益（5分位）与 long-short 收益
- 严格区分 train/test 数据
- 前向收益计算（`close.shift(-1) / close - 1`）

#### `sandbox.py`
- `sandbox_exec`：受限 `exec` 环境执行因子代码
- 仅注入 `pandas`, `numpy`, `scipy`

#### `library.py`
- `FactorLibrary`：存储、筛选、导出因子集合

### 6. 演化模块 (`evolution/`)

#### `elite_pool.py`
- `ElitePool`：管理精英因子，去重，保留Top 2

#### `feedback.py`
- `FeedbackLog`：记录无效因子，生成提示词注入摘要

#### `loop.py`
- `EvolutionLoop`：简化版进化循环
- 注入间隔生成，突变/交叉为MVP stub

### 7. 报告模块 (`reports/`)

#### `report_writer.py`
- `write_factor_report`：Markdown 格式报告
- `write_metrics_csv`：CSV 指标汇总
- 包含MVP免责声明

## 数据流

```
[Config] → [Synthetic Data] → [Mock LLM] → [Raw Response]
                                              ↓
[Factor Report] ← [Evaluate] ← [Leakage] ← [Quality] ← [Parse]
       ↓
[CSV Metrics] ← [Factor Library]
```

## 安全设计

1. **API Key 保护**：环境变量优先，日志自动脱敏
2. **未来信息泄漏防护**：静态扫描 + 动态截断检测
3. **沙盒执行**：因子代码在受限命名空间运行
4. **数据隔离**：训练期与测试期严格分离

## 扩展点

| 扩展方向 | 当前状态 | 扩展方式 |
|---------|---------|---------|
| 真实数据接入 | 仅合成数据 | 实现 `data/loader.py` 对接真实数据源 |
| 真实LLM | 仅Mock | 配置 `provider: openai` 并设置环境变量 |
| 完整进化 | 注入已实现，突变/交叉为stub | 完善 `evolution/loop.py` 中的 LLM 调用 |
| 技术指标 | 仅pandas/numpy | 可选接入 TA-Lib |
| 回测框架 | 自编评估 | 可选接入 backtrader |

## 测试策略

- **单元测试**：每个模块独立测试（parser, quality, leakage, evaluator, config, data, agents, llm）
- **集成测试**：`test_pipeline_smoke.py` 端到端验证完整数据流
- **CI**：GitHub Actions，pytest + ruff（可选）
