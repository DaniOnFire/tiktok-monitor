#!/bin/bash
# Aggiorna pip e installa Playwright
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Installa Chromium per Playwright
python3 -m playwright install chromium

# Avvia il bot
python3 monitor.py
