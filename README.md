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

## Assessment Notes

### 1. What was wrong, what was fixed, and what was left

#### What was wrong and how I fixed it:
* **Admin could see other companies' data (`dashboard.py`):** The `/dashboard` route checked if the user was an admin, but didn't check which company they belonged to. An admin at Northwind could change `org_id=2` in the URL and see Bluepeak's private scores and risks. I added a check `if m.org_id != org_id: raise HTTPException(403, "Forbidden")` to block this.
* **Lead managers missed senior questions (`questions.py`):** The code checked `if seniority < min_seniority`. Because these are strings, Python compared them alphabetically. Since `'lead'` comes before `'senior'` in the alphabet, Python thought leads were less senior than seniors and skipped their questions! I fixed it by mapping the levels to numbers (`junior: 1, mid: 2, senior: 3, lead: 4`) so it compares actual rank.
* **Dashboard averages were broken (`dashboard.py`):** The code was adding up all raw question points and dividing by the total number of people in the department (even those who hadn't taken the test). This gave impossible scores like `7.0` on a 1-5 scale and dragged down departments where only a few people answered. I fixed it by calculating each person's average score first, and then averaging only the people who actually took the test.
* **Duplicate grading rules (`dashboard.py`):** The dashboard had a copy-pasted `level_for()` function with lower score cutoffs than the official `maturity_level()` in `utils.py`. An employee and their boss saw two different grades for the exact same score. I deleted the duplicate function and imported `maturity_level` from `utils.py` so both pages use the exact same rule.
* **AI scoring could crash the server (`scoring.py`):** In `mock_ai_responses.json`, some AI responses have markdown blocks like ```` ```json ````, scores written as words like `"four"`, or scores like `7`. A bare `json.loads` would crash with a 500 error. I cleaned the markdown, added a `try/except` fallback, and clamped scores between 1 and 5 so the server never crashes on bad AI output.
* **Fixed broken test (`test_api.py`):** The test `test_admin_cannot_see_other_org` was querying `org_id=1` (the admin's own org). I updated it to query `org_id=2` and assert `403`.

#### What I deliberately left:
* **Role-based recommendations:** Next steps are currently hardcoded per job role in `reports.py`. I left them as-is because making up fake rules without real guidance from HR/Product wouldn't be useful.
* **SQLite:** Kept SQLite because it's simple to run locally and works fine for a pilot. No need to add extra database setup yet.

---

### 2. Client request and questions for them

#### What I implemented:
* **Right to Delete:** Added a `DELETE /reports/me` API and a red "Delete my data" button on the report page. When clicked, it deletes the employee's answers from the database and immediately updates the dashboard.
* **Clean Retakes:** Made sure that if someone retakes the diagnostic, their old answers are cleared first so questions don't repeat on their report.

#### Questions for Northwind HR:
1. **Departments with fewer than 5 people:** When a small team has fewer than 5 responses, should we completely hide that department from the dashboard, or show it grouped under a combined label like "Other teams"?
2. **Deleting data:** When someone deletes their answers, should their past score be completely removed from the department average, or should their score stay anonymously for company history?
3. **Audit log:** Does your legal team need a record/log of who deleted their data and when?

---

### 3. My own feature: "Explain My AI Score"

* **The Problem:** The report only showed a single number like `Average score: 2.58` and `Exploring`. Employees had no way of knowing which answers lowered their score, or what the AI thought about their written answer.
* **Why I picked it:** The database was already saving each question's score, answer, and the AI's written feedback, but the report wasn't showing it. I added a simple "Score breakdown" list on the report page showing each question, the points earned, and the AI's direct feedback. It makes the score transparent and easy for employees to understand.

---

### 4. How I used AI tools and where they got it wrong

* **How I used AI:** I used an AI tool as a quick sounding board to look through the project structure, check FastAPI syntax, and brainstorm edge cases.
* **Where it got it wrong:** When I looked at the prompt in `llm.py`, the prompt says `Return JSON: {"score": <1-5>}`. The AI told me that because the prompt specifies JSON, the model output would always be valid JSON and didn't need extra cleanup. But looking at `mock_ai_responses.json`, real models still return markdown blocks like ```` ```json ```` and string words like `"four"`. Relying only on prompt instructions was wrong, so I added manual cleanup in `scoring.py` to prevent crashes.


