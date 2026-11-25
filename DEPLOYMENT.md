# Deployment Guide – Anticipatory Commerce AI Platform

This repository is fully configured for production deployment across multiple environments.

---

## 🚀 Option 1: One-Click Streamlit Community Cloud (Recommended for fast demo)

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository:
   - **Repository:** `your-username/anticipatory-commerce`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Under **Advanced settings**, optionally add Secrets:
   ```toml
   REZOLVE_API_KEY = "your_actual_key"
   REZOLVE_KB_ID = "your_actual_kb_id"
   REZOLVE_API_BASE = "https://api.rezolvelabs.com/api/v1"
   ```
5. Click **Deploy!**

---

## 🐳 Option 2: Docker Container Deployment

### Local Docker Build & Run
```bash
# Build the Docker image
docker build -t anticipatory-commerce .

# Run the container on port 8501
docker run -d -p 8501:8501 --name anticipatory_app anticipatory-commerce
```

### Docker Compose
```bash
# Start with Docker Compose
docker-compose up -d

# Stop
docker-compose down
```

Access the application in your browser at `http://localhost:8501`.

---

## ☁️ Option 3: Cloud Platform Deployments

### Google Cloud Run
```bash
gcloud run deploy anticipatory-commerce \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8501
```

### AWS Elastic Beanstalk / ECS
- Deploy via the included `Dockerfile`.
- Map container port `8501` to host port `80/443`.

### Render / Railway / Heroku
- The included `Procfile` and `requirements.txt` are automatically detected.
- The app binds dynamically to the assigned `$PORT`.

---

## 💻 Local Windows Execution

Double-click `run_app.bat` or run:
```powershell
.\run_app.bat
```
or in PowerShell:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
