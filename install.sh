#!/bin/bash

# 1. Update system
echo "Updating system packages..."
sudo apt update -y && sudo apt upgrade -y

# 2. Install required packages
echo "Installing dependencies for Chrome + Selenium..."
sudo apt install -y wget curl unzip fontconfig libfontconfig1 libjpeg-turbo8 \
    libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 xfonts-75dpi xfonts-base \
    libappindicator3-1 libnss3 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 \
    libgbm1 libasound2 fonts-liberation libu2f-udev libvulkan1 \
    python3 python3-pip python3-venv

# 3. Install Google Chrome
echo "Installing Google Chrome Stable..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt-get install -f -y
rm -f google-chrome-stable_current_amd64.deb

echo "Chrome installed:"
google-chrome --version

# 4. Setup Python Virtual Environment
echo "Creating Python virtual environment..."
cd ~ || exit 1
python3 -m venv ~/botenv
source ~/botenv/bin/activate

# 5. Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install python-telegram-bot==21.* undetected-chromedriver selenium
