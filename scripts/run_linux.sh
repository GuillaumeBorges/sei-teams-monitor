#!/usr/bin/env bash
# Garante que o script roda a partir da pasta do projeto, não importa de
# onde o cron dispare. Aponte a entrada do crontab para ESTE arquivo.
DIR_PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR_PROJETO" || exit 1
/home/borges/.pyenv/versions/3.12.3/bin/python3 sei_monitor.py >> scripts/run_linux.log 2>&1
