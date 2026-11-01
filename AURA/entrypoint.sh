#!/bin/bash
set -e

# Screen resolution configuration (can be overridden via environment variables)
export SCREEN_WIDTH=${SCREEN_WIDTH:-1280}
export SCREEN_HEIGHT=${SCREEN_HEIGHT:-800}
export SCREEN_DEPTH=24
export WEB_PORT=${PORT:-7860}
export LIBGL_ALWAYS_SOFTWARE=1
export QT_QPA_PLATFORM=xcb

# Clean up any stale X locks or sockets from previous container runs/restarts
rm -f /tmp/.X*-lock /tmp/.X11-unix/X* 2>/dev/null || true

# Find an available display number (default :99)
DISP_NUM=99
while [ -f "/tmp/.X${DISP_NUM}-lock" ] || [ -S "/tmp/.X11-unix/X${DISP_NUM}" ]; do
    if rm -f "/tmp/.X${DISP_NUM}-lock" "/tmp/.X11-unix/X${DISP_NUM}" 2>/dev/null; then
        break
    fi
    DISP_NUM=$((DISP_NUM + 1))
done

export DISPLAY=":${DISP_NUM}"

echo "=========================================================="
echo " Starting AURA Cloud Virtual Desktop"
echo " Display: $DISPLAY (${SCREEN_WIDTH}x${SCREEN_HEIGHT})"
echo " Web Port: $WEB_PORT"
echo "=========================================================="

# 1. Start Xvfb virtual framebuffer
echo "[1/5] Initializing Xvfb virtual display on $DISPLAY..."
Xvfb "$DISPLAY" -screen 0 "${SCREEN_WIDTH}x${SCREEN_HEIGHT}x${SCREEN_DEPTH}" -ac -nolisten tcp &
XVFB_PID=$!

# Wait for Xvfb socket to appear
for i in $(seq 1 30); do
    if [ -S "/tmp/.X11-unix/X${DISP_NUM}" ] || [ -f "/tmp/.X${DISP_NUM}-lock" ]; then
        echo "Xvfb is ready on $DISPLAY"
        break
    fi
    sleep 0.2
done
sleep 1

# 2. Start lightweight Openbox window manager
echo "[2/5] Starting Openbox window manager..."
openbox &
OPENBOX_PID=$!
sleep 1

# 3. Start x11vnc server
echo "[3/5] Starting x11vnc server on port 5900..."
x11vnc -display "$DISPLAY" -forever -nopw -shared -rfbport 5900 -bg -quiet -wait 5

# 4. Configure noVNC web streaming bridge
echo "[4/5] Setting up noVNC web streaming bridge on port $WEB_PORT..."
NOVNC_DIR="/usr/share/novnc"
WEB_DIR="/home/user/novnc_web"
mkdir -p "$WEB_DIR"

if [ -d "$NOVNC_DIR" ]; then
    cp -r "$NOVNC_DIR"/* "$WEB_DIR/" 2>/dev/null || true
fi

# Auto-connecting index.html
cat << 'EOF' > "$WEB_DIR/index.html"
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AURA Neural Command Center</title>
    <meta http-equiv="refresh" content="0; url=vnc.html?autoconnect=true&resize=remote&reconnect=true">
    <style>
        body { background: #04060a; color: #00f0ff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    </style>
</head>
<body>
    <h2>Initializing AURA Neural Interface...</h2>
</body>
</html>
EOF

websockify --web="$WEB_DIR" "$WEB_PORT" localhost:5900 &
WEBSOCKIFY_PID=$!
sleep 1

# 5. Launch AURA Assistant
echo "[5/5] Launching AURA Python AI Assistant..."
python3 main.py

# Cleanup on exit
kill $WEBSOCKIFY_PID $OPENBOX_PID $XVFB_PID 2>/dev/null || true
