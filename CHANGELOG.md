# Changelog

## [2.1.3] — 2026-06-04

### 命名与文档

- 部署脚本重命名：`restart_web.sh`、`start_dev.sh`、`scripts/run_iams_web.sh`
- 文档与 CHANGELOG 去除旧版 UI 栈相关表述
- 删除本地 `pages/` 空目录残留

---

## [2.1.2] — 2026-06-04

- 合并 Python 依赖至根目录 `requirements.txt`
- 清理废弃 i18n 与客户链接文案；`clientLinkRedirect` 保留查询参数书签重定向
- CHANGELOG 仅保留当前产品线历史

---

## [2.1.1] — 2026-06-04

- 移除废弃 Python 单页 UI 代码与对照部署脚本
- 移除未使用 schema 与 Vite 脚手架资源
- 统一 conda 环境 `IAMS`（Python + Node）

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
