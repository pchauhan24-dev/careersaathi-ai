# CareerSaathi AI: API Documentation

**Version:** 1.0
**Document:** REST API Planning
**Backend:** FastAPI
**Base Path:** `/api/v1`
**Last Updated:** August 2026

---

## 1. Overview

CareerSaathi AI will use REST APIs for communication between the React
frontend and FastAPI backend.

The APIs will manage:

- Authentication
- Candidate profiles
- Skills
- Résumé uploads and analysis
- Job descriptions
- Job matching
- Interview sessions
- Voice transcription
- Answer evaluation
- Performance reports
- Candidate dashboard

FastAPI will automatically generate interactive Swagger documentation.

During local development, the API documentation will be available at:

```text
http://localhost:8000/docs
```

The OpenAPI schema will be available at:

```text
http://localhost:8000/openapi.json
```

---

## 2. Base URLs

### Local Development

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
API:      http://localhost:8000/api/v1
```

### Production

Production URLs will be configured through environment variables.

The frontend will use:

```env
VITE_API_URL=https://backend-domain.example/api/v1
```

The backend will use an allowed frontend-origin setting:

```env
CLIENT_URL=https://frontend-domain.example
```

---

## 3. Standard Success Response

Successful API requests will generally use this format:

```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}
```

Example:

```json
{
  "success": true,
  "message": "Profile retrieved successfully.",
  "data": {
    "id": "7f709452-8553-4e63-b588-e333cd3cd667",
    "fullName": "Candidate Name",
    "targetRole": "Python Developer"
  }
}
```

---

## 4. Standard Error Response

Failed API requests will generally use this format:

```json
{
  "success": false,
  "message": "The submitted information is invalid.",
  "errors": [
    {
      "field": "email",
      "message": "Enter a valid email address."
    }
  ],
  "requestId": "request-identifier"
}
```

Sensitive server information, passwords, tokens, database queries, and API keys
will not be returned in error responses.

---

## 5. Pagination Format

List endpoints will support pagination.

Example request:

```http
GET /api/v1/interviews?page=1&limit=10
```

Example response:

```json
{
  "success": true,
  "message": "Interview sessions retrieved successfully.",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "limit": 10,
      "totalItems": 0,
      "totalPages": 0,
      "hasNextPage": false,
      "hasPreviousPage": false
    }
  }
}
```

The default page size will be 10. The backend will enforce a maximum page size
to prevent oversized requests.

---

## 6. Authentication

CareerSaathi AI will use JWT authentication through HTTP-only cookies.

The frontend must send requests with credentials enabled:

```javascript
axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});
```

Protected endpoints will use the authenticated user's identity from the
verified cookie. They will not trust a user ID supplied by the frontend.

### Local Cookie Settings

```text
HttpOnly: true
Secure: false
SameSite: Lax
```

### Production Cookie Settings

Production settings will use HTTPS. If frontend and backend hosting require
cross-site cookies, the application will use secure cookie and request-origin
protection settings.

---

## 7. HTTP Status Codes

| Status | Meaning |
|---:|---|
| `200` | Request completed successfully |
| `201` | New record created successfully |
| `202` | Request accepted for processing |
| `204` | Request completed without response content |
| `400` | Invalid request |
| `401` | Authentication required |
| `403` | Permission denied |
| `404` | Record or route not found |
| `409` | Duplicate or conflicting record |
| `413` | Uploaded file is too large |
| `415` | Unsupported file type |
| `422` | Request validation failed |
| `429` | Too many requests |
| `500` | Unexpected server error |
| `502` | External AI or speech service failed |
| `503` | Service temporarily unavailable |

---

## 8. Health Endpoint

### Check API Health

```http
GET /api/v1/health
```

Authentication required: No

Example response:

```json
{
  "success": true,
  "message": "CareerSaathi AI API is running.",
  "data": {
    "status": "healthy",
    "environment": "development"
  }
}
```

The public health endpoint will not expose passwords, API keys, or detailed
infrastructure information.

---

## 9. Authentication Endpoints

### 9.1 Register Candidate

```http
POST /api/v1/auth/register
```

Authentication required: No

Request:

```json
{
  "fullName": "Candidate Name",
  "email": "candidate@example.com",
  "password": "private-password",
  "confirmPassword": "private-password",
  "acceptTerms": true
}
```

Success response: `201 Created`

```json
{
  "success": true,
  "message": "Account created successfully.",
  "data": {
    "user": {
      "id": "user-uuid",
      "fullName": "Candidate Name",
      "email": "candidate@example.com",
      "role": "candidate"
    }
  }
}
```

Possible errors:

- Invalid email
- Weak password
- Passwords do not match
- Terms not accepted
- Email already registered

### 9.2 Login

```http
POST /api/v1/auth/login
```

Authentication required: No

Request:

```json
{
  "email": "candidate@example.com",
  "password": "private-password",
  "rememberMe": true
}
```

Success response: `200 OK`

The backend will set the authentication cookie.

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "user": {
      "id": "user-uuid",
      "fullName": "Candidate Name",
      "email": "candidate@example.com",
      "role": "candidate"
    }
  }
}
```

### 9.3 Get Current User

```http
GET /api/v1/auth/me
```

Authentication required: Yes

Success response: `200 OK`

### 9.4 Logout

```http
POST /api/v1/auth/logout
```

Authentication required: Yes

The backend will remove the authentication cookie.

Success response: `200 OK`

```json
{
  "success": true,
  "message": "Logout successful.",
  "data": null
}
```

### 9.5 Refresh Session

```http
POST /api/v1/auth/refresh
```

Authentication required: Valid refresh session

This endpoint may be implemented if separate access and refresh tokens are used.

---

## 10. Candidate Profile Endpoints

### Get Candidate Profile

```http
GET /api/v1/profile
```

Authentication required: Yes

### Create or Update Candidate Profile

```http
PUT /api/v1/profile
```

Authentication required: Yes

Request:

```json
{
  "phone": "9876543210",
  "city": "Raipur",
  "state": "Chhattisgarh",
  "country": "India",
  "educationLevel": "Undergraduate",
  "experienceLevel": "Fresher",
  "yearsExperience": 0,
  "targetRole": "Python Developer",
  "headline": "Computer science student",
  "bio": "Interested in backend development and artificial intelligence."
}
```

### Partially Update Candidate Profile

```http
PATCH /api/v1/profile
```

Authentication required: Yes

Only submitted fields will be updated.

---

## 11. Skill Endpoints

### Get Available Skills

```http
GET /api/v1/skills
```

Authentication required: Yes

Supported query parameters:

```text
search
category
page
limit
```

Example:

```http
GET /api/v1/skills?search=python&category=programming
```

### Add Candidate Skill

```http
POST /api/v1/profile/skills
```

Authentication required: Yes

Request:

```json
{
  "skillId": "skill-uuid",
  "proficiencyLevel": "intermediate",
  "yearsExperience": 1
}
```

### Update Candidate Skill

```http
PATCH /api/v1/profile/skills/{candidateSkillId}
```

Authentication required: Yes

### Remove Candidate Skill

```http
DELETE /api/v1/profile/skills/{candidateSkillId}
```

Authentication required: Yes

---

## 12. Résumé Endpoints

### 12.1 Upload Résumé

```http
POST /api/v1/resumes
```

Authentication required: Yes
Content type: `multipart/form-data`

Form field:

```text
file
```

Supported formats:

- PDF
- DOCX

Planned maximum file size:

```text
5 MB
```

Success response: `201 Created`

```json
{
  "success": true,
  "message": "Résumé uploaded successfully.",
  "data": {
    "resume": {
      "id": "resume-uuid",
      "originalFilename": "candidate-resume.pdf",
      "fileType": "pdf",
      "fileSize": 245810,
      "processingStatus": "pending",
      "createdAt": "2026-08-15T10:00:00Z"
    }
  }
}
```

### 12.2 Get Résumés

```http
GET /api/v1/resumes
```

Authentication required: Yes

Supported query parameters:

```text
page
limit
status
```

### 12.3 Get Résumé Details

```http
GET /api/v1/resumes/{resumeId}
```

Authentication required: Yes

The candidate must own the requested résumé.

### 12.4 Set Primary Résumé

```http
PATCH /api/v1/resumes/{resumeId}/primary
```

Authentication required: Yes

### 12.5 Delete Résumé

```http
DELETE /api/v1/resumes/{resumeId}
```

Authentication required: Yes

Success response: `204 No Content`

---

## 13. Résumé-Analysis Endpoints

### 13.1 Start Résumé Analysis

```http
POST /api/v1/resumes/{resumeId}/analyses
```

Authentication required: Yes

The endpoint will:

1. Validate résumé ownership.
2. Extract résumé text.
3. Identify résumé sections.
4. Extract skills and candidate information.
5. Generate improvement suggestions.
6. Save the analysis.

Success response: `201 Created` or `202 Accepted`

### 13.2 Get Résumé Analyses

```http
GET /api/v1/resumes/{resumeId}/analyses
```

Authentication required: Yes

### 13.3 Get Latest Résumé Analysis

```http
GET /api/v1/resumes/{resumeId}/analyses/latest
```

Authentication required: Yes

### 13.4 Get Specific Analysis

```http
GET /api/v1/resume-analyses/{analysisId}
```

Authentication required: Yes

---

## 14. Job-Description Endpoints

### 14.1 Create Job Description

```http
POST /api/v1/job-descriptions
```

Authentication required: Yes

Request:

```json
{
  "jobTitle": "Python Developer",
  "companyName": "Example Company",
  "experienceLevel": "Fresher",
  "location": "Remote",
  "sourceUrl": null,
  "descriptionText": "The candidate should have knowledge of Python..."
}
```

Success response: `201 Created`

### 14.2 Get Job Descriptions

```http
GET /api/v1/job-descriptions
```

Authentication required: Yes

### 14.3 Get Job Description

```http
GET /api/v1/job-descriptions/{jobDescriptionId}
```

Authentication required: Yes

### 14.4 Update Job Description

```http
PATCH /api/v1/job-descriptions/{jobDescriptionId}
```

Authentication required: Yes

### 14.5 Delete Job Description

```http
DELETE /api/v1/job-descriptions/{jobDescriptionId}
```

Authentication required: Yes

---

## 15. Job-Match Endpoints

### 15.1 Create Job Match

```http
POST /api/v1/job-matches
```

Authentication required: Yes

Request:

```json
{
  "resumeId": "resume-uuid",
  "jobDescriptionId": "job-description-uuid"
}
```

The endpoint will:

1. Validate ownership.
2. Load résumé-analysis results.
3. Extract job requirements.
4. Compare skills and keywords.
5. Calculate category scores.
6. Generate improvement suggestions.
7. Save the match result.

Success response: `201 Created`

```json
{
  "success": true,
  "message": "Job match completed successfully.",
  "data": {
    "jobMatch": {
      "id": "job-match-uuid",
      "skillsScore": 82,
      "experienceScore": 70,
      "keywordScore": 78,
      "overallScore": 78,
      "matchedSkills": [
        "Python",
        "FastAPI",
        "PostgreSQL"
      ],
      "missingSkills": [
        "Docker",
        "AWS"
      ],
      "suggestions": [
        "Add deployment experience to the résumé.",
        "Include projects that demonstrate REST API development."
      ]
    }
  }
}
```

### 15.2 Get Job Matches

```http
GET /api/v1/job-matches
```

Authentication required: Yes

### 15.3 Get Job-Match Report

```http
GET /api/v1/job-matches/{jobMatchId}
```

Authentication required: Yes

### 15.4 Delete Job Match

```http
DELETE /api/v1/job-matches/{jobMatchId}
```

Authentication required: Yes

---

## 16. Interview Endpoints

### 16.1 Create Interview Session

```http
POST /api/v1/interviews
```

Authentication required: Yes

Request:

```json
{
  "resumeId": "resume-uuid",
  "jobDescriptionId": "job-description-uuid",
  "jobMatchId": "job-match-uuid",
  "jobRole": "Python Developer",
  "experienceLevel": "fresher",
  "interviewType": "mixed",
  "difficultyLevel": "medium",
  "answerMode": "voice",
  "questionLimit": 10
}
```

Success response: `201 Created`

```json
{
  "success": true,
  "message": "Interview session created successfully.",
  "data": {
    "interview": {
      "id": "interview-uuid",
      "status": "created",
      "questionLimit": 10
    }
  }
}
```

### 16.2 Get Interview Sessions

```http
GET /api/v1/interviews
```

Authentication required: Yes

Supported query parameters:

```text
status
interviewType
page
limit
sort
```

### 16.3 Get Interview Session

```http
GET /api/v1/interviews/{sessionId}
```

Authentication required: Yes

### 16.4 Start Interview

```http
POST /api/v1/interviews/{sessionId}/start
```

Authentication required: Yes

The response will contain the first question.

### 16.5 Get Current Question

```http
GET /api/v1/interviews/{sessionId}/questions/current
```

Authentication required: Yes

### 16.6 Submit Interview Answer

```http
POST /api/v1/interviews/{sessionId}/answers
```

Authentication required: Yes

Request:

```json
{
  "questionId": "question-uuid",
  "answerText": "FastAPI is a Python framework used to build APIs...",
  "answerMode": "text",
  "responseTimeSeconds": 72
}
```

The response may contain:

- Saved answer
- Question-level evaluation
- Follow-up question
- Next normal question
- Interview completion status

Example response:

```json
{
  "success": true,
  "message": "Answer evaluated successfully.",
  "data": {
    "evaluation": {
      "technicalScore": 82,
      "relevanceScore": 90,
      "communicationScore": 78,
      "structureScore": 75,
      "completenessScore": 80,
      "overallScore": 81,
      "feedback": "The answer was relevant but needed a practical example."
    },
    "nextQuestion": {
      "id": "next-question-uuid",
      "questionText": "Can you explain dependency injection in FastAPI?",
      "isFollowUp": true
    },
    "interviewComplete": false
  }
}
```

### 16.7 Complete Interview

```http
POST /api/v1/interviews/{sessionId}/complete
```

Authentication required: Yes

This endpoint will calculate final scores and generate the performance report.

### 16.8 Cancel Interview

```http
POST /api/v1/interviews/{sessionId}/cancel
```

Authentication required: Yes

### 16.9 Delete Interview

```http
DELETE /api/v1/interviews/{sessionId}
```

Authentication required: Yes

Only cancelled, failed, or completed interviews may be deleted.

---

## 17. Speech Endpoint

### Transcribe Voice Answer

```http
POST /api/v1/speech/transcriptions
```

Authentication required: Yes
Content type: `multipart/form-data`

Form fields:

```text
audio
sessionId
questionId
```

Planned supported formats:

- WebM
- WAV
- MP3
- M4A

Example response:

```json
{
  "success": true,
  "message": "Audio transcribed successfully.",
  "data": {
    "transcript": "FastAPI is a Python framework for creating APIs.",
    "durationSeconds": 28
  }
}
```

The candidate will be allowed to review the transcript before submitting it as
the final answer.

---

## 18. Evaluation Endpoints

### Get Question Evaluation

```http
GET /api/v1/answers/{answerId}/evaluation
```

Authentication required: Yes

The candidate must own the interview containing the answer.

The response will contain:

- Category scores
- Overall answer score
- Written feedback
- Strengths
- Improvement suggestions

---

## 19. Performance Report Endpoints

### 19.1 Get Performance Reports

```http
GET /api/v1/reports
```

Authentication required: Yes

Supported query parameters:

```text
page
limit
jobRole
interviewType
sort
```

### 19.2 Get Performance Report

```http
GET /api/v1/reports/{reportId}
```

Authentication required: Yes

### 19.3 Get Report for Interview

```http
GET /api/v1/interviews/{sessionId}/report
```

Authentication required: Yes

Example report response:

```json
{
  "success": true,
  "message": "Performance report retrieved successfully.",
  "data": {
    "report": {
      "id": "report-uuid",
      "technicalScore": 82,
      "communicationScore": 76,
      "relevanceScore": 88,
      "structureScore": 74,
      "responseTimeScore": 80,
      "overallScore": 80,
      "strengths": [
        "Strong understanding of Python fundamentals",
        "Relevant answers"
      ],
      "weaknesses": [
        "Limited practical examples",
        "Some answers lacked structure"
      ],
      "suggestions": [
        "Use the STAR method for behavioural answers.",
        "Add practical examples to technical explanations."
      ]
    }
  }
}
```

PDF report export may be added after the main report feature is complete.

---

## 20. Dashboard Endpoints

### Get Dashboard Summary

```http
GET /api/v1/dashboard/summary
```

Authentication required: Yes

The response may contain:

- Profile completion
- Total résumés
- Total job matches
- Total completed interviews
- Latest match score
- Latest interview score
- Recent activity

### Get Performance Progress

```http
GET /api/v1/dashboard/progress
```

Authentication required: Yes

Supported query parameters:

```text
period
jobRole
interviewType
```

The response will provide data for frontend charts.

---

## 21. Metadata Endpoints

### Get Interview Options

```http
GET /api/v1/metadata/interview-options
```

Authentication required: No

The response may contain:

- Interview types
- Experience levels
- Difficulty levels
- Answer modes
- Allowed question counts

### Get Job Roles

```http
GET /api/v1/metadata/job-roles
```

Authentication required: No

---

## 22. Ownership and Authorization Rules

Protected endpoints will follow these rules:

- A candidate can access only their own profile.
- A candidate can access only their own résumés.
- A candidate can access only their own job descriptions.
- A candidate can access only their own job matches.
- A candidate can access only their own interviews.
- A candidate can access only their own answers.
- A candidate can access only their own reports.
- User IDs sent by the frontend will not control ownership.
- Administrator endpoints will require a separate role check when added.

Unauthorized access will return `403 Forbidden` or `404 Not Found`, depending on
the security design.

---

## 23. Input Validation

The API will validate:

- Email addresses
- Password requirements
- UUID parameters
- Required text fields
- Allowed role values
- Score ranges
- Pagination values
- File types
- MIME types
- File sizes
- Interview status changes
- Question ownership
- Answer length
- Response time
- Uploaded audio types

Pydantic schemas will perform request and response validation.

---

## 24. Rate Limiting

Rate limiting will protect sensitive and expensive endpoints.

Stricter limits may be applied to:

- Registration
- Login
- Résumé analysis
- Job matching
- AI question generation
- Answer evaluation
- Speech transcription

When a rate limit is exceeded, the API will return:

```text
429 Too Many Requests
```

---

## 25. External Service Failure

If an AI or speech provider fails, the API will return a safe response.

Example:

```json
{
  "success": false,
  "message": "The AI service is temporarily unavailable. Please try again.",
  "errors": [],
  "requestId": "request-identifier"
}
```

Previously submitted answers will remain stored so the candidate can continue
the interview later.

---

## 26. API Testing

Each API module will be tested for:

- Successful requests
- Invalid requests
- Missing authentication
- Invalid authentication
- Record ownership
- Missing records
- Duplicate records
- File validation
- Database errors
- External AI failures
- Correct HTTP status codes
- Correct response structures

FastAPI Swagger, Pytest, HTTPX, and FastAPI TestClient will be used during API
testing.

---

## 27. Initial API Development Order

The APIs will be developed in this order:

1. Health endpoint
2. Database connection
3. Registration and login
4. Current-user and logout endpoints
5. Candidate profile
6. Skills
7. Résumé uploads
8. Résumé analysis
9. Job descriptions
10. Job matching
11. Interview sessions
12. Question generation
13. Text answers
14. Voice transcription
15. Answer evaluation
16. Performance reports
17. Dashboard and history

This order ensures that each new module builds on previously tested modules.

---

## 28. API Summary

```text
/api/v1
├── /health
├── /auth
├── /profile
├── /skills
├── /resumes
├── /resume-analyses
├── /job-descriptions
├── /job-matches
├── /interviews
├── /answers
├── /speech
├── /reports
├── /dashboard
└── /metadata
```

This API design supports the complete initial workflow of CareerSaathi AI while
allowing future modules to be added without changing the main API structure.

---

© 2026 CareerSaathi AI Project Documentation