# CareerSaathi AI: Technology Stack

**Version:** 1.0
**Document:** Technology Stack
**Last Updated:** August 2026

---

## 1. Overview

CareerSaathi AI will use a modern full-stack architecture consisting of a
React frontend, Python backend, PostgreSQL database, pre-trained AI models,
natural language processing, and speech-processing technologies.

The main technology combination is:

> React + FastAPI + PostgreSQL + LLM + NLP + Whisper

MongoDB will not be used in this project.

---

## 2. Frontend Technologies

### 2.1 React.js

React.js will be used to build the user interface using reusable components.

It will manage:

- Website pages
- Candidate dashboard
- Résumé-analysis results
- Interview configuration
- Interactive interview screen
- Performance reports
- User authentication interface

### 2.2 Vite

Vite will create and run the React application. It provides a fast development
server and generates an optimized production build.

Node.js and npm will only be used for frontend development and package
management. Node.js will not be used as the backend.

### 2.3 Tailwind CSS

Tailwind CSS will be used to build a responsive and consistent design system.

It will support:

- Responsive layouts
- Reusable design styles
- Dark and light interface elements
- Form and button styling
- Dashboard components
- Interview screens
- Mobile-device support

### 2.4 React Router

React Router will manage page navigation and protected frontend routes.

Example routes may include:

- `/`
- `/login`
- `/register`
- `/dashboard`
- `/profile`
- `/resumes`
- `/resume-analysis`
- `/job-match`
- `/interviews`
- `/interviews/new`
- `/interviews/:sessionId`
- `/reports/:reportId`

### 2.5 Axios

Axios will send HTTP requests from the React frontend to the FastAPI backend.

It will support:

- API base-URL configuration
- Secure cookie transmission
- Request and response handling
- Centralized error handling
- File uploads

### 2.6 Supporting Frontend Libraries

| Library | Purpose |
|---|---|
| React Hook Form | Form management |
| Zod | Frontend form validation |
| Recharts | Performance charts |
| Lucide React | Interface icons |
| Vitest | Frontend unit testing |
| React Testing Library | Component testing |
| Oxlint | JavaScript and React linting |
| Prettier | Code formatting |

---

## 3. Backend Technologies

### 3.1 Python

Python will be used for backend development, AI integration, NLP, résumé
processing, and speech processing.

Installed development version:

```text
Python 3.12.10
```

### 3.2 FastAPI

FastAPI will be used to create the backend REST APIs.

It will manage:

- Authentication
- Candidate profiles
- Résumé uploads
- Résumé processing
- Job matching
- Interview sessions
- AI-service communication
- Answer evaluation
- Performance reports
- Database operations

FastAPI also provides automatic OpenAPI and Swagger API documentation.

### 3.3 Uvicorn

Uvicorn will run the FastAPI application during development and deployment.

### 3.4 Pydantic

Pydantic will validate incoming and outgoing API data using structured Python
models.

### 3.5 Supporting Backend Libraries

| Library | Purpose |
|---|---|
| Uvicorn | Run the FastAPI server |
| Pydantic | Request and response validation |
| python-multipart | Handle uploaded files |
| HTTPX | External API requests and API testing |
| Ruff | Python linting and formatting |
| Pytest | Backend testing |

---

## 4. Database Technologies

### 4.1 PostgreSQL

PostgreSQL will be the main relational database.

Installed version:

```text
PostgreSQL 17.11
```

Local database configuration:

| Setting | Value |
|---|---|
| Database | `careersaathi_ai` |
| Application user | `careersaathi_app` |
| Host | `localhost` |
| Port | `5432` |
| Encoding | UTF-8 |

PostgreSQL will store:

- Users
- Candidate profiles
- Résumés
- Extracted skills
- Job descriptions
- Job-match results
- Interview configurations
- Interview sessions
- Questions
- Candidate answers
- Evaluations
- Performance reports

### 4.2 SQLAlchemy

SQLAlchemy 2 will be the Object Relational Mapper used to communicate with
PostgreSQL through Python models.

It will help with:

- Creating database models
- Reading and writing records
- Defining relationships
- Managing transactions
- Building secure database queries

### 4.3 Alembic

Alembic will manage database migrations. It will record and apply changes to
the database structure as the project develops.

### 4.4 Psycopg

Psycopg 3 will act as the PostgreSQL database driver for Python.

The backend connection will follow this format:

```text
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

The actual password will be stored in a private `.env` file and will never be
uploaded to GitHub.

---

## 5. Authentication and Security

### 5.1 JWT Authentication

JSON Web Tokens will manage authenticated user sessions.

Tokens will be placed in secure HTTP-only cookies to reduce access from
frontend JavaScript.

### 5.2 Password Hashing

The `pwdlib` library with the Argon2 algorithm will securely hash user
passwords before database storage.

Plain-text passwords will never be stored.

### 5.3 Authentication Libraries

| Library | Purpose |
|---|---|
| PyJWT | Create and verify authentication tokens |
| pwdlib with Argon2 | Secure password hashing |
| FastAPI security utilities | Protect API endpoints |

Additional security will include:

- CORS configuration
- Input validation
- File validation
- User ownership checks
- Rate limiting
- Safe error responses
- Environment-variable protection

---

## 6. Résumé Processing Technologies

### 6.1 PyMuPDF

PyMuPDF will extract readable text from PDF résumés.

### 6.2 python-docx

The `python-docx` library will extract text from DOCX résumés.

### 6.3 File Validation

The backend will validate:

- File extension
- MIME type
- File size
- File ownership
- Empty or unreadable files

Scanned-image résumés and Optical Character Recognition may be supported in a
future version.

---

## 7. Artificial Intelligence and NLP

### 7.1 Pre-Trained Large Language Model

CareerSaathi AI will use a pre-trained Large Language Model through an API. The
application will use an AI-provider service layer so that the selected model
can be changed without rewriting the complete backend.

The LLM will support:

- Résumé improvement suggestions
- Job-description understanding
- Interview-question generation
- Dynamic follow-up questions
- Answer evaluation
- Personalized feedback
- Performance summaries

The exact provider and model will be selected during the AI-integration phase
according to accuracy, API availability, response speed, and cost.

### 7.2 Natural Language Processing

Natural Language Processing will be used for:

- Text cleaning
- Résumé-section identification
- Skill extraction
- Keyword matching
- Job-description analysis
- Answer analysis

### 7.3 spaCy

spaCy may be used for text processing, sentence analysis, and entity
identification.

### 7.4 Rule-Based Matching

Skill dictionaries, normalization rules, and keyword matching will be combined
with AI analysis. This will make the match score easier to explain and test.

### 7.5 Model-Training Decision

The initial version will use pre-trained models and will not train a custom
Large Language Model.

This decision reduces:

- Development time
- Computing requirements
- Dataset requirements
- Deployment complexity
- Project cost

---

## 8. Speech Technologies

### 8.1 MediaRecorder API

The browser MediaRecorder API will record candidate voice answers.

### 8.2 Whisper

A Whisper-compatible speech-to-text model or API will convert recorded audio
into text.

### 8.3 Browser Speech Synthesis

The browser Speech Synthesis API will read interview questions aloud to the
candidate.

The initial version will not attempt to determine personality, emotion, or
protected personal characteristics from a candidate's voice.

---

## 9. API Communication

The initial application will use REST APIs for communication between React and
FastAPI.

The frontend will send requests to the backend. The backend will communicate
with PostgreSQL and approved external AI or speech services.

```mermaid
flowchart LR
    A["React Interface"] --> B["FastAPI REST API"]
    B --> C["PostgreSQL"]
    B --> D["AI Services"]
    B --> E["Speech Services"]
```

WebSockets may be added later if real-time audio streaming or other real-time
features become necessary.

---

## 10. File Storage

During local development, uploaded files will be stored in a controlled local
upload directory.

During deployment, résumé and audio storage will use secure cloud object
storage. File metadata and ownership information will remain in PostgreSQL.

Temporary audio files will be removed after transcription unless the user has
a clear reason to keep them.

The storage system will ensure that one candidate cannot access another
candidate's uploaded files.

---

## 11. Testing Technologies

### 11.1 Frontend Testing

The frontend will use:

- Vitest
- React Testing Library
- Manual browser testing
- Form-validation testing
- Responsive-design testing
- Production-build testing

### 11.2 Backend Testing

The backend will use:

- Pytest
- HTTPX
- FastAPI TestClient
- Database integration tests
- Authentication tests
- File-upload tests
- AI-service mock tests

### 11.3 System Testing

Complete system testing will include:

- Registration and login testing
- Résumé-upload testing
- Résumé-analysis testing
- Job-matching testing
- Interview-flow testing
- Voice-recording testing
- Speech-to-text testing
- AI error-handling testing
- Performance-report testing
- Deployment testing on another device

---

## 12. Development and Version Control

The following tools are installed in the development environment:

| Tool | Installed Version | Purpose |
|---|---:|---|
| Node.js | 22.18.0 | Frontend development |
| npm | 10.9.3 | Frontend package management |
| Python | 3.12.10 | Backend and AI development |
| pip | 26.0.1 | Python package management |
| PostgreSQL | 17.11 | Relational database |
| Git | 2.50.1 | Local version control |
| VS Code | 1.133.0 | Code editor |
| GitHub | Web service | Remote repository |

The GitHub repository name is:

```text
careersaathi-ai
```

Git will manage local source-code history, while GitHub will store the remote
repository and project backup.

---

## 13. Deployment Technologies

The planned deployment structure is:

| Application Part | Deployment Plan |
|---|---|
| React frontend | Static frontend hosting |
| FastAPI backend | Python application hosting |
| PostgreSQL | Managed PostgreSQL service |
| Uploaded files | Secure cloud object storage |
| Source code | GitHub |

Specific hosting providers will be finalized during the deployment phase after
checking availability, resource limits, pricing, and PostgreSQL support.

Environment variables will store:

- Database connection URL
- JWT secret
- AI API key
- Allowed frontend URL
- Upload configuration
- Application environment

Separate environment-variable values will be used for local development,
testing, and production deployment.

---

## 14. Technologies Not Used

The following technologies are not part of the CareerSaathi AI stack:

- MongoDB
- Mongoose
- Express.js
- Node.js backend
- MERN stack
- Custom LLM training for the MVP
- Facial recognition for the MVP
- Emotion or personality prediction

Node.js is required only for building and running the React frontend during
development.

---

## 15. Final Technology Stack

The finalized core technology stack is:

```text
Frontend:
React.js + Vite + Tailwind CSS

Backend:
Python + FastAPI + Pydantic

Database:
PostgreSQL + SQLAlchemy + Alembic + Psycopg

Authentication:
JWT + HTTP-only Cookies + Argon2 Password Hashing

Résumé Processing:
PyMuPDF + python-docx

AI and NLP:
Pre-trained LLM + spaCy + Rule-Based Matching

Speech:
MediaRecorder + Whisper + Speech Synthesis

Testing:
Vitest + React Testing Library + Pytest + HTTPX

Code Quality:
Oxlint + Prettier + Ruff

Version Control:
Git + GitHub
```

This technology stack is suitable for developing, testing, and deploying the
complete CareerSaathi AI application.

---

© 2026 CareerSaathi AI Project Documentation