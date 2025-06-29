# UAV Log Viewer

An interactive web application for visualising ArduPilot **MAVLink** and **DataFlash** logs.

---

## 🔑 Environment variables

Create a `.env` file in the project root and provide **either** an OpenAI or a Mistral API key, plus your Cesium ion access token:

```env
# choose **one** of the AI providers
OPENAI_API_KEY=your_openai_key_here
# or
MISTRAL_API_KEY=your_mistral_key_here

# Cesium ion token for 3‑D globe and terrain tiles
VUE_APP_CESIUM_TOKEN=your_cesium_token_here
```

## 📦 Quick Start (Docker Compose)

> These steps assume Docker ≥ 20.10 and Docker Compose v2 are installed.

```bash
# 1 ‒ Clone the repository (main branch)
git clone --branch main https://github.com/ashishsimonharrison/UAVLogViewer.git

# 2 ‒ Move into the project root
cd UAVLogViewer

# 3 ‒ Build the backend and frontend images
docker-compose build

# 4 ‒ Start the stack (Ctrl‑C to stop)
docker-compose up
```

Once both containers report **“Up”** you can open:

* **Frontend** → [http://localhost:8080](http://localhost:8080)

The frontend proxies its API calls to the backend automatically when running through Docker.

---

## 🗺️ Project Structure (excerpt)

```
UAVLogViewer/
├── backend/        # FastAPI server (log parsing & upload endpoints)
├── docker-compose.yml
└── README.md
```

## 📜 License

This project is licensed under the terms of the original UAV Log Viewer upstream licence.
