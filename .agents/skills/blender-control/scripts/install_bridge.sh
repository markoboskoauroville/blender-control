#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE_SRC="$SCRIPT_DIR/blender_control_bridge.py"
CLI_SCRIPT="$SCRIPT_DIR/blender_cli.py"

BLENDER_BIN="${BLENDER_BIN:-/Applications/Blender.app/Contents/MacOS/Blender}"
BLENDER_USER_STARTUP="$HOME/Library/Application Support/Blender/5.2/scripts/startup"

mkdir -p "$BLENDER_USER_STARTUP"
cp "$BRIDGE_SRC" "$BLENDER_USER_STARTUP/blender_control_bridge.py"
echo "Installed bridge -> $BLENDER_USER_STARTUP/blender_control_bridge.py"

# Check if bridge is already responding
if python3 "$CLI_SCRIPT" ping >/dev/null 2>&1; then
  echo "Live Blender bridge is already active:"
  python3 "$CLI_SCRIPT" ping
  exit 0
fi

# Check if Blender GUI is currently running without the bridge loaded
BLENDER_PID="$(pgrep -f '/Applications/Blender.app/Contents/MacOS/Blender' | head -n 1 || true)"
if [ -n "$BLENDER_PID" ]; then
  OPEN_BLEND="$(lsof -p "$BLENDER_PID" 2>/dev/null | grep '\.blend$' | grep -v 'userpref\.blend' || true)"
  if [ -z "$OPEN_BLEND" ]; then
    echo "Restarting untouched Blender instance (PID $BLENDER_PID) to activate startup bridge..."
    osascript -e 'tell application "Blender" to quit' >/dev/null 2>&1 || kill "$BLENDER_PID" || true
    for _ in $(seq 1 20); do
      if ! kill -0 "$BLENDER_PID" 2>/dev/null; then
        break
      fi
      sleep 0.2
    done
  else
    echo "WARNING: Blender (PID $BLENDER_PID) has an open .blend file:"
    echo "  $OPEN_BLEND"
    echo "In Blender's top menu bar, click: Blender -> System -> Reload Scripts"
    exit 1
  fi
fi

echo "Launching Blender.app in background focus mode..."
open -g -a Blender

for _ in $(seq 1 40); do
  if python3 "$CLI_SCRIPT" ping >/dev/null 2>&1; then
    echo "Connected to live Blender GUI:"
    python3 "$CLI_SCRIPT" ping
    exit 0
  fi
  sleep 0.25
done

echo "ERROR: Timed out waiting for Blender Control Bridge on 127.0.0.1:9876" >&2
exit 1
