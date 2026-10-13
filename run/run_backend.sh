#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python backend/wsgi.py
