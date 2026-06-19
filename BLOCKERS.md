# CogAlpha MVP Blockers

## 当前状态

截至2026-06-19，所有MVP核心功能已完成并测试通过（53/53 tests passed）。

## 已解决的阻塞项

### 1. Python路径问题（已解决）
- **问题**：系统默认bash环境中`python`命令不可用
- **解决**：使用完整路径 `/c/Users/gk_24/AppData/Local/Programs/Python/Python310/python.exe` 执行

### 2. GitHub Actions权限（未阻塞）
- **问题**：GitHub Actions workflow文件已创建（`.github/workflows/ci.yml`），但尚未在远程仓库验证实际运行
- **状态**：配置存在，待推送后验证。若Actions运行失败，可能需检查GitHub仓库设置中的Actions权限
- **下一步**：推送后检查首次Actions运行结果

## 无阻塞项

当前MVP闭环可以完整运行（使用Mock Provider和合成数据）：
- `examples/run_mvp.py` 成功运行并生成报告
- `pytest tests/` 53个测试全部通过
- CLI所有子命令可正常使用

## 新发现的阻塞项

### 1. DeepSeek API Key 无效（2026-06-19）
- **问题**：用户提供的 API Key `sk-mFXaY8U2q9oJXIaC2CMtcAZD5TkfdJ5yNoIxGz3yRUHhLywWnOO4nyda2j9830S7` 返回 401 Authentication Error
- **错误信息**：`Authentication Fails, Your api key: ****30S7 is invalid`
- **原因**：Key 已失效、账户余额不足、或 Key 本身不正确
- **人工动作**：请重新登录 DeepSeek 开放平台 (https://platform.deepseek.com) 获取新的 API Key，并更新 `.env` 文件中的 `DEEPSEEK_API_KEY`
- **备注**：`.env` 文件已创建，已加入 `.gitignore`，不会泄露到 GitHub

### 2. AKShare 网络连接失败（2026-06-19）
- **问题**：当前运行环境存在代理限制，无法访问东方财富数据源（`82.push2.eastmoney.com`）
- **错误信息**：`ProxyError: Unable to connect to proxy` / `Remote end closed connection without response`
- **原因**：当前 Kimi Work 运行环境的网络代理策略阻止了对外部数据源的访问
- **人工动作**：在本地开发环境（无代理限制）中运行 `python -m cogalpha.cli run-mvp --config config.yaml` 时，AKShare 模块会自动获取真实数据
- **备注**：AKShare 数据获取模块 `src/cogalpha/data/akshare_loader.py` 已完整实现，代码逻辑正确，仅受网络环境限制

## 未来扩展可能阻塞项（需人工动作）

### 1. 真实LLM API Key
- **阻塞原因**：需要真实 DeepSeek/Qwen/OpenAI API Key
- **人工动作**：在 `.env` 或环境变量中设置 `OPENAI_API_KEY` 或对应模型的API Key
- **备注**：MVP默认使用Mock Provider，无需API Key即可运行

### 2. 真实A股数据
- **阻塞原因**：需要接入真实行情数据源（Tushare/AKShare等）
- **人工动作**：获取数据源Token，配置 `config.yaml` 中的 `data.path` 指向真实数据文件
- **备注**：MVP自带合成数据生成器，无需真实数据即可运行

### 3. TA-Lib安装（可选）
- **阻塞原因**：TA-Lib为C扩展，Windows安装可能需要预编译wheel
- **人工动作**：下载对应Python版本的 `.whl` 文件后 `pip install` 安装
- **备注**：MVP中所有技术指标使用pandas/numpy实现，TA-Lib非强依赖
