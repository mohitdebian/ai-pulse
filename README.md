# AI Pulse

AI Pulse helps a company understand how well its people use AI at work, team by team.

- **Employees** sign in, pick their organization, and take a short diagnostic. Questions adapt to their job role and seniority. One open-ended answer is scored by an LLM.
- **Each employee** gets a personal report: maturity level, risks, and next steps for their role.
- **Company admins** see a dashboard of AI maturity by department and the top risks across the company.
- Some users (consultants, group-company HR) belong to **more than one organization** and choose one after login.

This codebase was started by a previous developer who has since left. It runs, but it is unfinished, and we are not confident in all of it.

## Stack

- Backend: Python, FastAPI, SQLAlchemy (SQLite by default)
- Frontend: React (Vite)
- AI: any OpenAI-compatible chat completions endpoint, or mock mode with canned responses

## Run it locally

Backend:

```bash
cd backend
pip install -r requirements.txt
python -m app.seed          # creates demo data, password for all users: pulse123
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Tests:

```bash
cd backend
python -m pytest
```

## Demo accounts (password `pulse123`)

| Email | Organization(s) | Role |
|---|---|---|
| asha@northwind.test | Northwind Logistics | Admin |
| meera@bluepeak.test | Bluepeak Retail | Admin |
| ravi@consult.test | Both | Employee at Northwind, admin at Bluepeak |
| priya@northwind.test | Northwind Logistics | Employee (Support) |
| dev@northwind.test | Northwind Logistics | Employee (Engineering, lead) |

## AI mode

`AI_MODE=mock` (default) returns canned model responses from `backend/data/mock_ai_responses.json`. Like a real model, they are not always well-formed.

`AI_MODE=live` calls `LLM_API_URL` with `LLM_API_KEY` and `LLM_MODEL`.

---

## Engineering Assessment Report

### 1. What was wrong, what was fixed, and what was deliberately left

#### What was wrong & fixed:
* **Multi-tenant IDOR Vulnerability (`backend/app/routes/dashboard.py`):** The `/dashboard` route checked whether the caller was an admin, but never verified whether `m.org_id == org_id`. An admin at Northwind could query `?org_id=2` and inspect Bluepeak Retail's private departments and risks. Fixed by adding a tenant check that enforces `m.org_id == org_id` and returns `403 Forbidden`.
* **Seniority Filtering Bug (`backend/app/services/questions.py`):** Questions were filtered using string inequality (`seniority < min_seniority`). In Python, this compared strings alphabetically, meaning `'lead' < 'senior'` evaluated to `True`, incorrectly skipping senior policy questions for lead managers. Fixed by mapping seniority to integer ranks (`LEVELS = {"junior": 1, "mid": 2, "senior": 3, "lead": 4}`).
* **Dashboard Average Distortion (`backend/app/routes/dashboard.py`):** The dashboard calculated department averages by summing raw individual question points and dividing by total department headcount. This penalized departments with partial participation and generated impossible scores like `7.0` on a 1–5 scale. Fixed using a proper two-step average: computing each respondent's personal 1–5 average first, and then averaging only across active respondents.
* **Conflicting Grading Logic (`backend/app/routes/dashboard.py`):** The dashboard had a private duplicate function `level_for()` with conflicting cutoffs (< 3.5 for Leader) compared to `app.utils.maturity_level` (< 4.0 for Leader). Replaced with a unified import from `utils.py`.
* **Fragile AI Scoring Parser (`backend/app/services/scoring.py`):** Handled unvalidated LLM outputs by stripping markdown code fences (```` ```json ````), safely catching malformed JSON, and clamping scores strictly between 1.0 and 5.0.
* **Test Suite Gaps (`backend/tests/test_api.py`):** Corrected `test_admin_cannot_see_other_org` to assert `403` on cross-tenant requests, and added tests for score breakdown and deletion.

#### What was deliberately left:
* **Static Role-Based Recommendations (`NEXT_STEPS`):** Recommendations are currently hardcoded per job role. Left as-is rather than inventing an arbitrary recommendation engine before product/HR requirements are defined.
* **SQLite Database:** Kept the existing SQLite setup to ensure zero friction for local evaluation, avoiding unnecessary DevOps overhead for a pilot codebase.

---

### 2. How the client's request was handled & questions for them

#### Handled:
* **Right to Delete:** Implemented `DELETE /reports/me` in the backend and a confirmation button in the frontend. Calling this endpoint purges the employee's records from the database, which immediately recalculates and removes their contribution from the admin dashboard.
* **Clean Retakes:** Added a pre-deletion step in `POST /diagnostic/submit` so retaking the diagnostic cleanly overwrites prior attempts rather than duplicating questions.

#### Questions for Northwind HR:
1. **Small Group Aggregation (< 5 employees):** Should departments with fewer than 5 respondents be completely hidden from leadership, or aggregated under a combined "Other Teams" category?
2. **Deletion & Historical Rollups:** When an employee exercises their Right to Delete, should their answers be hard-deleted immediately (which shifts past department averages), or should their contribution be anonymized for historical benchmarking?
3. **Audit Compliance:** Does legal/compliance require an immutable audit trail logging who initiated data deletion and when?

---

### 3. Your own feature: "Explain My AI Score"

* **Problem Solved:** Diagnostic reports previously presented an opaque number (e.g. `Average score: 2.58 — Exploring`) with zero visibility into which questions contributed, what points were earned, or what the AI thought of their open-ended task.
* **Why this was chosen:** The database was already collecting and storing individual question points and qualitative AI feedback, but the report endpoint discarded it. Surfacing an itemized score breakdown makes the score transparent, educational, and actionable for employees without adding third-party dependencies or expensive extra LLM calls.

---

### 4. How AI tools were used, and one place they got it wrong

* **How AI was used:** Used as a pair-programming partner to rapidly trace data flows across routes and identify edge cases in the test suite.
* **Where AI got it wrong:** When asked to fix the department score calculation, AI initially suggested simply changing the denominator to `responded` while still summing the raw question points array. It completely missed the dimensional mismatch: because each employee answers multiple questions, summing raw points still produced inflated scores over 5.0. A human engineer had to spot the error and enforce the proper two-step average (averaging an employee's question points first, then averaging those respondent scores across the department).

