#!/bin/bash
echo "Starting Eren Stresser Bot with Persistent Chrome..."

# Kill old Chrome instances
pkill -f chrome 2>/dev/null
sleep 2

# Start Chrome with Remote Debugging Port
echo " Launching Chrome on port 9222..."
google-chrome \
    --remote-debugging-port=9222 \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-blink-features=AutomationControlled \
    --window-size=1366,768 \
    --user-data-dir="/root/chrome_profile" \
    https://return.st/panel &

echo "⏳ Waiting for Chrome to start (10 seconds)..."
sleep 10

echo "Starting Telegram Bot (Connecting to Chrome on port 9222)..."
python3 stresser_bot.py
