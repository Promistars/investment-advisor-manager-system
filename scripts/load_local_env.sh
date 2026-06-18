#!/usr/bin/env bash
# 解析 IAMS 统一 conda 环境路径（默认环境名 IAMS，Python 与 npm 同源）
set -euo pipefail

_IAMS_LOAD_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_LOCAL_ENV="$_IAMS_LOAD_ROOT/config/local.env"

if [ -f "$_LOCAL_ENV" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$_LOCAL_ENV"
  set +a
fi

IAMS_CONDA_ENV="${IAMS_CONDA_ENV:-IAMS}"

_resolve_conda_base() {
  if command -v conda >/dev/null 2>&1; then
    _b="$(conda info --base 2>/dev/null || true)"
    if [ -n "$_b" ]; then
      echo "$_b"
      return
    fi
  fi
  if [ -n "${CONDA_BASE:-}" ]; then
    echo "$CONDA_BASE"
    return
  fi
  if [ -n "${CONDA_PREFIX:-}" ]; then
    case "$CONDA_PREFIX" in
      */envs/*) echo "${CONDA_PREFIX%/envs/*}" ;;
      */envs) echo "${CONDA_PREFIX%/envs}" ;;
      *) echo "$CONDA_PREFIX" ;;
    esac
  fi
}

_base="$(_resolve_conda_base)"
_env_bin=""

if [ -n "$_base" ] && [ -d "$_base/envs/$IAMS_CONDA_ENV/bin" ]; then
  _env_bin="$_base/envs/$IAMS_CONDA_ENV/bin"
fi

if [ -z "${CONDA_PYTHON:-}" ] && [ -n "$_env_bin" ] && [ -x "$_env_bin/python" ]; then
  CONDA_PYTHON="$_env_bin/python"
  export CONDA_PYTHON
fi

if [ -z "${CONDA_NODE:-}" ]; then
  if [ -n "$_env_bin" ] && [ -x "$_env_bin/npm" ]; then
    CONDA_NODE="$_env_bin"
    export CONDA_NODE
  elif [ -n "${CONDA_PYTHON:-}" ]; then
    CONDA_NODE="$(dirname "$CONDA_PYTHON")"
    export CONDA_NODE
  fi
fi

if [ -z "${CONDA_STREAMLIT:-}" ] && [ -n "$_env_bin" ] && [ -x "$_env_bin/streamlit" ]; then
  CONDA_STREAMLIT="$_env_bin/streamlit"
  export CONDA_STREAMLIT
fi

export CONDA_PYTHON="${CONDA_PYTHON:-python3}"
export CONDA_STREAMLIT="${CONDA_STREAMLIT:-streamlit}"
if [ -n "${CONDA_NODE:-}" ]; then
  export CONDA_NODE
fi

unset _IAMS_LOAD_ROOT _LOCAL_ENV _base _env_bin _resolve_conda_base
