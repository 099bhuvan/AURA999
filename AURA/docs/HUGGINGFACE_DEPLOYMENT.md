# ◈ Deploying AURA to Hugging Face Spaces (Free Cloud Hosting)

This guide walks you through hosting AURA on **Hugging Face Spaces** for free. AURA will run inside a cloud Linux container and stream its complete, interactive PySide6 graphical interface directly to your web browser via noVNC/WebRTC.

---

## Prerequisites

1. A free account on [Hugging Face](https://huggingface.co/join).
2. Git installed on your local computer (or you can upload files directly via the Hugging Face web UI).
3. *(Optional)* An API key for an online model provider (e.g. OpenAI, Groq, OpenRouter, or Gemini).

---

## Step 1: Create a New Space on Hugging Face

1. Log in to [Hugging Face](https://huggingface.co).
2. Click on your profile picture in the top-right corner and select **New Space** (or navigate to [huggingface.co/new-space](https://huggingface.co/new-space)).
3. Fill in the Space settings:
   - **Space Name**: `aura-assistant` (or any custom name)
   - **License**: `mit` (or choose your preferred license)
   - **Select the Space SDK**: Click **Docker** 🐳
   - **Choose a Docker template**: Select **Blank**
   - **Space Hardware**: Free (**CPU basic • 2 vCPU • 16 GB RAM**)
   - **Privacy**: **Public** (or **Private** if you want it visible only to you)
4. Click **Create Space**.

---

## Step 2: Push AURA Code to Your Space

You can push the codebase using Git:

### Option A: Via Git Command Line

In your local AURA folder:

```powershell
cd c:\Users\Admin\Desktop\AURA

# Initialize git if not already initialized
git init
git add .
git commit -m "Deploy AURA to Hugging Face Spaces"

# Add your Hugging Face Space as a remote (replace USERNAME and SPACE-NAME)
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/aura-assistant

# Push to Hugging Face (you will be prompted for your HF username and Access Token)
git branch -M main
git push -u space main --force
```

> **Note on HF Access Token**: When prompted for a password, use a Hugging Face **Access Token** with `write` permissions from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

### Option B: Via Web UI
1. In your newly created Space, click **Files** tab.
2. Drag and drop all project files into the browser (ensure `Dockerfile` and `entrypoint.sh` are at the repository root).
3. Click **Commit changes to main**.

---

## Step 3: Configure Environment Variables & Secrets

Because Hugging Face cloud containers do not run a local Ollama daemon by default, configure an online AI provider:

1. In your Space, navigate to the **Settings** tab.
2. Scroll down to **Variables and secrets**.
3. Under **Secrets**, click **New secret**:
   - Name: `ONLINE_API_KEY`
   - Value: `your_api_key_here` (e.g. OpenAI `sk-...`, Groq `gsk_...`, or OpenRouter)
4. Under **Variables**, click **New variable**:
   - Name: `AI_DEFAULT_MODE`
   - Value: `online`
5. *(Optional)* If using a provider other than standard OpenAI:
   - Variable `ONLINE_API_BASE_URL`: e.g. `https://api.groq.com/openai/v1`
   - Variable `ONLINE_MODEL_NAME`: e.g. `llama-3.3-70b-versatile`

---

## Step 4: Access Your Live Assistant

1. Hugging Face will automatically detect the `Dockerfile`, build the container, and start the services.
2. Once the build finishes (typically 2-3 minutes), the status badge will switch to **Running**.
3. In the **App** tab of your Space, the noVNC client will connect and render AURA's live desktop interface!
4. You can click, type, manage sessions, upload documents, and interact with the animated core directly inside your browser from any PC, Mac, iPad, or mobile phone.

---

## Tips & Troubleshooting

- **Display Scaling**: The noVNC bridge is set to `resize=remote`, which automatically scales the display resolution to your browser window. You can also customize screen dimensions by setting the `SCREEN_WIDTH` (default `1280`) and `SCREEN_HEIGHT` (default `800`) environment variables in your Space settings.
- **Audio in Browser**: In browser-streamed VNC environments, microphone access is handled via the built-in text-only fallback command bar on the Voice page.
- **Persistent Storage**: Data stored in `/home/user/.aura` persists while the Space is awake. For enterprise persistence, you can link a persistent storage disk in Hugging Face Space settings.
