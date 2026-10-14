# CloudBlueprint AI

CloudBlueprint AI turns a project idea into a practical AWS project plan. Enter a project title, the problem it solves, intended users, and any desired features. The app checks that the idea is understandable, then generates a plan with an AWS architecture, data flow, security considerations, and build phases.

The project uses a React and TypeScript frontend, a FastAPI backend, and the Qwen 2.5 3B model running locally through Ollama. Generated plans are suggestions, not production-ready architecture designs.

## Features

- Generate a structured plan with six sections:
  - Project summary
  - Suggested features
  - AWS architecture
  - Data flow
  - Security and privacy considerations
  - Build phases
- Reject input that the language model identifies as unintelligible.
- Display section headings in bold and list items as bullets.
- Download a generated plan as a text file.
- Run the language model locally with Ollama.

## Technology

- Frontend: React, TypeScript, and Vite
- Backend: Python, FastAPI, and Uvicorn
- Model runtime: Ollama
- Default model: `qwen2.5:3b`

## Requirements

Install these before starting:

- Git
- Node.js and npm
- Python 3
- [Ollama](https://ollama.com/download)

## Run locally on Windows

### 1. Get the project

Clone the repository from GitHub and enter its folder. Replace the example owner and repository name with yours:

```powershell
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Download the Ollama model

Open a terminal and download the model used by default:

```powershell
ollama pull qwen2.5:3b
```

Ollama normally runs in the background after installation. If it is not running, start it in a separate terminal:

```powershell
ollama serve
```

Keep that terminal open if you started Ollama manually.

### 3. Set up and start the backend

Open a new terminal from the project root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

The API will be available at `http://127.0.0.1:8001`. FastAPI's interactive API documentation is at `http://127.0.0.1:8001/docs`.

If PowerShell blocks virtual environment activation, allow it for the current terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Alternatively, run the venv's Python directly without activating it:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### 4. Set up and start the frontend

Open another terminal from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

Keep the backend, frontend, and Ollama running while using the app.

## Useful commands

Run these from the indicated project folders.

### Backend

From `backend` with its virtual environment active:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Check backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health
```

Generate a plan directly through the API:

```powershell
$body = @{
  title = "Community Garden Planner"
  problem = "Gardeners need a simple way to coordinate shared plots and watering."
  projectType = "A web app for local community gardens"
  features = "Plot scheduling`nWatering reminders"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8001/api/generate-plan `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### Frontend

From `frontend`:

```powershell
npm run dev
npm run build
npm run lint
npm run preview
```

- `npm run dev` starts the local development server.
- `npm run build` type-checks the project and creates a production build in `frontend/dist`.
- `npm run lint` runs ESLint.
- `npm run preview` serves the production build locally. Run `npm run build` first.

## Configuration

The defaults work for local development:

| Variable | Used by | Default | Purpose |
| --- | --- | --- | --- |
| `OLLAMA_URL` | Backend | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | Backend | `qwen2.5:3b` | Model name available in Ollama |
| `FRONTEND_ORIGIN` | Backend | Not set | Optional additional frontend origin for CORS |
| `VITE_API_BASE_URL` | Frontend | `http://127.0.0.1:8001` | FastAPI base URL |

To use a different Ollama model, pull it first, then set the backend variable in the backend terminal before starting Uvicorn. For example:

```powershell
ollama pull llama3.2
$env:OLLAMA_MODEL = "llama3.2"
```

To point the frontend to a backend running at another address, set `VITE_API_BASE_URL` in the frontend terminal before running `npm run dev`:

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8001"
npm run dev
```

Vite reads its environment variables when it starts; restart the development server after changing them.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Check that the backend is running |
| `POST` | `/api/generate-plan` | Validate an idea and generate a plan |

## Project structure

```text
.
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── package.json
│   └── package-lock.json
└── README.md
```

## Troubleshooting

- **The frontend cannot reach the backend:** confirm Uvicorn is running on port `8001`, then check `http://127.0.0.1:8001/api/health`.
- **The backend cannot reach Ollama:** confirm Ollama is running and that `ollama list` shows the configured model.
- **Ollama reports that the model is missing:** run `ollama pull qwen2.5:3b`, or pull the model configured in `OLLAMA_MODEL`.
- **The response takes a while:** local model generation time depends on your hardware and available memory.
- **The input is rejected:** enter recognizable words in the project title or problem description. The backend uses the configured Ollama model to check whether the text is intelligible.

## Notes

- The generated plan describes suggested AWS services; the app does not create AWS resources or deploy the plan.
- Do not submit secrets, credentials, or sensitive personal information in project descriptions.
- Review generated architecture choices for your project's requirements before implementation.
