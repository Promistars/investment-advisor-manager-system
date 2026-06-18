#!/usr/bin/env bash
# 一键创建/更新 IAMS conda 环境（Python + Node + 全部 pip 依赖）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v conda >/dev/null 2>&1; then
  echo "❌ 未找到 conda。请先安装 Miniconda / Anaconda："
  echo "   https://docs.conda.io/en/latest/miniconda.html"
  exit 1
fi

ENV_NAME="${IAMS_CONDA_ENV:-IAMS}"

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "📦 更新 conda 环境: $ENV_NAME"
  conda env update -n "$ENV_NAME" -f environment.yml --prune
else
  echo "📦 创建 conda 环境: $ENV_NAME"
  conda env create -f environment.yml
fi

echo ""
echo "✅ 环境就绪。后续步骤："
echo "   conda activate $ENV_NAME"
echo "   cd frontend && npm install && cd .."
echo "   bash restart_web2.sh"
echo ""
echo "💡 可选：cp config/local.env.example config/local.env 并按本机修改 CONDA_BASE"
