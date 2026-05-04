# Free C/C++/Java Compiler

This project is a simple web-based compiler (C, C++, Java) built with FastAPI and a vanilla frontend. It includes a Dockerfile and a Render blueprint for easy deployment.

Quick structure:

- `frontend/` — static frontend (`index.html`, `styles.css`, `app.js`) served from the backend
- `backend/` — FastAPI app, `backend/app/main.py`, `backend/Dockerfile`, and `backend/requirements.txt`

Deploy to Render (recommended)
1. Push code to GitHub (already done).
2. Go to https://render.com and create a new Web Service.
3. Choose your GitHub repo `Aatif05-it/Compiler` and branch `main`.
4. For **Environment**, choose **Docker**.
5. Set the **Dockerfile path** to `backend/Dockerfile`.
6. Set the **Health Check Path** to `/health` and enable **Auto Deploy**.
7. Deploy — Render will build and run the container. The service exposes dynamic `PORT` automatically.

Local testing (VS Code)
1. From the repository root, install dependencies into a virtualenv and activate it.

```powershell
python -m venv .venv
. .venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. Run the backend locally (it serves the frontend static files):

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

3. Open http://127.0.0.1:8000 in your browser.

Notes
- For real compilation (non-demo) in Render, the Docker image installs `gcc`, `g++`, and `default-jdk-headless`.
- If you want Vercel for the frontend only, deploy the `frontend/` folder separately and point the API calls to the Render service URL.
# Free C/C++/Java Compiler (Deployable)

A web app that compiles and runs user code in:
- C (`gcc`)
- C++ (`g++`)
- Java (`javac` + `java`)

Built with FastAPI + vanilla frontend and packaged with Docker.

## 1) Run Locally (No Cost)

### With Docker (recommended)

```bash
docker build -t compiler-lab .
docker run --rm -p 8000:8000 compiler-lab
```

Open: `http://localhost:8000`

### Without Docker (if toolchains already installed)

Install Python deps:

```bash
pip install -r requirements.txt
```

Run server:

```bash
uvicorn app.main:app --reload
```

## 2) Free Deployment Options

## Option A: Render (easy)

1. Push this project to GitHub.
2. Go to Render and create a **Blueprint** deployment from your repo.
3. Render reads `render.yaml` and deploys this Docker service.
4. Wait for the service health check to pass on `/health`.
5. Open your Render URL.

Important for Render:
- This project now starts with `--port ${PORT:-8000}` so it works with Render's assigned port.
- If deployment fails, check Render logs for startup errors and confirm the service is running (not sleeping).

## Option B: Railway / Fly.io

Both can deploy from this `Dockerfile` directly.
- Create a new app from GitHub repo.
- Select Docker deployment.
- Expose port `8000`.

## API

POST `/api/run`

Request body:

```json
{
  "language": "c",
  "code": "#include <stdio.h>\nint main(){printf(\"hi\\n\");}",
  "stdin": ""
}
```

## Important Safety Note

This project applies basic CPU/RAM/time limits, but it is **not a production-grade sandbox**.
For public internet use at scale, run untrusted code in a stronger isolation model (VMs/microVMs, seccomp, network isolation, queueing, and strict per-job containers).
