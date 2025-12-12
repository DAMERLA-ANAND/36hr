# Job Search App with Chatbot & AI Mock Interviews — Full Documentation

This document describes the architecture, backend API routes, frontend components, data models, and how both parts work together. It also includes environment, setup, and contribution guidelines.

## Overview

- **Frontend**: Vite + React (TypeScript). Provides onboarding, chat, job browsing, interview preparation, and profile management UI. Lives under `frontend/`.
- **Backend**: FastAPI with Google Gemini for AI, JSearch API for job listings, and Retell AI for voice interviews; MongoDB for persistence. Lives under `backend/`.
- **Key Flows**:
  - Resume onboarding → extracts user profile via Gemini and stores it.
  - Chat → AI assistant helps find jobs, refine searches, and provide guidance. Function calling integrates job search/details.
  - Jobs → Save/Unsave, Apply tracking, and retrieval.
  - Interviews → Create custom or job-specific mock interviews, conduct voice practice sessions, receive analytics.

## Backend

Location: `backend/`

### Environment

Create `backend/.env` with:

- `GEMINI_API_KEY=<your_key>`
- `MONGODB_URI=<connection_string>` (set by `db.py` expectations)
- `JSEARCH_API_KEY=<your_key>` (for JSearch job listings)
- `RETELL_API_KEY=<your_key>` (for voice interviews)
- `RETELL_AGENT_ID_1=<agent_id>` (first interviewer agent)
- `RETELL_AGENT_ID_2=<agent_id>` (second interviewer agent)
- `RETELL_AGENT_ID_3=<agent_id>` (third interviewer agent)

### Dependencies

See `backend/requirements.txt`. Core libs:

- FastAPI, Uvicorn
- PyPDF2
- pydantic
- google-generativeai
- motor / pymongo (via `db.py`)
- retell-sdk (for voice interviews)

### Data Models (pydantic)

Defined in `backend/models.py`:

**User & Chat Models:**
- `UserOnboardingResponse`: structured profile data (name, email, skills, experience, etc.)
- `ChatMessage`, `Chat`, `ChatHistoryResponseItem`, `ChatHistoryResponse`, `CreateChatRequest/Response`
- `ChatMessageRequest/Response`, `GetChatMessagesRequest/Response`

**Job Models:**
- `GetAppliedJobsResponseItem`, `GetSavedJobsResponseItem`, etc.

**Interview Models:**
- `Interviewer`: AI interviewer profile (id, name, personality, traits)
- `InterviewQuestion`: question with follow-up count
- `Interview`: full interview document (name, objective, questions, job context)
- `CreateInterviewRequest/Response`: custom interview creation
- `CreateJobInterviewRequest/Response`: job-specific interview creation
- `InterviewResponse`: voice interview session data
- `InterviewAnalytics`: performance scores and feedback
- `RegisterCallRequest/Response`: Retell voice call registration

### API Routes

Implemented in `backend/main.py`.

#### User & Onboarding Routes

- `POST /api/onboardFileUpload`
  - Input: raw PDF file body.
  - Process: parses resume text → prompts Gemini with a JSON schema → returns validated `UserOnboardingResponse`.
  - Errors: 400 for non-PDF; 500 on processing issues.

- `POST /api/confirmOnboardingDetails`
  - Input: `UserOnboardingResponse` (confirmed by user).
  - Process: upserts user doc in `users` collection; initializes `chat_history`, `saved_jobs`, `applied_jobs`.
  - Output: `{ message, id | email }`.

- `POST /api/updateUserProfile`
  - Input: `UserProfileUpdateRequest` (partial updates supported).
  - Process: `$set` fields for the user.

#### Chat Routes

- `GET /api/chatHistoryRequest?email=<email>`
  - Output: `ChatHistoryResponse` containing `{ id, chat_name, chat_id }` per chat.

- `POST /api/createChat`
  - Input: `CreateChatRequest { email }`.
  - Process: creates permanent context via Gemini from user profile, initializes chat with greeting.
  - Output: `CreateChatResponse { chat_id, chat_name, initial_message }`.

- `POST /api/sendMessage`
  - Input: `ChatMessageRequest { email, chat_id, message, selected_job_id? }`.
  - Process: builds context prompt (permanent profile, conversation summary, recent messages). Uses Gemini with function calling:
    - `search_jobs(query, ...)` → returns job cards for UI.
    - `get_job_details(job_id, ...)` → returns selected job details.
  - Output: `ChatMessageResponse { message, jobs?, selected_job_details? }`.

- `GET /api/getChatMessages?email=<email>&chat_id=<id>`
  - Output: `{ messages, chat_name }` for the chat.

#### Job Routes

- `GET /api/getAppliedJobs?email=<email>`
  - Output: `GetAppliedJobsResponse` (list of applied jobs).

- `GET /api/getSavedJobs?email=<email>`
  - Output: `GetSavedJobsResponse` (list of saved jobs).

- `POST /api/saveJob`
  - Input: `SaveJobRequest { email, job_id, job_title, company_name, job_link }`.
  - Process: `$addToSet` to `saved_jobs`.

- `POST /api/unsaveJob`
  - Input: `SaveJobRequest` (same as above).
  - Process: `$pull` from `saved_jobs`.

- `POST /api/applyJob`
  - Input: `ApplyJobRequest`.
  - Process: tracks applied jobs after user confirms in UI.

#### Interview Routes (NEW)

- `GET /api/interviewers`
  - Output: List of available AI interviewer profiles.
  - Returns: `[{ id, name, personality, description, voice, empathy, exploration, rapport_building, professionalism }]`

- `POST /api/createInterview`
  - Input: `CreateInterviewRequest { email, name, objective, interviewer_id, question_count, time_duration }`.
  - Process: generates interview questions via Gemini AI based on objective.
  - Output: `CreateInterviewResponse { interview_id, name, questions, interviewer }`.

- `POST /api/createJobInterview`
  - Input: `CreateJobInterviewRequest { email, job_id, job_title, company_name, interviewer_id, question_count, time_duration }`.
  - Process: generates job-specific interview questions using job details.
  - Output: `CreateJobInterviewResponse { interview_id, name, questions, interviewer, job_context }`.

- `GET /api/interviews?email=<email>`
  - Output: List of user's interview sessions with metadata.

- `GET /api/interview/{interview_id}?email=<email>`
  - Output: Full interview details including questions, interviewer info, and job context.

- `POST /api/registerCall`
  - Input: `RegisterCallRequest { interview_id, email }`.
  - Process: creates Retell AI voice call session, returns call credentials.
  - Output: `RegisterCallResponse { call_id, access_token, sample_rate }`.

- `POST /api/updateInterviewResponse`
  - Input: `{ interview_id, call_id, transcript?, duration?, is_ended? }`.
  - Process: updates interview response with call data.

- `GET /api/interviewHistory?email=<email>`
  - Output: User's practice session history with analytics.

- `POST /api/analyzeInterview`
  - Input: `{ interview_id, response_id }`.
  - Process: analyzes transcript via Gemini, generates scores and feedback.
  - Output: `InterviewAnalytics { overall_score, communication_score, technical_score, strengths, improvements }`.

- `POST /api/submitInterviewFeedback`
  - Input: `{ interview_id, email, feedback, satisfaction }`.
  - Process: stores user feedback about interview experience.

- `POST /api/retellWebhook`
  - Input: Retell callback payload.
  - Process: handles call status updates, transcript completion.

- `POST /api/generateInterviewObjective`
  - Input: `{ job_title, company_name, job_description? }`.
  - Process: uses Gemini to generate suggested interview objectives.
  - Output: `{ objective }`.

### Interview Service

`backend/interview_service.py` handles:

- Retell AI client initialization and configuration.
- Interview question generation via Gemini AI.
- Voice call session management.
- Interview analytics generation.
- Interviewer profile management.

### Chat Service

`backend/chat_service.py` handles:

- Gemini configuration and system prompt.
- Function declarations for `search_jobs` and `get_job_details`.
- Context management: permanent profile context, conversation summary, recent messages.
- Database updates of chat messages and context.

### Job Search Client

`backend/jsearch_client.py` provides `search_jobs` and `get_job_details` wrappers to JSearch API and helpers:

- `extract_job_cards_from_response(result)` returns compact cards for frontend.
- `extract_job_card_data(job)` returns detailed card for a single job.

### Database

`backend/db.py` defines database connection and collections:

**`users` collection:**
- User document contains: profile fields from onboarding, arrays `saved_jobs`, `applied_jobs`, and `chat_history` (array of chat docs with `messages` and `context`).

**`interviews` collection (NEW):**
- Interview documents with questions, interviewer settings, job context.

**`interview_responses` collection (NEW):**
- Voice call session data with transcripts and analytics.

**`interview_feedback` collection (NEW):**
- User feedback on interview experiences.

## Frontend

Location: `frontend/`

### Tech Stack

- Vite + React + TypeScript
- Component library under `frontend/src/components/ui/*`
- Tailwind CSS for styling

### Application Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `OnboardingPage` | Resume upload and profile creation |
| `/home` | `HomePage` | Dashboard with quick actions |
| `/chat/:chatId` | `ChatPage` | AI chat for job search |
| `/profile` | `ProfilePage` | User profile management |
| `/interview-prep` | `InterviewPrepPage` | Interview dashboard (NEW) |
| `/interview/:interviewId` | `InterviewRoomPage` | Voice interview room (NEW) |

### Key Pages & Components

**Existing Components:**
- `src/components/HomePage.tsx`: shows recent chats, saved jobs, and entry points including interview prep.
- `src/components/OnboardingPage.tsx`: upload resume (PDF) → displays extracted fields for confirmation → calls `confirmOnboardingDetails`.
- `src/components/ChatPage.tsx`: chat UI, renders bot messages, and job cards returned by `/api/sendMessage`; handles `createChat`, `getChatMessages`, `sendMessage`.
- `src/components/JobCard.tsx`: visual card for a job returned from backend; supports Save/Apply actions and **Prepare Interview** button.
- `src/components/JobDetailModal.tsx`: displays detailed job info when user selects a job.
- `src/components/ProfilePage.tsx`: user profile view/edit; calls `/api/updateUserProfile`.

**New Interview Components:**
- `src/components/InterviewPrepPage.tsx`: interview preparation dashboard featuring:
  - List of saved/applied jobs with "Prepare Interview" option
  - Create custom interview modal
  - AI-generated interview objectives
  - Interview history and analytics
  - Interviewer selection with personality traits

- `src/components/InterviewRoomPage.tsx`: voice interview room featuring:
  - Pre-interview screen with questions preview and instructions
  - Real-time voice conversation with AI interviewer
  - Live transcript display (interviewer and user responses)
  - Timer and progress tracking
  - Tab switch detection and warning
  - Post-interview summary and analytics

### Services

- `src/services/api.ts`: centralizes API calls to backend endpoints including:
  - Job search and management functions
  - Chat session functions
  - Interview functions (`getInterviewers`, `createInterview`, `createJobInterview`, `registerCall`, etc.)

### How Frontend and Backend Work Together

1. **Onboarding**: User uploads PDF → frontend posts raw file to `/api/onboardFileUpload` → backend returns `UserOnboardingResponse` → user confirms → frontend posts to `/api/confirmOnboardingDetails` → backend stores user.

2. **Chat Session**: Frontend calls `/api/createChat` → receives initial bot message and `chat_id` → subsequent messages sent to `/api/sendMessage` → backend may call job functions and return job cards or selected job details.

3. **Jobs**: Frontend Save/Apply buttons call `/api/saveJob`, `/api/unsaveJob`, `/api/applyJob` → backend updates arrays in user doc.

4. **Interview Prep (NEW)**:
   - User clicks "Prepare Interview" on job card → frontend calls `/api/generateInterviewObjective` → pre-fills interview form
   - User configures interview settings → frontend calls `/api/createJobInterview` or `/api/createInterview`
   - Backend generates questions via Gemini → returns interview details
   - User navigates to interview room → frontend calls `/api/registerCall` → starts Retell voice session
   - After interview → frontend calls `/api/analyzeInterview` → displays analytics

5. **History**: Frontend fetches chats via `/api/chatHistoryRequest` and interviews via `/api/interviews`.

### API Base URL

Adjust `src/services/api.ts` to point to your backend, typically `http://localhost:8000` during development. CORS in backend permits local origins.

## Running Locally

Backend (PowerShell):

```powershell
Push-Location backend
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
# Ensure .env has all required keys
uvicorn main:app --reload --host 0.0.0.0 --port 8000
Pop-Location
```

Frontend:

```bash
cd frontend
npm i
npm run dev
```

## Testing

- Backend includes `test_chatbot_simulation.py` and `test_simulation.py` for basic flows. Run with your Python test runner once env is configured.

## Contributing

- **Branching**: create feature branches from `main`.
- **Coding style**: follow existing TypeScript/React patterns and Python FastAPI conventions; keep changes minimal and focused.
- **Commit messages**: clear, imperative style (e.g., "Add onboarding error handling").
- **PRs**: include description, steps to test, and screenshots if UI changes.
- **Backend additions**: update `models.py` and document new routes here.
- **Frontend additions**: update or add components under `src/components` and wire APIs in `src/services/api.ts`.
- **Interview features**: when modifying interview logic, update both `interview_service.py` and corresponding frontend components.
- **Docs**: when changing APIs or component behavior, update this `documentation.md` and link relevant sections from `README.md`.

## Security & Privacy

- Do not commit secrets. Use `.env`.
- Treat resume data and profile fields as sensitive; avoid logging PII.
- Validate inputs server-side and sanitize any external API output.
- Interview transcripts contain user voice data; handle with appropriate privacy measures.

## Deployment Notes (high level)

- Backend: containerize with Uvicorn/Gunicorn, set envs, connect managed MongoDB.
- Frontend: build with `npm run build` and serve via a static host or CDN; configure backend URL.
- Enable HTTPS and tighten CORS for production.
- Configure Retell AI webhook URL for production domain.
- Ensure Retell AI agents are configured in production environment.
