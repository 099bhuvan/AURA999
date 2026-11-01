# ==============================================================================
# AURA - Pure Python AI Personal Assistant (Cloud Streaming Dockerfile)
# Runs PySide6 Desktop GUI streaming live over WebRTC/noVNC
# ==============================================================================

FROM python:3.12-slim-bookworm

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV QT_QPA_PLATFORM=xcb

# Install system utilities, X11 virtual display, window manager, and complete Qt6 runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    openbox \
    novnc \
    websockify \
    libegl1 \
    libegl-mesa0 \
    libgl1 \
    libgl1-mesa-dri \
    libglx-mesa0 \
    libglib2.0-0 \
    libfontconfig1 \
    libfreetype6 \
    libxrender1 \
    libxi6 \
    libxcomposite1 \
    libxdamage1 \
    libxtst6 \
    libxrandr2 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxcb-xkb1 \
    libx11-xcb1 \
    libdbus-1-3 \
    libpulse0 \
    alsa-utils \
    espeak-ng \
    procps \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Ensure /tmp/.X11-unix exists with sticky bit for Xvfb sockets
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

# Standard non-root user (UID 1000) for security compliance
RUN useradd -m -u 1000 user
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /home/user/app

# Copy dependency definition and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY --chown=user:user . .

# Set permissions for startup script and storage
RUN chmod +x entrypoint.sh && \
    chown -R user:user /home/user

# Switch to standard non-root user
USER user

# Expose web streaming ports (7860 for Hugging Face Spaces, 10000 for Render)
EXPOSE 7860 10000

# Launch Xvfb, Openbox, noVNC web streaming, and AURA GUI
CMD ["bash", "entrypoint.sh"]
