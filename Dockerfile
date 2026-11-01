# ==============================================================================
# AURA - Tactical AI Neural Command Center (Cloud Web Service)
# Direct FastAPI + HTML5/CSS3/Canvas Web Server for Render & Cloud Hosting
# ==============================================================================

FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install essential system packages for Python extensions and healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

USER user

# Render web service port
EXPOSE 10000

# Start AURA Web Command Center
CMD ["python3", "web_app.py"]
