# 🌌 Nova Quant | 智能投顾与全周期资产管理中枢

![Version](https://img.shields.io/badge/Version-2.1.2-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![License](https://img.shields.io/badge/License-MIT-green)

> **"让代码处理繁琐，让大脑专注决策。"**
> 生产级私募/专户投资管理控制台。**FastAPI + React** 单端口部署（`/IAMS/`），内置业绩报酬核算、双口径价格引擎、三级行情容灾与客户只读大屏。

---

## ✨ 核心特性

- **高水位线业绩报酬引擎**：动态基数、双轨目标、溢出利润截断
- **前后台物理隔离**：投顾全量控制台 vs 客户只读大屏（`/client/{user}/{acc}`）
- **双擎价格基准**：图表前复权 + 交易结算不复权
- **全自动分红派息**：除权除息日自动入账/送股
- **三级容灾数据引擎**：新浪 → 东财 → BaoStock
- **产品 UI**：六宫格 KPI、ECharts 双图、交易录入台、持仓结构、操作全景图、雷达监控、Quill 寄语、流水编辑与中英双语

---

## 🚀 快速开始

### 1. 创建 conda 环境（推荐）

```bash
git clone https://github.com/Promistars/investment-advisor-manager-system.git
cd investment-advisor-manager-system

bash scripts/setup_conda_env.sh    # 创建 env「IAMS」：Python + Node + 全部依赖
conda activate IAMS
cd frontend && npm install && cd ..

cp .env.example .env               # 生产环境请修改 SECRET_KEY
bash restart_web2.sh                 # 默认 http://127.0.0.1:29996/IAMS/
```

开发模式（API :8000 + Vite :5173）：`bash start_web2.sh`

### 2. 数据抓取

```bash
conda activate IAMS
python auto_fetch.py
python -c "import auto_fetch; auto_fetch.fetch_data_now()"   # 立即补抓
```

### 3. 服务器长期部署

```bash
conda activate IAMS
bash setup_systemd.sh    # Web + 爬虫 + 每小时探活
bash restart_all.sh      # 日常重启
```

---

## 📂 目录结构

```text
├── environment.yml         # 统一 conda 环境（Python + Node + pip）
├── backend/                # FastAPI REST API
├── frontend/               # React + Vite + TypeScript + Tailwind + ECharts
├── portfolio_engine.py     # 统一绩效/持仓引擎
├── auto_fetch.py           # 定时增量抓取
├── stock_fetch.py          # 新浪/东财/BaoStock K 线
├── db_manager.py           # SQLite 用户与交易
├── restart_web2.sh         # 生产启动
├── config/network.env      # 项目代理策略（默认直连）
├── systemd/                # systemd 单元模板
├── financial_data/         # [本地] 个股 K 线
└── dividend_data/          # [本地] 分红事件
```

---

## 🔒 隐私与安全

以下内容**不会**提交到 GitHub：数据库（`*.db`）、本地配置 JSON、行情 CSV、`.env`、日志等。详见 `.gitignore`。

---

## 📜 版本

当前 **2.1.2** — 详见 [CHANGELOG.md](CHANGELOG.md)。

---

*"在不确定性中寻找确定性，在复利中见证时间的玫瑰。"*
