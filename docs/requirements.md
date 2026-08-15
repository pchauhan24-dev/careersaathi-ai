# CareerSaathi AI: System Requirements

**Version:** 1.0
**Document:** Functional and Non-Functional Requirements
**Last Updated:** August 2026

---

## 1. Purpose

This document defines the functional and non-functional requirements of
CareerSaathi AI. These requirements will guide the design, development,
testing, and deployment of the application.

CareerSaathi AI combines résumé intelligence, job-description matching, and
AI-powered mock interviews to help students and job seekers improve their job
readiness.

---

## 2. User Roles

### 2.1 Candidate

A candidate can:

- Register and log in.
- Create and update a profile.
- Upload and manage résumés.
- Analyse a résumé.
- Enter a target job description.
- View match scores and missing skills.
- Configure and attend mock interviews.
- Answer questions using text or voice.
- View performance reports.
- Review previous interview sessions.

### 2.2 Administrator

An administrator may be added in a later version to:

- Manage users.
- Manage job roles and skill categories.
- Review system activity.
- Manage reported or invalid content.
- Monitor AI and system usage.

The candidate module will be developed first.

---

## 3. Functional Requirements

### FR-01: User Registration

The system shall allow a new candidate to create an account using a full name,
email address, and password.

### FR-02: User Authentication

The system shall allow registered candidates to log in and log out securely.
Protected pages shall only be available to authenticated users.

### FR-03: Candidate Profile

The system shall allow candidates to create and update profile information,
including education, skills, experience level, and target job role.

### FR-04: Résumé Upload

The system shall allow candidates to upload résumés in PDF or DOCX format. The
system shall validate the file type and file size before processing it.

### FR-05: Résumé Text Extraction

The system shall extract readable text from uploaded résumés and identify
important résumé sections.

### FR-06: Candidate Information Extraction

The system shall identify information such as:

- Skills
- Education
- Work experience
- Projects
- Certifications
- Contact information

### FR-07: Job-Description Input

The system shall allow candidates to enter or paste a job description for a
target position.

### FR-08: Résumé and Job Matching

The system shall compare the résumé with the job description and calculate a
match score.

### FR-09: Skill-Gap Analysis

The system shall show matched skills, missing skills, and important keywords
that may improve the candidate's suitability for the selected role.

### FR-10: Résumé Suggestions

The system shall generate understandable and personalized résumé improvement
suggestions.

### FR-11: Interview Configuration

The system shall allow candidates to select:

- Job role
- Experience level
- Interview type
- Difficulty level
- Answer mode
- Number of questions

### FR-12: AI Question Generation

The system shall generate interview questions based on the candidate's résumé,
skills, job description, and selected interview settings.

### FR-13: Dynamic Follow-Up Questions

The system shall generate relevant follow-up questions according to the
candidate's previous answers.

### FR-14: Text-Based Answers

The system shall allow candidates to type and submit interview answers.

### FR-15: Voice-Based Answers

The system shall allow candidates to record interview answers using a
microphone.

### FR-16: Speech-to-Text Conversion

The system shall convert recorded voice answers into text before evaluation.

### FR-17: Answer Evaluation

The system shall evaluate candidate answers using defined scoring criteria,
including:

- Technical knowledge
- Answer relevance
- Communication quality
- Answer structure
- Response completeness
- Response time

### FR-18: Performance Scoring

The system shall calculate category scores and an overall interview score.

### FR-19: Performance Report

The system shall generate a report containing:

- Overall score
- Category-wise scores
- Strengths
- Weaknesses
- Question-level feedback
- Personalized improvement suggestions

### FR-20: Interview History

The system shall save completed interview sessions and allow candidates to
review previous results.

### FR-21: Dashboard

The system shall provide a dashboard showing recent résumé analyses, interview
sessions, performance scores, and progress.

### FR-22: Data Management

The system shall ensure that candidates can access only their own profiles,
résumés, analyses, interviews, answers, and reports.

---

## 4. Non-Functional Requirements

### NFR-01: Security

- Passwords shall be stored using secure password hashing.
- Authentication tokens shall use secure HTTP-only cookies.
- Private API routes shall require authentication.
- Uploaded files shall be validated.
- Secrets and database passwords shall not be stored in GitHub.
- User input shall be validated before processing.

### NFR-02: Performance

- Normal API responses should complete within a reasonable time.
- AI-processing screens shall show loading progress.
- Long-running operations shall not freeze the user interface.
- Database queries shall use suitable indexes.

### NFR-03: Usability

- The interface shall use clear and understandable language.
- Important actions shall provide success or error messages.
- Forms shall display useful validation messages.
- The interview screen shall provide clear instructions.

### NFR-04: Responsiveness

The frontend shall work correctly on desktop computers, laptops, tablets, and
mobile devices.

### NFR-05: Reliability

The system shall handle invalid files, failed AI requests, interrupted
recordings, and database errors without crashing.

### NFR-06: Maintainability

The frontend and backend shall use a modular folder structure. Code shall
follow consistent naming, formatting, documentation, and testing standards.

### NFR-07: Scalability

The architecture shall allow new interview types, AI providers, job roles,
languages, and evaluation criteria to be added later.

### NFR-08: Privacy

- Résumés and interview answers shall be treated as private information.
- Users shall not be able to access another candidate's information.
- Audio recordings shall not be retained longer than necessary.
- Sensitive information shall not be included in application logs.

### NFR-09: Compatibility

The web application shall support current versions of major browsers,
including Chrome, Edge, Firefox, and Safari.

### NFR-10: Accessibility

Forms, navigation, buttons, error messages, and interview controls should be
usable with keyboards and common assistive technologies.

---

## 5. Data Requirements

The system shall use PostgreSQL to store structured application data.

The database shall store:

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

Every important record shall contain creation and update timestamps. Records
belonging to a candidate shall be connected to the correct user account.

---

## 6. Software Requirements

The development environment requires:

- Windows 10 or later
- Visual Studio Code
- Git and GitHub
- Node.js and npm
- Python and pip
- PostgreSQL 17
- pgAdmin 4
- Modern web browser
- Internet connection for AI services

---

## 7. System Constraints

- AI features may require an internet connection.
- AI output may sometimes contain incomplete or inaccurate information.
- Voice accuracy may be affected by noise, microphone quality, and
  pronunciation.
- The MVP will support PDF and DOCX résumés only.
- Facial-expression analysis will not be included in the initial version.
- AI-generated scores will provide practice guidance and will not represent an
  official hiring decision.
- API usage may be limited by the selected AI provider's cost and rate limits.

---

## 8. Assumptions

- Candidates will provide accurate profile information.
- Uploaded résumés will contain readable text.
- Candidates will grant microphone permission for voice interviews.
- The PostgreSQL server will be available during local development.
- AI and speech services will be correctly configured before use.
- Users will review AI-generated suggestions before applying them.

---

## 9. Acceptance Criteria

The initial version will be considered functional when a candidate can:

1. Register and log in securely.
2. Create and update a candidate profile.
3. Upload a valid PDF or DOCX résumé.
4. Extract information from the résumé.
5. Compare the résumé with a job description.
6. View a match score and missing skills.
7. Configure a mock interview.
8. Answer AI-generated questions through text or voice.
9. Receive relevant follow-up questions.
10. Complete the interview and receive a performance report.
11. View saved analyses and previous interview sessions.
12. Use the deployed application from another supported device.

---

## 10. Ethical Use

CareerSaathi AI shall provide career-preparation guidance and practice
feedback. It shall not make final employment decisions or guarantee job
selection.

The system shall avoid evaluating candidates using protected personal
characteristics. Scores shall be based on résumé-job relevance, answer content,
communication structure, and defined interview criteria.

---

© 2026 CareerSaathi AI Project Documentation