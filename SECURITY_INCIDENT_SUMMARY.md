# Security Incident Summary

> Date: 2026-06-19
> Repository: GK0421/cogalpha-factor-mining (old/polluted)
> Incident: API Key historical exposure in git history

## 1. 事件概述

本项目的旧仓库（`cogalpha-factor-mining`）在开发过程中，两个 DeepSeek API Key 被意外写入 `BLOCKERS.md` 文件并提交到 git 历史，随后推送到公开 GitHub 仓库。事件已确认，当前工作区已 redacted，但历史泄露无法撤销。

## 2. 泄露详情

| Key | 暴露位置 | 暴露范围 |
|-----|----------|----------|
| `sk-REDACTED` | commit `490b89a` (BLOCKERS.md) | GitHub 公开仓库历史 |
| `sk-REDACTED` | commit `415dd2f` (BLOCKERS.md) | GitHub 公开仓库历史 |

**注意**：出于安全，本报告中 Key 的具体值已用 REDACTED 替换。实际的泄露值已记录于安全审查记录中，不在此文件重复。

## 3. 泄露原因

1. 调试过程中，将 API Key 明文写入 `BLOCKERS.md` 文档文件
2. `BLOCKERS.md` 不在 `.gitignore` 中，被意外提交
3. 已 push 到公开 GitHub 仓库，进入不可撤销的历史

## 4. 已采取的措施

- ✅ 当前工作区中所有 Key 已替换为 `sk-REDACTED`
- ✅ `.env` 和 `config.yaml` 已排除在版本控制外
- ✅ 已创建干净的新仓库：`cogalpha-factor-mining-clean`（私有）
- ✅ 新仓库已重新初始化 git，不继承旧历史
- ✅ 新仓库已通过全局密钥扫描，确认无泄露

## 5. 用户必须手动完成的动作

### 5.1 立即执行：作废旧 Key

1. 登录 https://platform.deepseek.com
2. 进入 API Keys 管理页面
3. 删除/禁用以下两个 Key（旧仓库历史中暴露的 Key）
4. 检查账户调用量和账单，确认无异常请求

### 5.2 生成新 Key

1. 在 DeepSeek 控制台生成新的 API Key
2. 仅写入本地 `.env` 文件：
   ```bash
   DEEPSEEK_API_KEY=新Key
   ```
3. **不得**将新 Key 写入任何文档、报告、commit message、Markdown 文件

### 5.3 旧仓库处置建议

- 将旧仓库设为 Private：仓库 Settings → Change visibility → Private
- 或归档：仓库 Settings → Archive this repository
- 或删除（如果不再需要旧历史）

## 6. 新仓库信息

- **新仓库地址**：https://github.com/GK0421/cogalpha-factor-mining-clean
- **新仓库状态**：私有，无历史泄露，仅含一个干净初始 commit
- **迁移方式**：源码重新导出，排除敏感文件，重新初始化 git

## 7. 预防措施

1. 永远不要在任何文档、报告、commit message 中记录真实 API Key
2. 所有 API Key 仅通过 `.env` 文件或环境变量注入
3. 提交前运行 `git grep "sk-"` 检查
4. 在 CI 中增加密钥扫描（如 truffleHog、git-secrets）
5. `.gitignore` 必须包含 `.env`、`config.yaml`、`*.key`

## 8. 结论

旧仓库已发生不可逆的历史泄露，不建议继续使用。新项目开发请使用干净的新仓库，并严格遵守 Key 管理规范。
