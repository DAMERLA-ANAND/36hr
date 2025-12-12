# Job Search App with Chatbot & AI Mock Interviews (36hr)

This repository contains a full-stack job search application with an AI chatbot that helps users discover roles, review resume fit, and prepare for interviews. It also includes an integrated AI Mock Interview platform with voice-based practice sessions powered by Retell AI. The backend is built with FastAPI and integrates Google Gemini for conversational AI, the JSearch API for job listings, and Retell AI for voice interviews. The frontend is a Vite + React app using a modern component library.

- Documentation: see [documentation.md](documentation.md)
- Integration Guide: see [INTEGRATION_README.md](INTEGRATION_README.md)
- Frontend quickstart: [frontend/README.md](frontend/README.md)
- Backend requirements: [backend/requirements.txt](backend/requirements.txt)

## Key Features

- **Resume Parsing**: Upload PDF resume for AI-powered profile extraction
- **AI Job Search**: Chat-based job discovery with Gemini AI
- **Job Management**: Save, unsave, and track applied jobs
- **AI Mock Interviews**: Voice-based practice interviews with AI interviewers
- **Job-Specific Interview Prep**: Generate interview questions tailored to saved jobs
- **Interview Analytics**: Performance feedback and scoring

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- A running MongoDB (local or cloud)
- Environment variables for backend (see below)

### Backend Setup

1. Create and activate a virtual environment.
2. Install dependencies from `backend/requirements.txt`.
3. Set environment variables in `backend/.env`.
4. Run the API server.

Example on Windows (PowerShell):

```powershell
Push-Location backend
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
copy NUL .env
# Edit .env with required keys (see documentation.md)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Pop-Location
```

### Environment Variables

Create `backend/.env` with:

```env
GEMINI_API_KEY=<your_gemini_api_key>
MONGODB_URI=<your_mongodb_connection_string>
JSEARCH_API_KEY=<your_jsearch_api_key>
RETELL_API_KEY=<your_retell_api_key>
RETELL_AGENT_ID_1=<agent_id_for_interviewer_1>
RETELL_AGENT_ID_2=<agent_id_for_interviewer_2>
RETELL_AGENT_ID_3=<agent_id_for_interviewer_3>
```

### Frontend Setup

1. Install dependencies.
2. Run the dev server.

```bash
cd frontend
npm i
npm run dev
```

By default, frontend runs on `http://localhost:5173` (Vite) and backend on `http://localhost:8000`. CORS is configured to allow local development.

## Application Routes

| Route | Description |
|-------|-------------|
| `/` | Onboarding page (resume upload) |
| `/home` | Home dashboard with quick actions |
| `/chat/:chatId` | AI chat for job search |
| `/profile` | User profile management |
| `/interview-prep` | Interview preparation dashboard |
| `/interview/:interviewId` | Voice interview room |

## Contributing

We welcome contributions! Please read the contribution guide in [documentation.md](documentation.md#contributing) and open an issue/PR with a clear description.

## License

Proprietary or project-specific; confirm before redistribution.
