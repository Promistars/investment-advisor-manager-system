#!/usr/bin/env bash
PORT="${STREAMLIT_PORT:-29998}"
echo "Stopping Streamlit on port $PORT ..."
ps -ef | grep "[s]treamlit run app.py" | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
echo "Done."
