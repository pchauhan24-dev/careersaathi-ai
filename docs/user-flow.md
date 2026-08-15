# CareerSaathi AI: User Flow

**Version:** 1.0
**Document:** User Flow
**Last Updated:** August 2026

---

## 1. Overview

This document describes how users will interact with CareerSaathi AI. It
covers registration, profile creation, résumé analysis, job matching, mock
interviews, performance reports, and interview history.

The primary user of the initial version is a candidate preparing for jobs,
internships, technical interviews, or HR interviews.

---

## 2. Main User

### Candidate

A candidate can:

- Create an account
- Log in securely
- Create a candidate profile
- Upload a résumé
- Analyse résumé content
- Enter a target job description
- View match scores and skill gaps
- Configure a mock interview
- Answer through text or voice
- Receive AI-generated follow-up questions
- View a performance report
- Review previous analyses and interviews
- Log out securely

An administrator dashboard may be added in a future version.

---

## 3. Main Entry Flow

```mermaid
flowchart TD
    A["Open CareerSaathi AI"] --> B["Landing Page"]
    B --> C{"Already Registered?"}
    C -->|No| D["Create Account"]
    C -->|Yes| E["Log In"]
    D --> E
    E --> F["Candidate Dashboard"]
```

A visitor can view the public landing page. Authentication will be required
before accessing personal résumés, interview sessions, and reports.

---

## 4. Primary Candidate Journey

```mermaid
flowchart TD
    A["Register or Log In"] --> B["Complete Profile"]
    B --> C["Upload Résumé"]
    C --> D["Analyse Résumé"]
    D --> E["Enter Job Description"]
    E --> F["View Job Match"]
    F --> G["Configure Interview"]
    G --> H["Complete Mock Interview"]
    H --> I["View Performance Report"]
    I --> J["Review Improvements"]
    J --> K["Practise Again"]
```

This represents the main end-to-end journey of CareerSaathi AI.

---

## 5. Registration Flow

```mermaid
flowchart TD
    A["Open Registration"] --> B["Enter User Details"]
    B --> C["Accept Terms"]
    C --> D["Submit Form"]
    D --> E{"Input Valid?"}
    E -->|No| F["Show Validation Errors"]
    F --> B
    E -->|Yes| G["Create Account"]
    G --> H["Show Success Message"]
    H --> I["Open Login"]
```

### Registration Information

The registration form will collect:

- Full name
- Email address
- Password
- Password confirmation
- Acceptance of terms

The system will check:

- Required fields
- Valid email format
- Unique email address
- Minimum password strength
- Matching passwords
- Acceptance of terms

---

## 6. Login Flow

```mermaid
flowchart TD
    A["Open Login"] --> B["Enter Email and Password"]
    B --> C["Submit Login"]
    C --> D{"Credentials Valid?"}
    D -->|No| E["Show Login Error"]
    E --> B
    D -->|Yes| F["Create Secure Session"]
    F --> G{"Previous Page Saved?"}
    G -->|Yes| H["Return to Previous Page"]
    G -->|No| I["Open Dashboard"]
```

After successful login, the backend will place the authentication token in a
secure HTTP-only cookie.

---

## 7. Candidate Profile Flow

```mermaid
flowchart TD
    A["Open Profile"] --> B["View Profile"]
    B --> C["Edit Information"]
    C --> D["Validate Information"]
    D --> E{"Information Valid?"}
    E -->|No| F["Show Errors"]
    F --> C
    E -->|Yes| G["Save Profile"]
    G --> H["Show Success Message"]
```

The candidate profile may contain:

- Full name
- Education
- Experience level
- Technical skills
- Preferred job role
- Career objective
- Profile completion status

---

## 8. Résumé Upload Flow

```mermaid
flowchart TD
    A["Open Résumé Page"] --> B["Select PDF or DOCX"]
    B --> C["Validate File"]
    C --> D{"File Valid?"}
    D -->|No| E["Show File Error"]
    E --> B
    D -->|Yes| F["Upload File"]
    F --> G["Extract Text"]
    G --> H["Analyse Résumé"]
    H --> I["Save Results"]
    I --> J["Display Analysis"]
```

### File Validation

The system will check:

- File extension
- MIME type
- File size
- Empty files
- Unreadable files
- User ownership

### Résumé Analysis Results

The candidate will be able to view:

- Extracted skills
- Education
- Work experience
- Projects
- Certifications
- Missing résumé sections
- Improvement suggestions

---

## 9. Job-Matching Flow

```mermaid
flowchart TD
    A["Select Résumé"] --> B["Enter Job Description"]
    B --> C["Start Analysis"]
    C --> D["Extract Job Requirements"]
    D --> E["Compare Résumé and Job"]
    E --> F["Calculate Match Score"]
    F --> G["Generate Suggestions"]
    G --> H["Display Match Report"]
```

### Job-Match Report

The report will display:

- Overall match score
- Matched skills
- Missing skills
- Partially matched skills
- Important keywords
- Experience alignment
- Résumé improvement suggestions

The candidate may continue directly from the job-match report to a personalized
mock interview.

---

## 10. Interview Configuration Flow

```mermaid
flowchart TD
    A["Start Mock Interview"] --> B["Select Job Role"]
    B --> C["Select Experience Level"]
    C --> D["Select Interview Type"]
    D --> E["Select Difficulty"]
    E --> F["Select Answer Mode"]
    F --> G["Select Question Count"]
    G --> H["Review Configuration"]
    H --> I["Start Interview"]
```

### Interview Options

The candidate can select:

- Target job role
- Beginner, intermediate, or experienced level
- Technical, HR, behavioural, or mixed interview
- Easy, medium, or difficult questions
- Text or voice answer mode
- Number of interview questions

A résumé and job description may also be selected to personalize the
questions.

---

## 11. Text Interview Flow

```mermaid
flowchart TD
    A["Display Question"] --> B["Start Response Timer"]
    B --> C["Candidate Types Answer"]
    C --> D["Submit Answer"]
    D --> E["Evaluate Answer"]
    E --> F{"Follow-Up Required?"}
    F -->|Yes| G["Generate Follow-Up"]
    G --> A
    F -->|No| H{"Interview Complete?"}
    H -->|No| I["Generate Next Question"]
    I --> A
    H -->|Yes| J["Generate Final Report"]
```

The candidate will answer one question at a time. The system will store the
question, answer, response time, and evaluation.

---

## 12. Voice Interview Flow

```mermaid
flowchart TD
    A["Display and Speak Question"] --> B["Request Microphone"]
    B --> C{"Permission Granted?"}
    C -->|No| D["Show Instructions"]
    D --> E["Use Text Mode"]
    C -->|Yes| F["Record Answer"]
    F --> G["Upload Audio"]
    G --> H["Convert Speech to Text"]
    H --> I["Review Transcript"]
    I --> J["Submit Answer"]
```

The candidate will be allowed to review the transcript before submitting it
for evaluation.

If voice recording or transcription fails, the candidate can retry or switch
to text mode.

---

## 13. Dynamic Follow-Up Flow

```mermaid
flowchart TD
    A["Receive Candidate Answer"] --> B["Analyse Answer"]
    B --> C{"Needs Clarification?"}
    C -->|Yes| D["Generate Clarification Question"]
    C -->|No| E{"Needs More Depth?"}
    E -->|Yes| F["Generate Technical Follow-Up"]
    E -->|No| G["Continue Interview"]
    D --> H["Ask Follow-Up"]
    F --> H
    H --> I["Candidate Answers"]
    I --> B
```

Follow-up questions may be generated when:

- The answer is incomplete
- The answer requires clarification
- The candidate mentions an important technology
- A technical concept needs deeper explanation
- The candidate provides an interesting project example

The system will limit follow-up questions so that the interview does not
continue indefinitely.

---

## 14. Answer-Evaluation Flow

```mermaid
flowchart TD
    A["Submitted Answer"] --> B["Validate Answer"]
    B --> C["Analyse Content"]
    C --> D["Apply Evaluation Criteria"]
    D --> E["Calculate Scores"]
    E --> F["Generate Feedback"]
    F --> G["Save Evaluation"]
```

Each answer may be scored using:

- Technical correctness
- Answer relevance
- Communication quality
- Clarity
- Structure
- Completeness
- Use of examples
- Response time

The evaluation will not use protected personal characteristics.

---

## 15. Final Report Flow

```mermaid
flowchart TD
    A["Interview Completed"] --> B["Collect Evaluations"]
    B --> C["Calculate Category Scores"]
    C --> D["Calculate Overall Score"]
    D --> E["Identify Strengths"]
    E --> F["Identify Weaknesses"]
    F --> G["Generate Suggestions"]
    G --> H["Display and Save Report"]
```

The final report will include:

- Technical-knowledge score
- Communication score
- Relevance score
- Answer-structure score
- Response-time score
- Overall score
- Candidate strengths
- Areas for improvement
- Question-level feedback
- Personalized practice suggestions

---

## 16. Dashboard Flow

```mermaid
flowchart TD
    A["Open Dashboard"] --> B["View Summary"]
    B --> C["Open Résumé Analysis"]
    B --> D["Open Job Matches"]
    B --> E["Open Interview History"]
    B --> F["Start New Interview"]
    E --> G["Open Previous Report"]
```

The dashboard will provide quick access to:

- Candidate profile
- Uploaded résumés
- Latest résumé analysis
- Saved job-match reports
- Recent interviews
- Performance history
- New mock interview
- Improvement suggestions

---

## 17. Interview History Flow

```mermaid
flowchart TD
    A["Open Interview History"] --> B["View Session List"]
    B --> C["Select Interview"]
    C --> D["View Configuration"]
    D --> E["View Questions and Answers"]
    E --> F["View Evaluation"]
    F --> G["Open Final Report"]
```

Candidates will only be able to access their own interview sessions and
reports.

---

## 18. Logout Flow

```mermaid
flowchart TD
    A["Select Logout"] --> B["Send Logout Request"]
    B --> C["Remove Authentication Cookie"]
    C --> D["Clear User State"]
    D --> E["Return to Landing Page"]
```

After logout, protected pages will redirect the user to the login page.

---

## 19. Protected Route Flow

```mermaid
flowchart TD
    A["Open Protected Page"] --> B["Check Session"]
    B --> C{"Authenticated?"}
    C -->|Yes| D["Display Requested Page"]
    C -->|No| E["Save Requested Location"]
    E --> F["Redirect to Login"]
    F --> G["Complete Login"]
    G --> D
```

Protected pages will include:

- Dashboard
- Profile
- Résumés
- Job matches
- Interview sessions
- Performance reports
- History pages

---

## 20. Error and Recovery Flow

```mermaid
flowchart TD
    A["Application Operation"] --> B{"Operation Successful?"}
    B -->|Yes| C["Continue User Flow"]
    B -->|No| D["Show Clear Error"]
    D --> E{"Can Retry?"}
    E -->|Yes| F["Retry Operation"]
    F --> A
    E -->|No| G["Return to Safe Page"]
```

Examples include:

- Invalid login details
- Unsupported résumé files
- Failed file uploads
- Unreadable résumé text
- Microphone permission denied
- Speech-transcription failure
- AI-service failure
- Lost internet connection
- Expired authentication session
- Database or server error

The system will preserve completed work whenever possible.

---

## 21. Planned Application Routes

### Public Routes

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/login` | Candidate login |
| `/register` | Candidate registration |
| `/about` | Project information |
| `/privacy` | Privacy information |

### Protected Routes

| Route | Purpose |
|---|---|
| `/dashboard` | Candidate dashboard |
| `/profile` | Candidate profile |
| `/resumes` | Résumé management |
| `/resumes/:resumeId` | Résumé details |
| `/job-match` | Create job match |
| `/job-matches/:matchId` | Job-match report |
| `/interviews` | Interview history |
| `/interviews/new` | Interview configuration |
| `/interviews/:sessionId` | Active interview |
| `/reports/:reportId` | Performance report |

A final not-found route will handle invalid URLs.

---

## 22. Complete User Journey Summary

```text
Open CareerSaathi AI
        ↓
Register or Log In
        ↓
Complete Candidate Profile
        ↓
Upload and Analyse Résumé
        ↓
Enter Target Job Description
        ↓
View Match Score and Skill Gaps
        ↓
Configure Personalized Interview
        ↓
Answer through Text or Voice
        ↓
Receive Dynamic Follow-Up Questions
        ↓
Complete Interview
        ↓
View Performance Report
        ↓
Review Suggestions
        ↓
Practise Again and Track Progress
```

This flow allows CareerSaathi AI to support the candidate from résumé
preparation through interview practice and performance improvement.

---

© 2026 CareerSaathi AI Project Documentation