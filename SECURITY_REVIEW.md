# Security Review Report

> Date: 2026-06-19
> Repository: GK0421/cogalpha-factor-mining
> Branch: feature/cogalpha-mvp

## 1. 密钥扫描命令与结果

### 1.1 git grep 工作区扫描
```bash
git grep -n "sk-" -- .
```
**结果**：
- `BLOCKERS.md` 第20-21行：包含两个历史 Key 的明文（已修复为 REDACTED）
- `prompts/agent_21_lv7_fusion.j2` 第14行：仅为英文提示词文本（非密钥）
- `tests/test_config.py` 第31-33行：测试用占位 Key `sk-test123`（非真实密钥）

### 1.2 git log 全历史扫描
```bash
git log --all -p | grep -i "sk-"
git log --all -p | grep -i "DEEPSEEK"
git log --all --pretty=format:"%H %s" | grep -i "sk-"
```
**结果**：
- commit message 中 **无** sk- 前缀
- 但 `BLOCKERS.md` 的 diff 中出现了真实 Key 的明文

### 1.3 git pickaxe 深度扫描
```bash
git log --all -S "sk-7c538" --pretty=format:"%H %s"
# → 490b89a feat: integrate DeepSeek real LLM

git log --all -S "sk-mFXa" --pretty=format:"%H %s"
# → 415dd2f feat: add AKShare real data loader and DeepSeek config support
```

## 2. 发现的真实密钥泄露

| Key | 位置 | 状态 |
|-----|------|------|
| `sk-7c538130996542898bb0b650f182f1cc` | commit `490b89a` (BLOCKERS.md) | **已泄露到远程历史** |
| `sk-mFXaY8U2q9oJXIaC2CMtcAZD5TkfdJ5yNoIxGz3yRUHhLywWnOO4nyda2j9830S7` | commit `415dd2f` (BLOCKERS.md) | **已泄露到远程历史** |

**当前工作区状态**：已修复为 `sk-REDACTED`

## 3. 其他敏感文件检查

| 文件 | 在 .gitignore | 在 git 跟踪 | 是否含真实 Key |
|------|--------------|------------|---------------|
| `.env` | ✅ 是 | ❌ 否 | ❌ 已替换为占位符 |
| `config.yaml` | ✅ 是 | ❌ 否 | ❌ 使用 `${}` 占位符 |
| `*.key` | ✅ 是 | ❌ 否 | — |
| `results/` | ✅ 是 | ❌ 否 | — |
| `logs/` | ✅ 是 | ❌ 否 | — |
| `data/*.parquet` | ✅ 是 | ❌ 否 | — |

## 4. 泄露原因分析

1. **BLOCKERS.md 被意外写入真实 Key**：在调试过程中，将 API Key 明文写入了文档文件
2. **BLOCKERS.md 被提交到 git**：由于该文件在文档目录，未被 .gitignore 排除
3. **已 push 到 GitHub**：远程历史已包含泄露内容

## 5. 处置建议（必须执行）

### 5.1 立即执行：Rotate API Key

**两个 DeepSeek API Key 均已暴露，必须立即作废并重新生成。**

操作步骤：
1. 登录 https://platform.deepseek.com
2. 进入 API Keys 管理页面
3. 删除旧 Key `sk-7c538130996542898bb0b650f182f1cc` 和 `sk-mFXaY8U2q9oJXIaC2CMtcAZD5TkfdJ5yNoIxGz3yRUHhLywWnOO4nyda2j9830S7`
4. 生成新的 API Key
5. 更新本地 `.env` 文件中的 `DEEPSEEK_API_KEY`
6. **永远不要在任何文档、报告、commit message 中记录真实 Key**

### 5.2 可选：清理 git 历史

由于 Key 已 push 到 GitHub 公开仓库，即使本地重写历史，GitHub 的缓存中仍可能保留。建议：
- 使用 `git filter-repo` 清理历史（会改变所有 commit hash，影响协作）
- 或接受历史泄露的事实，重点确保新 Key 不再泄露

### 5.3 预防措施

1. 所有文档中提及 API Key 时使用 `sk-REDACTED` 或 `${DEEPSEEK_API_KEY}`
2. 在 CI 中增加密钥扫描（如 `git-secrets` 或 `truffleHog`）
3. 提交前运行 `git grep "sk-"` 检查

## 6. 结论

- ❌ **历史泄露**：两个真实 Key 已暴露于 git 历史
- ✅ **当前工作区**：已修复，无真实 Key 残留
- ⚠️ **必须动作**：到 DeepSeek 平台 rotate API Key
- ❌ **不建议立即合并 main**：历史泄露未清理，合并后泄露将永久存在于 main 分支

## 7. 再次验证命令

```bash
# 当前工作区验证（应无真实 Key）
git grep "sk-7c538" -- .
git grep "sk-mFXa" -- .
# 预期：无输出

# 历史验证（会显示泄露）
git log --all -S "sk-7c538" --pretty=format:"%H %s"
# 预期：显示 490b89a
```
