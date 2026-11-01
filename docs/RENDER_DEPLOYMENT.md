# ◈ Deploying AURA to Render (Cloud Web Service)

This guide walks you through deploying AURA on **[Render](https://render.com)** as a Docker Web Service. AURA runs inside a cloud container, rendering the PySide6 desktop GUI on a virtual X11 display, and streaming it directly to any web browser via noVNC.

---

## Prerequisites

1. A [Render account](https://dashboard.render.com/register).
2. A [GitHub](https://github.com) or [GitLab](https://gitlab.com) account.
3. An API key for an online AI provider (OpenAI `sk-...`, Groq `gsk_...`, or OpenRouter).

---

## Step 1: Push AURA to Your GitHub Repository

1. Create a new repository on GitHub (e.g. `AURA` or `aura-assistant`).
2. In your local AURA directory, initialize and push:

```powershell
cd c:\Users\Admin\Desktop\AURA

# Initialize git if not already done
git init
git add .
git commit -m "Configure AURA for Render cloud deployment"

# Set main branch and link your GitHub remote
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/AURA.git
git push -u origin main --force
```

---

## Step 2: Create a Web Service on Render

1. Log in to the [Render Dashboard](https://dashboard.render.com).
2. Click the **New +** button in the top navigation bar and select **Web Service**.
3. Under **Connect a repository**, search for and select your `AURA` GitHub repository.
4. Configure the service settings:
   - **Name**: `aura-assistant` (or your preferred name)
   - **Region**: Choose the region closest to you (e.g. `Oregon (US West)`, `Frankfurt (EU)`)
   - **Branch**: `main`
   - **Runtime**: **Docker** *(Render automatically detects the root `Dockerfile`)*
   - **Instance Type**:
     - **Starter** ($7/mo • 1 GB RAM • 0.5 CPU) — *(Recommended for smooth 60 FPS streaming and zero spin-down)*
     - **Free** (512 MB RAM) — *(Works for basic testing; recommend setting `REDUCED_MOTION=true`)*

---

## Step 3: Configure Environment Variables on Render

In the **Environment Variables** section on the same setup page (or under the **Environment** tab later):

Click **Add Environment Variable** for each:

| Key | Recommended Value | Description |
|---|---|---|
| `PORT` | `10000` | Port Render routes web traffic to *(automatic)* |
| `AI_DEFAULT_MODE` | `online` | Forces online cloud AI routing |
| `ONLINE_API_KEY` | `sk-...` *(your key)* | Your OpenAI, Groq, or OpenRouter API key |
| `ONLINE_MODEL_NAME` | `gpt-4o-mini` | AI model name (or `llama-3.3-70b-versatile`) |
| `ONLINE_API_BASE_URL` | `https://api.openai.com/v1` | Provider API base URL (or `https://api.groq.com/openai/v1`) |
| `REDUCED_MOTION` | `false` | Set to `true` if using the 512MB Free Tier |

---

## Step 4: Deploy & Access

1. Click **Deploy Web Service** at the bottom.
2. Render will pull your repository, build the Docker image, and run `entrypoint.sh`.
   - The build process takes approximately 2–3 minutes.
3. Once the deployment logs show:
   ```
   [1/5] Initializing Xvfb virtual display on :99...
   [2/5] Starting Openbox window manager...
   [3/5] Starting x11vnc server on port 5900...
   [4/5] Setting up noVNC web streaming bridge on port 10000...
   [5/5] Launching AURA Python AI Assistant...
   ```
4. Click your Render application URL at the top of the dashboard:
   ```
   https://aura-assistant.onrender.com
   ```
5. Your browser will instantly open the live, interactive cinematic AURA interface.

---

## Tips for Render Deployment

- **Port Binding**: Render automatically passes `$PORT` (default `10000`). Our `entrypoint.sh` automatically reads `${PORT:-7860}`, so it binds seamlessly on Render without manual port forwarding.
- **Free Tier Sleep**: On the Free tier, Render puts web services to sleep after 15 minutes of inactivity. The first visit after sleep will take ~50 seconds to wake up.
- **Using Free Groq Models**: For ultra-fast and free online inference, set:
  - `ONLINE_API_BASE_URL`: `https://api.groq.com/openai/v1`
  - `ONLINE_MODEL_NAME`: `llama-3.3-70b-versatile`
  - `ONLINE_API_KEY`: your free key from [console.groq.com](https://console.groq.com)
