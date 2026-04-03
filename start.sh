#!/bin/bash
python3 -m pip install --upgrade pip
python3 -m pip install playwright
python3 -m playwright install chromium
python3 monitor.py
