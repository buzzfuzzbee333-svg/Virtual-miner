#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# Virtual Miner — Termux Setup Script
# Run this once inside Termux to get everything installed and connected.
# =============================================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║       Virtual Miner — Termux Setup           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. System packages ────────────────────────────────────────────────────────
echo "[1/5] Installing system packages..."
pkg update -y -q
pkg install -y python android-tools git

# ── 2. Python dependencies ────────────────────────────────────────────────────
echo ""
echo "[2/5] Installing Python packages..."
pip install --quiet httpx

# ── 3. ADB connection ─────────────────────────────────────────────────────────
echo ""
echo "[3/5] Setting up ADB (wireless)..."
echo ""
echo "  To connect ADB to this device:"
echo ""
echo "  Android 11+:"
echo "    Settings → Developer Options → Wireless Debugging"
echo "    Tap 'Pair device with pairing code', note the IP:PORT and CODE"
echo "    Then run: adb pair <IP>:<PORT>"
echo "    Enter the pairing code when prompted."
echo "    Then connect: adb connect localhost:5555"
echo ""
echo "  Android 10 and below:"
echo "    Settings → Developer Options → Enable USB Debugging"
echo "    Run: adb tcpip 5555"
echo "    Run: adb connect localhost:5555"
echo ""
read -p "  Press Enter once you've set up ADB, or Ctrl+C to skip... "

# Try connecting to localhost
adb connect localhost:5555 2>/dev/null && echo "  [✓] ADB connected" || echo "  [!] ADB connect failed — check steps above"

# ── 4. Config file ────────────────────────────────────────────────────────────
echo ""
echo "[4/5] Creating config.json..."

if [ ! -f config.json ]; then
    cp config.example.json config.json
    echo "  [✓] config.json created from template"
    echo "  [!] Edit config.json and add your credentials before running tasks"
else
    echo "  [·] config.json already exists — skipping"
fi

# ── 5. Smoke test ─────────────────────────────────────────────────────────────
echo ""
echo "[5/5] Running smoke test..."
python -c "
import sys, sqlite3, httpx, asyncio
print('  Python  :', sys.version.split()[0])
print('  SQLite  :', sqlite3.sqlite_version)
print('  httpx   :', httpx.__version__)
print('  asyncio : ok')
" && echo "  [✓] All imports OK"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Setup complete! Next steps:                                 ║"
echo "║                                                              ║"
echo "║  1. Edit config.json with your Fire Faucet credentials       ║"
echo "║  2. Register the task:                                       ║"
echo "║       python tasks/fire_faucet.py                            ║"
echo "║  3. Check everything looks right:                            ║"
echo "║       python main.py status                                  ║"
echo "║  4. Test-run the task once:                                  ║"
echo "║       python main.py run fire_faucet_claim                   ║"
echo "║  5. Start the scheduler:                                     ║"
echo "║       python main.py start                                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
