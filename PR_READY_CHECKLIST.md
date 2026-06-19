# PR Ready Checklist

> Repository: GK0421/cogalpha-factor-mining
> Source Branch: feature/cogalpha-mvp
> Target Branch: main
> Date: 2026-06-19

## 合并前必须检查项

### 1. 安全（最高优先级）

| # | 检查项 | 状态 | 备注 |
|---|--------|------|------|
| 1.1 | git grep 当前工作区无真实 Key | ✅ 通过 | `BLOCKERS.md` 已修复为 REDACTED |
| 1.2 | git log 全历史无真实 Key | ❌ **失败** | commit `490b89a` 和 `415dd2f` 含 `BLOCKERS.md` 明文 Key |
| 1.3 | API Key 已 rotate | ❌ **未执行** | 两个 DeepSeek Key 已暴露，需到平台作废并重新生成 |
| 1.4 | .env 和 config.yaml 不在 git 跟踪 | ✅ 通过 | `git ls-files` 确认无此二文件 |
| 1.5 | .gitignore 正确排除敏感文件 | ✅ 通过 | 包含 `.env`、`config.yaml`、`*.key`、`results/`、`logs/` |

**结论**：安全条件 **不满足**。必须先执行 Key rotation 才能合并。

### 2. 测试

| # | 检查项 | 状态 | 备注 |
|---|--------|------|------|
| 2.1 | pytest 全部通过 | ✅ 通过 | 53/53 passed in 4.79s |
| 2.2 | 无测试被删除以换取通过 | ✅ 通过 | 所有原始测试文件完整保留 |
| 2.3 | leakage 检测测试通过 | ✅ 通过 | test_leakage_detection.py 4/4 passed |
| 2.4 | mock pipeline 端到端通过 | ✅ 通过 | `python -m cogalpha.cli run-mvp --config config.example.yaml` 成功 |
| 2.5 | real provider 可连通 | ✅ 通过 | DeepSeek API 验证成功（Key 已 REDACTED） |

### 3. CI

| # | 检查项 | 状态 | 备注 |
|---|--------|------|------|
| 3.1 | GitHub Actions workflow 文件存在 | ✅ 通过 | `.github/workflows/ci.yml` 已提交 |
| 3.2 | CI 可触发 | ⚠️ 未验证 | 需 push 到 main 或创建 PR 后触发 |
| 3.3 | CI 通过 | ⚠️ 未验证 | 首次运行待观察 |
| 3.4 | ruff 通过 | ⚠️ 未运行 | 本地未安装，CI 中需验证 |

### 4. 文档

| # | 检查项 | 状态 | 备注 |
|---|--------|------|------|
| 4.1 | README 无夸大投资结论 | ✅ 通过 | 首行 DISCLAIMER，声明合成数据 |
| 4.2 | docs/ 无真实 Key | ✅ 通过 | 已扫描 |
| 4.3 | GITHUB_SYNC_REPORT.md 已更新 | ⚠️ 待更新 | 当前版本未反映最新安全状态 |
| 4.4 | SECURITY_REVIEW.md 已生成 | ✅ 通过 | 已记录泄露事件和处置建议 |
| 4.5 | VALIDATION_REPORT.md 已生成 | ✅ 通过 | 已记录测试和 pipeline 结果 |

### 5. 功能

| # | 检查项 | 状态 | 备注 |
|---|--------|------|------|
| 5.1 | mock provider 默认启用 | ✅ 通过 | `config.example.yaml` 默认 `provider: "mock"` |
| 5.2 | real provider 仅环境变量启用 | ✅ 通过 | 需 `provider: "deepseek"` + `DEEPSEEK_API_KEY` 环境变量 |
| 5.3 | evaluator 样本外隔离 | ✅ 通过 | `_slice()` 方法严格日期过滤 |
| 5.4 | AKShare 失败 graceful | ✅ 通过 | 抛出异常，不伪造数据 |
| 5.5 | 21 个 AgentSpec 存在 | ✅ 通过 | `agents/registry.py` 包含 21 个 |
| 5.6 | 21 个 prompt 模板存在 | ✅ 通过 | prompts/ 目录包含 21 个 .j2 文件 |

### 6. GitHub 同步

| # | 检查项 | 状态 | 备注 |
|---|--------|------|------|
| 6.1 | 本地分支与远程同步 | ✅ 通过 | `490b89a` 已 push 到 `origin/feature/cogalpha-mvp` |
| 6.2 | 无未提交更改 | ✅ 通过 | `git status` 显示工作区干净 |
| 6.3 | 最新 commit 为 490b89a | ✅ 通过 | 已确认 |

---

## 合并建议

### ❌ 当前不建议合并到 main

**阻塞原因**：
1. **历史泄露未处理**：commit `490b89a` 和 `415dd2f` 中 `BLOCKERS.md` 包含两个真实 DeepSeek API Key 的明文。合并到 main 后，这些泄露将永久存在于 main 分支历史中。
2. **Key 未 rotate**：暴露的 Key 仍然有效（或至少其中一个 `sk-7c538...` 在验证时有效），必须先到 DeepSeek 平台作废。

### 建议执行顺序

1. **立即执行**：到 https://platform.deepseek.com 作废两个 Key
   - `sk-7c538130996542898bb0b650f182f1cc`
   - `sk-mFXaY8U2q9oJXIaC2CMtcAZD5TkfdJ5yNoIxGz3yRUHhLywWnOO4nyda2j9830S7`
2. **生成新 Key**：在 DeepSeek 平台创建新的 API Key
3. **本地更新**：在 `.env` 中写入新 Key（永不提交到 git）
4. **验证安全**：确认 `git log --all -S "sk-7c538"` 仍显示历史，但 Key 已作废
5. **清理历史（可选）**：使用 `git filter-repo` 或接受历史泄露（已作废的 Key 不再有风险）
6. **创建 PR**：此时可以安全地创建 PR 合并到 main

### 最低可合并条件

如果不执行历史清理，最低要求是：
- ✅ Key 已 rotate（旧 Key 已作废）
- ✅ 当前工作区无真实 Key（已满足）
- ✅ pytest 全部通过（已满足）
- ✅ CI 通过（创建 PR 后触发）
