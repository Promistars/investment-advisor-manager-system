# Changelog

## [2.1.2] — 2026-06-04

### 仓库精简

- 合并 `backend/requirements.txt` → 根目录 `requirements.txt`
- 移除 CHANGELOG 中 v1.x 历史（GitHub 仅保留 v2 当前线）
- 清理 Streamlit / v1 相关 i18n 与客户链接文案
- `legacyClientUrl` 重命名为 `clientLinkRedirect`（仅保留旧书签重定向）
- 移除 `main.py` 中非核心的 palette-studio 挂载

---

## [2.1.1] — 2026-06-04

### 清理与精简

- 移除 Streamlit 1.x 遗留代码（`app.py`、`pages/`、`iams_*` 模块及对照部署脚本）
- 移除未使用的 `backend/app/schemas.py`、Vite 脚手架资源
- `requirements.txt` 仅保留领域层与 API 依赖
- 统一 conda 环境 `IAMS`（Python + Node）
- 绩效引擎缓存版本号升至 2.1.1

---

## [2.1.0] — 2026-06-04

- 交易录入「标的」可检索下拉；股票抓取交互反馈；Analytics 吸顶标题
- 账户大厅累计管理费与分账户明细
- 修复 `list_accounts` DataFrame 500 错误
- 新增 `environment.yml` 与 `scripts/setup_conda_env.sh`

---

## [2.0.0] — 2026-06-04

- **架构**：FastAPI + React 单端口部署（`/IAMS/`）
- **功能**：登录/大厅/看板/流水/Quill 寄语/客户链接/高水位结算/雷达监控/中英双语
