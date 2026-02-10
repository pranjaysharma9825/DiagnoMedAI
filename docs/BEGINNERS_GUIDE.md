# DDX Diagnostic System - Beginner's Guide

## Welcome!

This guide will help you set up and run the DDX Diagnostic System from scratch, even if you have no prior experience with Python or web development.

---

## Prerequisites

Before starting, ensure you have the following installed:

| Software | Version | Download Link |
|----------|---------|---------------|
| **Python** | 3.10+ | https://www.python.org/downloads/ |
| **Node.js** | 18+ | https://nodejs.org/ |
| **Git** | Latest | https://git-scm.com/downloads |

### Checking Your Installation

Open **PowerShell** (Windows) or **Terminal** (Mac/Linux) and run:

```powershell
python --version   # Should show Python 3.10 or higher
node --version     # Should show v18 or higher
npm --version      # Should show 8 or higher
```

---

## Step 1: Navigate to the Project

Open PowerShell and navigate to the project folder:

```powershell
cd d:\PRANJAY\IPD\NEW_DDX
```

---

## Step 2: Set Up the Backend

### 2.1 Create a Virtual Environment (First Time Only)

A virtual environment keeps project dependencies isolated:

```powershell
python -m venv venv
```

### 2.2 Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate
```

You should see `(venv)` at the start of your command line.

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 2.3 Install Python Dependencies

```powershell
pip install -r requirements.txt
```

This installs all required Python packages (FastAPI, LangGraph, TensorFlow, etc.)

### 2.4 Create Environment File (First Time Only)

Create a file named `.env` in the project root with these settings:

```ini
# d:\PRANJAY\IPD\NEW_DDX\.env

# Application Settings
APP_NAME=DDX Diagnostic System
DEBUG=true

# LLM Provider (choose one)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2

# Optional: Cloud LLM fallback
# GROQ_API_KEY=your-groq-key-here
# GOOGLE_API_KEY=your-google-key-here
```

---

## Step 3: Start the Backend Server

With the virtual environment activated, run:

```powershell
cd d:\PRANJAY\IPD\NEW_DDX
.\venv\Scripts\activate
uvicorn backend.app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

### Verify Backend is Running

Open your browser and go to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Step 4: Set Up the Frontend

Open a **new PowerShell window** (keep the backend running in the first one).

### 4.1 Navigate to Frontend Folder

```powershell
cd d:\PRANJAY\IPD\NEW_DDX\DiagnoMed_AI-main
```

### 4.2 Install Node Dependencies (First Time Only)

```powershell
npm install
```

This may take a few minutes.

### 4.3 Start the Frontend Server

```powershell
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

---

## Step 5: Access the Application

Open your browser and go to:

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | **Main Application** |
| http://localhost:8000/docs | API Documentation |

### Using the Application

1. **Login**: Enter any username, select "Doctor" or "Patient" role
2. **Patient Flow**: Enter symptoms → Upload X-ray → View results
3. **Doctor Flow**: View patient cases → Review DDx analysis

---

## Step 6: Running Tests

To verify everything works correctly:

```powershell
cd d:\PRANJAY\IPD\NEW_DDX
.\venv\Scripts\activate
python backend\test_all.py
```

Expected output:
```
TOTAL: 9/9 tests passed
```

---

## Step 7: Generate Evaluation Results (For Research)

### Pareto Evaluation (Accuracy vs Cost)

```powershell
curl -X POST "http://localhost:8000/api/evaluation/pareto/generate?n_cases=100"
```

### Likert Survey (Clinical Acceptability)

```powershell
curl -X POST "http://localhost:8000/api/evaluation/likert/generate?n_responses=50"
```

Results are saved in:
```
d:\PRANJAY\IPD\NEW_DDX\data\evaluation_results\
```

---

## Common Issues & Solutions

### Issue: "python is not recognized"

**Solution**: Add Python to your system PATH or use the full path:
```powershell
C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe
```

### Issue: "npm is not recognized"

**Solution**: Restart PowerShell after installing Node.js, or add Node to PATH.

### Issue: Backend fails to start with import errors

**Solution**: Ensure virtual environment is activated:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Frontend shows "Failed to fetch" errors

**Solution**: Make sure the backend is running on port 8000 first.

### Issue: CORS errors in browser

**Solution**: The backend allows all origins by default. If issues persist, check that both servers are running.

---

## Quick Reference Commands

```powershell
# Start Backend (Terminal 1)
cd d:\PRANJAY\IPD\NEW_DDX
.\venv\Scripts\activate
uvicorn backend.app:app --reload --port 8000

# Start Frontend (Terminal 2)
cd d:\PRANJAY\IPD\NEW_DDX\DiagnoMed_AI-main
npm run dev

# Run Tests
cd d:\PRANJAY\IPD\NEW_DDX
.\venv\Scripts\activate
python backend\test_all.py

# Stop Servers
# Press Ctrl+C in each terminal window
```

---

## Project Structure Overview

```
NEW_DDX/
├── backend/                 # Python backend
│   ├── app.py              # FastAPI main application
│   ├── agents/             # Multi-agent system
│   ├── models/             # Pydantic data models
│   ├── priors/             # Epidemiology & genomics
│   ├── services/           # Business logic
│   ├── evaluation/         # Pareto & Likert
│   └── utils/              # Utilities & CNN
├── data/                    # CSV knowledge base
├── DiagnoMed_AI-main/      # React frontend
│   ├── src/                # Source code
│   ├── package.json        # Node dependencies
│   └── .env                # Frontend config
├── requirements.txt         # Python dependencies
└── .env                    # Backend config
```

---

## Need Help?

- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Check Logs**: Backend logs appear in the terminal
- **Test Endpoints**: Use the "Try it out" button in Swagger docs

Happy diagnosing! 🏥
