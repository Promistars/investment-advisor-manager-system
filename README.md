# 🌌 Nova Quant | 智能投顾与全周期资产管理中枢

![Version](https://img.shields.io/badge/Version-2.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react)
![License](https://img.shields.io/badge/License-MIT-green)

> **"让代码处理繁琐，让大脑专注决策。"**
> 本项目是一个基于 Python 的**生产级私募/专户投资管理控制台**。v2 采用 **FastAPI + React** 产品级架构（单端口部署），并保留 Streamlit 1.x 遗留入口便于对照。系统内置业绩报酬核算引擎，融合自动化除权息处理、双口径价格引擎与客户视角大屏展示，以及严密的「管理端/客户端」双视角物理隔离。

---

## ✨ 核心特性

- **高水位线业绩报酬引擎**：动态基数、双轨目标、溢出利润截断
- **前后台物理隔离**：投顾全量控制台 vs 客户只读大屏（`/client/{user}/{acc}`）
- **双擎价格基准**：图表前复权 + 交易结算不复权
- **全自动分红派息**：除权除息日自动入账/送股
- **三级容灾数据引擎**：新浪 → 东财 → BaoStock，项目级 `config/network.env` 网络策略
- **v2 产品 UI**：六宫格 KPI、ECharts 双图、交易录入台、持仓结构、操作全景图、雷达监控、Quill 寄语、流水编辑与中英双语

---

## 🚀 快速开始（v2 推荐）

### 1. 创建统一 conda 环境（推荐）

本项目使用 **单个 conda 环境** 隔离 Python 后端、Node 前端构建与 Streamlit 遗留入口。

前置：已安装 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda。

```bash
git clone https://github.com/Promistars/investment-advisor-manager-system.git
cd investment-advisor-manager-system

# 创建/更新环境 IAMS（含 Python 3.10+、Node 20+、全部 pip 依赖）
bash scripts/setup_conda_env.sh

conda activate IAMS
cd frontend && npm install && cd ..

# 可选：生产密钥
cp .env.example .env

# 构建前端并单端口启动（默认 29996，挂载 /IAMS/）
bash restart_web2.sh
```

浏览器访问：`http://127.0.0.1:29996/IAMS/`

> 部署脚本会自动在 `conda env list` 中查找名为 **IAMS** 的环境；若 conda 安装路径非常规，可复制 `config/local.env.example` → `config/local.env` 并设置 `CONDA_BASE`。

开发模式（API :8000 + Vite :5173）：

```bash
conda activate IAMS
bash start_web2.sh
```

### 2. 不用 conda 时（备选）

```bash
pip install -r requirements.txt
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
bash restart_web2.sh
```

### 数据抓取

```bash
python auto_fetch.py          # 后台调度（每日 18:00）
python -c "import auto_fetch; auto_fetch.fetch_data_now()"  # 立即补抓
```

### 服务器长期部署

```bash
# 安装 systemd 用户服务（Web + 爬虫 + 每小时探活）
# 可按本机设置 CONDA_PYTHON / CONDA_NODE 后再执行
bash setup_systemd.sh

# 日常重启
bash restart_all.sh
```

---

## 📂 目录结构

```text
├── environment.yml         # 统一 conda 环境定义（Python + Node + pip）
├── scripts/setup_conda_env.sh
├── backend/                # FastAPI REST API
├── frontend/               # React + Vite + TypeScript + Tailwind + ECharts
├── app.py                  # Streamlit 遗留入口（可选对照）
├── pages/analytics.py      # Streamlit 看板逻辑（遗留）
├── portfolio_engine.py     # 统一绩效/持仓引擎
├── auto_fetch.py           # 定时增量抓取
├── stock_fetch.py          # 新浪/东财/BaoStock K 线
├── db_manager.py           # SQLite 用户与交易
├── restart_web2.sh         # v2 生产启动（推荐）
├── start_web2.sh           # v2 开发启动
├── config/network.env      # 项目代理策略（默认直连）
├── config/local.env.example # 本机 conda 路径可选覆盖
├── systemd/                # systemd 单元模板（@IAMS_ROOT@ 占位符）
├── financial_data/         # [本地生成，不入库] 个股 K 线
├── dividend_data/          # [本地生成，不入库] 分红事件
└── .gitignore              # 数据库 / JSON 配置 / CSV 隔离
```

---

## 🔒 隐私与安全

以下内容**不会**提交到 GitHub（见 `.gitignore`）：

| 类型 | 示例 |
|------|------|
| 数据库 | `*.db`（用户、密码、交易流水） |
| 本地配置 | `account_config.json`、`user_prefs.json`、`commentaries.json`、`stock_config.json` |
| 行情数据 | `financial_data/`、`dividend_data/`、`*.csv` |
| 机密 | `.env`、`secrets.toml`、本地日志 |

首次部署请自行注册账户；生产环境务必在 `.env` 中设置 `IAMS_SECRET_KEY`。

---

## 📜 版本记录

详见 [CHANGELOG.md](CHANGELOG.md)。当前版本：**2.1.0**（`VERSION` 文件）。

Streamlit 临时对照（本地 only）：

```bash
bash restart_streamlit_temp.sh   # 默认 localhost:29998
```

---

*"在不确定性中寻找确定性，在复利中见证时间的玫瑰。"*
