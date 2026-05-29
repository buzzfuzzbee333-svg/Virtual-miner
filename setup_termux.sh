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
echo "  Android 11+:"
echo "    Settings → Developer Options → Wireless Debugging"
echo "    Tap 'Pair device with pairing code', note the IP:PORT and CODE"
echo "    Run: adb pair <IP>:<PORT>  (enter the pairing code when prompted)"
echo "    Then connect: adb connect localhost:5555"
echo ""
echo "  Android 10 and below:"
echo "    Settings → Developer Options → Enable USB Debugging"
echo "    Run: adb tcpip 5555"
echo "    Run: adb connect localhost:5555"
echo ""
read -p "  Press Enter once ADB is set up, or Ctrl+C to skip... "

adb connect localhost:5555 2>/dev/null \
  && echo "  [✓] ADB connected" \
  || echo "  [!] ADB connect failed — follow the steps above and reconnect manually"

# ── 4. Config file ────────────────────────────────────────────────────────────
echo ""
echo "[4/5] Creating config.json..."

if [ ! -f config.json ]; then
    cp config.example.json config.json
    echo "  [✓] config.json created from template"
    echo "  [!] Edit config.json and fill in:"
    echo "        agent.api_key         — your Anthropic API key (sk-ant-...)"
    echo "        fire_faucet.username  — FireFaucet.win username"
    echo "        fire_faucet.password  — FireFaucet.win password"
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
echo "║  1. Edit config.json (add API key + site credentials)        ║"
echo "║                                                              ║"
echo "║  2. Register tasks:                                          ║"
echo "║       python tasks/viefaucet.py                              ║"
echo "║       python tasks/solpick.py                                ║"
echo "║       python tasks/fire_faucet.py                            ║"
echo "║                                                              ║"
echo "║  3. Check everything:                                        ║"
echo "║       python main.py status                                  ║"
echo "║                                                              ║"
echo "║  4. Test one task manually:                                  ║"
echo "║       python main.py run viefaucet_sol_claim                 ║"
echo "║       python main.py run solpick_sol_claim                   ║"
echo "║                                                              ║"
echo "║  5. Start the scheduler:                                     ║"
echo "║       python main.py start                                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
