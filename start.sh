#!/bin/bash

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies in isolated environment
pip install --no-cache-dir -r requirements.txt

# Run the bot
python bot.py
