#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:${PYTHONPATH:-}"

python -m gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind=0.0.0.0:${PORT:-8000}
