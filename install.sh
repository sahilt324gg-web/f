#!/bin/bash
echo " Starting Stresser Bot with Persistent Chrome..."

# Kill any existing Chrome instances
pkill -f chrome 2>/dev/null
sleep 2

# Start Chrome with Remote Debugging (Persistent Browser)
echo " Launching Chrome on port 9222..."
google-chrome \
    --remote-debugging-port=9222 \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --window-size=1280,1024 \
    --user-data-dir="/root/chrome_profile" \
    --disable-blink-features=AutomationControlled \
    https://return.st/panel &

# Wait for Chrome to fully start
echo " Waiting for Chrome to initialize (8 seconds)..."
sleep 8

# Run the Python bot
echo "🤖 Starting Telegram Bot..."
python3 stresser_bot.py
