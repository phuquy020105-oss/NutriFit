#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
printf "Dependencies installed. Configure .env and read README.md for database steps.
"
