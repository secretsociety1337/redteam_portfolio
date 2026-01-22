#!/usr/bin/env bash

set -e

echo "[*] Detecting OS..."

if [ -f /etc/debian_version ]; then
    echo "[+] Debian-based OS detected (Kali/Ubuntu)"

    echo "[*] Updating system..."
    sudo apt update && sudo apt upgrade -y

    echo "[*] Installing system dependencies..."
    sudo apt install -y \
        python3 \
        python3-venv \
        python3-cryptography \
        python3-pynput

    echo "[*] Creating Python virtual environment..."
    python3 -m venv venv

    echo "[*] Activating virtual environment..."
    source venv/bin/activate

    echo "[*] Upgrading pip inside venv..."
    pip install --upgrade pip

    echo "[*] Installing Python-only dependencies..."
    pip install mss

    echo "[+] Installation complete!"
    echo "[!] Activate the environment before running:"
    echo "    source venv/bin/activate"

elif [ -f /etc/arch-release ]; then
    echo "[+] Arch-based OS detected"

    echo "[*] Updating system..."
    sudo pacman -Syu --noconfirm

    echo "[*] Installing dependencies..."
    sudo pacman -S --noconfirm \
        python \
        python-mss \
        python-cryptography \
        python-pynput

    echo "[+] Installation complete!"

else
    echo "[-] Unsupported OS"
    exit 1
fi
