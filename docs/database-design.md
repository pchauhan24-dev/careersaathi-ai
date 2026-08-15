# CareerSaathi AI: Database Design

**Version:** 1.0
**Document:** PostgreSQL Database Design
**Database:** `careersaathi_ai`
**PostgreSQL Version:** 17.11
**Last Updated:** August 2026

---

## 1. Overview

CareerSaathi AI will use PostgreSQL as its relational database. The database
will store user accounts, candidate profiles, résumés, extracted skills, job
descriptions, job-match results, interview sessions, answers, evaluations, and
performance reports.

SQLAlchemy will define database models in Python. Alembic will create and
manage database migrations.

Database tables will not be created manually through `psql`.

---

## 2. Database Configuration

The local PostgreSQL configuration is:

| Setting | Value |
|---|---|
| Database name | `careersaathi_ai` |
| Application user | `careersaathi_app` |
| Host | `localhost` |
| Port | `5432` |
| Encoding | UTF-8 |
| Database system | PostgreSQL 17.11 |
| Python driver | Psycopg 3 |
| ORM | SQLAlchemy 2 |
| Migration tool | Alembic |

The backend connection URL will follow this format:

```text
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

Example `.env` configuration:

```env
DATABASE_URL=postgresql+psycopg://careersaathi_app:YOUR_PASSWORD@localhost:5432/careersaathi_ai
```

The actual password must never be added to GitHub.

---

## 3. Database Naming Standards

The database will use the following naming rules:

- Table names will use lowercase plural names.
- Column names will use `snake_case`.
- Primary keys will normally use UUID values.
- Foreign keys will end with `_id`.
- Date and time fields will use UTC timestamps.
- Boolean fields will begin with `is_` or `has_`.
- Table indexes will use clear descriptive names.
- Passwords will only be stored as secure hashes.
- Scores will use values from 0 to 100.

Examples:

```text
users
candidate_profiles
resume_analyses
job_descriptions
interview_sessions
performance_reports
```

---

## 4. Main Database Tables

The initial database will contain these tables:

1. `users`
2. `candidate_profiles`
3. `skills`
4. `candidate_skills`
5. `resumes`
6. `resume_analyses`
7. `resume_skills`
8. `job_descriptions`
9. `job_required_skills`
10. `job_matches`
11. `job_match_skills`
12. `interview_sessions`
13. `interview_questions`
14. `candidate_answers`
15. `answer_evaluations`
16. `performance_reports`

---

## 5. User and Profile Relationships

```mermaid
erDiagram
    USERS ||--o| CANDIDATE_PROFILES : has
    USERS ||--o{ CANDIDATE_SKILLS : selects
    SKILLS ||--o{ CANDIDATE_SKILLS : identifies

    USERS {
        uuid id PK
        varchar full_name
        varchar email UK
        varchar password_hash
        varchar role
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    CANDIDATE_PROFILES {
        uuid id PK
        uuid user_id FK
        varchar education_level
        varchar experience_level
        varchar target_role
        numeric years_experience
        text bio
        timestamptz created_at
        timestamptz updated_at
    }

    SKILLS {
        uuid id PK
        varchar name UK
        varchar category
        varchar normalized_name UK
        timestamptz created_at
    }

    CANDIDATE_SKILLS {
        uuid id PK
        uuid user_id FK
        uuid skill_id FK
        varchar proficiency_level
        integer years_experience
        timestamptz created_at
    }
```

---

## 6. Résumé and Job-Match Relationships

```mermaid
erDiagram
    USERS ||--o{ RESUMES : uploads
    RESUMES ||--o{ RESUME_ANALYSES : receives
    RESUMES ||--o{ RESUME_SKILLS : contains
    SKILLS ||--o{ RESUME_SKILLS : identifies
    USERS ||--o{ JOB_DESCRIPTIONS : creates
    JOB_DESCRIPTIONS ||--o{ JOB_REQUIRED_SKILLS : requires
    SKILLS ||--o{ JOB_REQUIRED_SKILLS : identifies
    RESUMES ||--o{ JOB_MATCHES : compared
    JOB_DESCRIPTIONS ||--o{ JOB_MATCHES : compared
    JOB_MATCHES ||--o{ JOB_MATCH_SKILLS : contains

    RESUMES {
        uuid id PK
        uuid user_id FK
        varchar original_filename
        varchar stored_filename
        varchar file_type
        integer file_size
        varchar storage_path
        boolean is_primary
        timestamptz created_at
    }

    RESUME_ANALYSES {
        uuid id PK
        uuid resume_id FK
        text extracted_text
        jsonb education_data
        jsonb experience_data
        jsonb project_data
        jsonb certification_data
        jsonb suggestions
        varchar status
        timestamptz created_at
    }

    JOB_DESCRIPTIONS {
        uuid id PK
        uuid user_id FK
        varchar job_title
        varchar company_name
        text description_text
        varchar experience_level
        timestamptz created_at
    }

    JOB_MATCHES {
        uuid id PK
        uuid user_id FK
        uuid resume_id FK
        uuid job_description_id FK
        numeric overall_score
        jsonb matched_keywords
        jsonb missing_keywords
        jsonb suggestions
        timestamptz created_at
    }
```

---

## 7. Interview Relationships

```mermaid
erDiagram
    USERS ||--o{ INTERVIEW_SESSIONS : attends
    RESUMES ||--o{ INTERVIEW_SESSIONS : personalizes
    JOB_DESCRIPTIONS ||--o{ INTERVIEW_SESSIONS : targets
    INTERVIEW_SESSIONS ||--o{ INTERVIEW_QUESTIONS : contains
    INTERVIEW_QUESTIONS ||--o| CANDIDATE_ANSWERS : receives
    CANDIDATE_ANSWERS ||--o| ANSWER_EVALUATIONS : receives
    INTERVIEW_SESSIONS ||--o| PERFORMANCE_REPORTS : generates

    INTERVIEW_SESSIONS {
        uuid id PK
        uuid user_id FK
        uuid resume_id FK
        uuid job_description_id FK
        varchar job_role
        varchar interview_type
        varchar difficulty_level
        varchar answer_mode
        varchar status
        integer question_limit
        timestamptz started_at
        timestamptz completed_at
    }

    INTERVIEW_QUESTIONS {
        uuid id PK
        uuid session_id FK
        uuid parent_question_id FK
        text question_text
        varchar question_type
        integer sequence_number
        boolean is_follow_up
        timestamptz created_at
    }

    CANDIDATE_ANSWERS {
        uuid id PK
        uuid question_id FK
        uuid session_id FK
        text answer_text
        text transcript_text
        varchar audio_path
        integer response_time_seconds
        timestamptz submitted_at
    }

    ANSWER_EVALUATIONS {
        uuid id PK
        uuid answer_id FK
        numeric technical_score
        numeric relevance_score
        numeric communication_score
        numeric structure_score
        numeric completeness_score
        text feedback
        jsonb strengths
        jsonb improvements
        timestamptz created_at
    }

    PERFORMANCE_REPORTS {
        uuid id PK
        uuid session_id FK
        uuid user_id FK
        numeric technical_score
        numeric communication_score
        numeric relevance_score
        numeric structure_score
        numeric response_time_score
        numeric overall_score
        text summary
        jsonb strengths
        jsonb weaknesses
        jsonb suggestions
        timestamptz created_at
    }
```

---

## 8. Table Definitions

### 8.1 Users Table

The `users` table stores authentication and basic account information.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `full_name` | VARCHAR(100) | Required |
| `email` | VARCHAR(255) | Required and unique |
| `password_hash` | VARCHAR(255) | Required |
| `role` | VARCHAR(20) | Default `candidate` |
| `is_active` | BOOLEAN | Default `true` |
| `is_email_verified` | BOOLEAN | Default `false` |
| `last_login_at` | TIMESTAMPTZ | Optional |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

The email address will be converted to lowercase before storage.

---

### 8.2 Candidate Profiles Table

The `candidate_profiles` table stores additional candidate information.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Unique foreign key to `users` |
| `phone` | VARCHAR(20) | Optional |
| `city` | VARCHAR(100) | Optional |
| `state` | VARCHAR(100) | Optional |
| `country` | VARCHAR(100) | Default `India` |
| `education_level` | VARCHAR(100) | Optional |
| `experience_level` | VARCHAR(30) | Optional |
| `years_experience` | NUMERIC(4,1) | Default `0` |
| `target_role` | VARCHAR(150) | Optional |
| `headline` | VARCHAR(200) | Optional |
| `bio` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

One user can have only one candidate profile.

---

### 8.3 Skills Table

The `skills` table provides a reusable skill catalogue.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | VARCHAR(100) | Required and unique |
| `normalized_name` | VARCHAR(100) | Required and unique |
| `category` | VARCHAR(100) | Optional |
| `description` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |

Examples of skill categories include programming, databases, cloud, data
science, communication, and project management.

---

### 8.4 Candidate Skills Table

The `candidate_skills` table connects users with skills.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key to `users` |
| `skill_id` | UUID | Foreign key to `skills` |
| `proficiency_level` | VARCHAR(30) | Optional |
| `years_experience` | NUMERIC(4,1) | Optional |
| `created_at` | TIMESTAMPTZ | Required |

The combination of `user_id` and `skill_id` must be unique.

---

### 8.5 Résumés Table

The `resumes` table stores résumé file information.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key to `users` |
| `original_filename` | VARCHAR(255) | Required |
| `stored_filename` | VARCHAR(255) | Required and unique |
| `file_type` | VARCHAR(20) | PDF or DOCX |
| `mime_type` | VARCHAR(100) | Required |
| `file_size` | INTEGER | Required |
| `storage_path` | TEXT | Required |
| `checksum` | VARCHAR(128) | Optional |
| `is_primary` | BOOLEAN | Default `false` |
| `processing_status` | VARCHAR(30) | Default `pending` |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

A user may upload multiple résumés but should have only one primary résumé at a
time.

---

### 8.6 Résumé Analyses Table

The `resume_analyses` table stores extracted and analysed résumé information.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `resume_id` | UUID | Foreign key to `resumes` |
| `extracted_text` | TEXT | Required |
| `education_data` | JSONB | Default empty list |
| `experience_data` | JSONB | Default empty list |
| `project_data` | JSONB | Default empty list |
| `certification_data` | JSONB | Default empty list |
| `contact_data` | JSONB | Default empty object |
| `suggestions` | JSONB | Default empty list |
| `analysis_version` | VARCHAR(30) | Required |
| `status` | VARCHAR(30) | Required |
| `error_message` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

Separate analysis records allow a résumé to be analysed again after the
analysis logic is improved.

---

### 8.7 Résumé Skills Table

The `resume_skills` table connects extracted résumé skills with the skill
catalogue.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `resume_id` | UUID | Foreign key to `resumes` |
| `skill_id` | UUID | Foreign key to `skills` |
| `confidence_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `source_text` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |

The combination of `resume_id` and `skill_id` must be unique.

The confidence score represents extraction confidence and not the candidate's
actual level of expertise.

---

### 8.8 Job Descriptions Table

The `job_descriptions` table stores job requirements provided by candidates.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key to `users` |
| `job_title` | VARCHAR(150) | Required |
| `company_name` | VARCHAR(150) | Optional |
| `description_text` | TEXT | Required |
| `experience_level` | VARCHAR(30) | Optional |
| `location` | VARCHAR(150) | Optional |
| `source_url` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

---

### 8.9 Job Required Skills Table

The `job_required_skills` table stores skills extracted from job descriptions.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `job_description_id` | UUID | Foreign key |
| `skill_id` | UUID | Foreign key to `skills` |
| `importance_level` | VARCHAR(30) | Required or preferred |
| `weight` | NUMERIC(5,2) | Match-score weight |
| `source_text` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |

The combination of `job_description_id` and `skill_id` must be unique.

---

### 8.10 Job Matches Table

The `job_matches` table stores résumé and job-comparison results.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key to `users` |
| `resume_id` | UUID | Foreign key to `resumes` |
| `job_description_id` | UUID | Foreign key |
| `skills_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `experience_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `keyword_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `overall_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `matched_keywords` | JSONB | Default empty list |
| `missing_keywords` | JSONB | Default empty list |
| `suggestions` | JSONB | Default empty list |
| `analysis_summary` | TEXT | Optional |
| `created_at` | TIMESTAMPTZ | Required |

---

### 8.11 Job-Match Skills Table

The `job_match_skills` table stores skill-level matching details.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `job_match_id` | UUID | Foreign key to `job_matches` |
| `skill_id` | UUID | Foreign key to `skills` |
| `match_status` | VARCHAR(30) | Matched, partial, or missing |
| `resume_confidence` | NUMERIC(5,2) | Optional |
| `required_weight` | NUMERIC(5,2) | Optional |
| `created_at` | TIMESTAMPTZ | Required |

The combination of `job_match_id` and `skill_id` must be unique.

---

### 8.12 Interview Sessions Table

The `interview_sessions` table stores interview configuration and progress.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | Foreign key to `users` |
| `resume_id` | UUID | Optional foreign key |
| `job_description_id` | UUID | Optional foreign key |
| `job_match_id` | UUID | Optional foreign key |
| `job_role` | VARCHAR(150) | Required |
| `experience_level` | VARCHAR(30) | Required |
| `interview_type` | VARCHAR(30) | Required |
| `difficulty_level` | VARCHAR(30) | Required |
| `answer_mode` | VARCHAR(20) | Text or voice |
| `question_limit` | INTEGER | Required |
| `status` | VARCHAR(30) | Required |
| `current_question_number` | INTEGER | Default `0` |
| `started_at` | TIMESTAMPTZ | Optional |
| `completed_at` | TIMESTAMPTZ | Optional |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

Possible session statuses include:

- `created`
- `in_progress`
- `completed`
- `cancelled`
- `failed`

---

### 8.13 Interview Questions Table

The `interview_questions` table stores generated questions.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key |
| `parent_question_id` | UUID | Optional self-reference |
| `question_text` | TEXT | Required |
| `question_type` | VARCHAR(30) | Required |
| `difficulty_level` | VARCHAR(30) | Required |
| `sequence_number` | INTEGER | Required |
| `is_follow_up` | BOOLEAN | Default `false` |
| `expected_topics` | JSONB | Default empty list |
| `created_at` | TIMESTAMPTZ | Required |

`parent_question_id` connects a follow-up question with the question or answer
that caused it to be generated.

---

### 8.14 Candidate Answers Table

The `candidate_answers` table stores text and voice answers.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | Foreign key |
| `question_id` | UUID | Unique foreign key |
| `answer_text` | TEXT | Required after submission |
| `transcript_text` | TEXT | Optional |
| `audio_path` | TEXT | Optional |
| `response_time_seconds` | INTEGER | Required |
| `answer_mode` | VARCHAR(20) | Text or voice |
| `started_at` | TIMESTAMPTZ | Optional |
| `submitted_at` | TIMESTAMPTZ | Required |
| `created_at` | TIMESTAMPTZ | Required |

One question can have one final submitted answer in the initial version.

---

### 8.15 Answer Evaluations Table

The `answer_evaluations` table stores question-level evaluation results.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `answer_id` | UUID | Unique foreign key |
| `technical_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `relevance_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `communication_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `structure_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `completeness_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `overall_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `feedback` | TEXT | Required |
| `strengths` | JSONB | Default empty list |
| `improvements` | JSONB | Default empty list |
| `evaluation_details` | JSONB | Default empty object |
| `created_at` | TIMESTAMPTZ | Required |

---

### 8.16 Performance Reports Table

The `performance_reports` table stores final interview reports.

| Column | Data Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `session_id` | UUID | Unique foreign key |
| `user_id` | UUID | Foreign key to `users` |
| `technical_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `communication_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `relevance_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `structure_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `response_time_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `overall_score` | NUMERIC(5,2) | Value from 0 to 100 |
| `summary` | TEXT | Required |
| `strengths` | JSONB | Default empty list |
| `weaknesses` | JSONB | Default empty list |
| `suggestions` | JSONB | Default empty list |
| `created_at` | TIMESTAMPTZ | Required |
| `updated_at` | TIMESTAMPTZ | Required |

---

## 9. Main Relationships

| Parent | Child | Relationship |
|---|---|---|
| User | Candidate profile | One-to-one |
| User | Candidate skills | One-to-many |
| User | Résumés | One-to-many |
| User | Job descriptions | One-to-many |
| User | Job matches | One-to-many |
| User | Interview sessions | One-to-many |
| User | Performance reports | One-to-many |
| Résumé | Résumé analyses | One-to-many |
| Résumé | Résumé skills | One-to-many |
| Job description | Required skills | One-to-many |
| Résumé and job description | Job matches | Many comparisons |
| Interview session | Questions | One-to-many |
| Question | Answer | One-to-one |
| Answer | Evaluation | One-to-one |
| Interview session | Performance report | One-to-one |

---

## 10. Database Constraints

The database will apply the following rules:

- Email addresses must be unique.
- Skill normalized names must be unique.
- One user can have only one candidate profile.
- Duplicate candidate skills will not be allowed.
- Duplicate résumé skills will not be allowed.
- Duplicate job-required skills will not be allowed.
- One question can have only one final answer.
- One answer can have only one evaluation.
- One completed interview can have only one final report.
- Scores must remain between 0 and 100.
- Question limits and sequence numbers must be positive.
- Foreign-key values must reference valid records.
- Required fields cannot contain null values.

---

## 11. Database Indexes

Indexes will be added for frequently searched fields.

Planned indexes include:

- Unique index on `users.email`
- Index on `users.role`
- Index on `resumes.user_id`
- Index on `resumes.created_at`
- Index on `resume_analyses.resume_id`
- Index on `skills.normalized_name`
- Index on `job_descriptions.user_id`
- Index on `job_matches.user_id`
- Index on `job_matches.resume_id`
- Index on `interview_sessions.user_id`
- Index on `interview_sessions.status`
- Index on `interview_sessions.created_at`
- Index on `interview_questions.session_id`
- Index on `candidate_answers.session_id`
- Index on `performance_reports.user_id`
- Index on `performance_reports.created_at`

Indexes will improve dashboard, history, résumé, job-match, and interview
queries.

---

## 12. Data Ownership and Security

Every user-owned record will be connected directly or indirectly to a user.

The backend will verify ownership before allowing a candidate to:

- View a résumé
- Delete a résumé
- View a job description
- View a job-match result
- Open an interview session
- Submit an interview answer
- View a performance report
- Delete personal history

The application will not trust a user ID received from the frontend. It will
use the authenticated user's ID from the verified authentication token.

---

## 13. Data Deletion Rules

Planned deletion behaviour includes:

- Deleting a user removes their owned personal records.
- Deleting a résumé removes its analyses and extracted résumé skills.
- Interview history may preserve a résumé reference as null after résumé
  deletion.
- Deleting a job description removes related matching records.
- Deleting an interview removes its questions, answers, evaluations, and
  report.
- Shared skill-catalogue records will not be removed automatically.
- Temporary audio files will be deleted after transcription when possible.

Deletion behaviour will be implemented through foreign-key rules and
application services.

---

## 14. Timestamp Rules

Important tables will contain:

```text
created_at
updated_at
```

Time values will be stored in UTC using `TIMESTAMPTZ`.

The frontend will convert UTC timestamps into the user's local display time.

---

## 15. JSONB Usage

PostgreSQL JSONB fields will be used only for flexible structured information,
including:

- Education entries
- Project entries
- Certifications
- AI suggestions
- Strength lists
- Weakness lists
- Evaluation details
- Matched and missing keywords

Core relationships, users, skills, sessions, questions, answers, and scores
will remain in relational columns.

---

## 16. Migration Strategy

Alembic will manage all database-structure changes.

The migration process will be:

```text
Update SQLAlchemy Model
        ↓
Generate Alembic Migration
        ↓
Review Migration File
        ↓
Apply Migration
        ↓
Run Database Tests
```

Common commands will include:

```powershell
alembic revision --autogenerate -m "migration description"
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```

Migration files will be committed to GitHub.

---

## 17. Seed Data

The project may use seed data for:

- Common technical skills
- Communication skills
- Job roles
- Interview categories
- Difficulty levels
- Example job descriptions

Seed data will not contain real candidate résumés or sensitive personal
information.

---

## 18. Backup and Recovery

During development, important database changes will be stored through Alembic
migrations.

Before deployment updates, the production database should be backed up.

Example PostgreSQL backup command:

```powershell
pg_dump -U careersaathi_app -h localhost -d careersaathi_ai -F c -f careersaathi_ai.backup
```

Example restoration command:

```powershell
pg_restore -U careersaathi_app -h localhost -d careersaathi_ai careersaathi_ai.backup
```

Production backup procedures will depend on the selected managed PostgreSQL
provider.

---

## 19. Database Testing

Database testing will verify:

- Successful database connection
- Table creation through migrations
- Unique email validation
- Foreign-key relationships
- User ownership rules
- Score constraints
- Create, read, update, and delete operations
- Transaction rollback
- Résumé-analysis storage
- Job-match storage
- Interview-session storage
- Performance-report generation

Tests will use a separate test database or isolated test transactions.

---

## 20. Database Design Summary

CareerSaathi AI will use a structured PostgreSQL database that supports:

```text
Users and Profiles
        ↓
Résumés and Skills
        ↓
Job Descriptions and Matches
        ↓
Interview Sessions
        ↓
Questions and Answers
        ↓
Evaluations and Reports
```

This design keeps candidate records connected, supports secure ownership
checks, and allows the system to grow without replacing the main database.

---

© 2026 CareerSaathi AI Project Documentation