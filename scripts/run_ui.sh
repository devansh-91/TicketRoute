#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec streamlit run app.py --server.port 8501 --server.address 0.0.0.0
