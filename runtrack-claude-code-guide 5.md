# 🤖 RunTrack — Claude Code Developer Guide

> How to build this project using AI efficiently — save tokens, stay in context, ship faster
> **This is a skill that will matter more than the app itself.**

-----

## Why This Guide Exists

Most people use AI like a search engine — one question at a time, no memory, no
structure. That’s the expensive, slow way. The engineers who stand out use AI like
a **senior collaborator who has read the entire codebase** — because they set it up
that way.

This guide teaches you how to do that for RunTrack. Every pattern here is used by
real engineering teams at companies like Anthropic, Abnormal AI, and incident.io.
At 15, knowing this puts you ahead of most adults.

-----

## Part 1 — How Claude Code Actually Works

### The Most Important Thing: Context Window

Claude Code holds your **entire conversation in memory** — every message, every file
it reads, every command output. This fills up fast. When it fills up, Claude starts
forgetting earlier instructions and making more mistakes.

**Think of it like RAM in a computer.** Your job is to manage it.

```
Context window = finite memory
Every file Claude reads = costs tokens
Every long output = costs tokens
When it fills up = quality drops
```

### The Golden Rules

|Rule                                          |Why                                          |
|----------------------------------------------|---------------------------------------------|
|Start a new session for each phase            |Don’t carry Phase 2 context into Phase 5     |
|Use CLAUDE.md to replace repeated explanations|Write it once, load it every session for free|
|Give Claude a way to verify its own work      |Tests > you checking manually                |
|Explore first, plan second, code third        |Never let Claude jump straight to coding     |
|Reference files with `@` not descriptions     |`@app.py` beats “the main Flask file”        |
|Keep prompts specific, not vague              |Vague = more back-and-forth = more tokens    |

-----

## Part 2 — Project Folder Structure for Claude Code

This structure is designed so Claude always knows where everything is and
never has to go searching.

```
runtrack/
│
├── CLAUDE.md                  ← 🔑 Claude reads this EVERY session automatically
├── SPEC.md                    ← Full project spec (Claude writes this in Phase 0)
├── PROGRESS.md                ← Running log of what's done (you update this)
│
├── .claude/
│   └── commands/              ← Custom slash commands (reusable prompts)
│       ├── add-route.md       ← /add-route command
│       ├── add-test.md        ← /add-test command
│       └── check-db.md        ← /check-db command
│
├── app.py                     ← Main Flask app
├── database.py                ← All DB functions
├── models.py                  ← Data classes / types
├── requirements.txt
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── add_time.html
│   ├── team.html
│   └── login.html
│
├── static/
│   ├── style.css
│   └── chart.js
│
├── tests/
│   ├── test_database.py       ← DB function tests
│   ├── test_routes.py         ← Flask route tests
│   └── test_utils.py          ← Time conversion tests
│
└── docs/
    ├── data-model.md          ← DB schema reference
    ├── api-routes.md          ← All Flask routes listed
    └── decisions.md           ← Why you made certain choices
```

### Why `docs/` matters for Claude

Every session, Claude can read `docs/data-model.md` in one line instead of
scanning the entire database. This is how you save tokens at scale.

-----

## Part 3 — The CLAUDE.md File (Write This First)

CLAUDE.md is a special file that Claude reads at the start of every conversation.
It serves as an onboarding guide — every session starts with this context already
loaded, eliminating the need to explain basic project information repeatedly.

CLAUDE.md is loaded into context every single session. Every line consumes
context window budget. Think of it like onboarding a new developer — you wouldn’t
hand them a 50-page document on their first day. Give them the essentials and point
to detailed docs when needed.

Keep your CLAUDE.md under 60 lines. Claude actively filters what it follows rather
than treating everything as a persistent command — frontier models follow roughly
150–200 instructions before compliance drops, and Claude Code’s own system prompt
takes up about 50 of those slots already.

### Your CLAUDE.md (copy this into your project root)

```markdown
# RunTrack — Claude Code Context

## What this project is
A Flask web app for tracking running performance for a high school track team.
Athletes log race times. Coach sees team dashboard. Charts show improvement over time.

## Tech stack
- Python 3.11 + Flask
- SQLite (local dev) / PostgreSQL (Render.com production)
- Chart.js for charts (loaded from CDN)
- werkzeug for password hashing
- flask-login for sessions
- Deployed on Render.com (free tier)

## Key files
- app.py — all Flask routes
- database.py — all DB functions (get_db, init_db, helpers)
- docs/data-model.md — full DB schema reference
- docs/api-routes.md — all routes listed
- PROGRESS.md — current status and what's done

## Critical rules
- Always store time as SECONDS (float). Convert to MM:SS only in templates.
- Never store plain text passwords — use werkzeug generate_password_hash
- SQLite for local. PostgreSQL for production via DATABASE_URL env var.
- Run tests after every change: `python -m pytest tests/ -v`
- After any DB schema change, update docs/data-model.md

## Coding style
- Functions have one-line docstrings
- Flask routes are grouped by feature (auth, athlete, coach, import)
- Error handling: return JSON with {"error": "message"} for API routes
- HTML errors: flash() then redirect, never raw error pages

## Do not
- Add new packages without updating requirements.txt
- Modify the DB schema without updating docs/data-model.md
- Write more than 50 lines per function — split it
```

-----

## Part 4 — Phase-by-Phase Claude Code Prompts

Each prompt below is written to be **copy-paste ready**. They are designed to:

- Be specific enough that Claude doesn’t waste tokens clarifying
- Include a verification step so Claude checks its own work
- Reference files directly with `@` instead of descriptions
- Stay focused on one task per session

-----

### 🔵 PHASE 0 — Spec Writing Session

**Goal:** Have Claude interview you and write a complete spec before any code exists.

#### Prompt 0.1 — Generate the project spec

```
I'm building a web app called RunTrack. Before writing any code, I need a
complete spec. Interview me using questions to understand:
- Who the users are and what they need
- The 5 core features for V1 (nothing more)
- The data model (what gets stored)
- What's explicitly OUT of scope for V1
- How success will be measured

Ask me one question at a time. Dig into hard edge cases I might not have
considered. When we've covered everything, write the complete spec to SPEC.md.
Use clear sections. End with an end-to-end verification step that proves the
app works.
```

**After this session:** Read SPEC.md. Edit anything that’s wrong. This is your
source of truth for the whole summer.

-----

### 🟢 PHASE 1 — Setup Session

**Goal:** Working Flask app, GitHub connected, folder structure in place.

> Start a **new session** for this phase.

#### Prompt 1.1 — Scaffold the project

```
I'm starting a new Flask project called RunTrack. Read @SPEC.md and @CLAUDE.md
for context.

Set up the complete project scaffold:
1. Create the folder structure from CLAUDE.md (app.py, database.py, templates/,
   static/, tests/, docs/)
2. Create a working Flask "Hello World" in app.py
3. Create requirements.txt with: flask, flask-login, werkzeug, psycopg2-binary,
   gunicorn, pytest
4. Create a .gitignore for Python (include *.db, __pycache__, .env, venv/)
5. Create empty placeholder files: models.py, docs/data-model.md,
   docs/api-routes.md, docs/decisions.md, PROGRESS.md
6. Create tests/test_utils.py with one passing dummy test

After setup, run `python app.py` and confirm it starts without errors.
Then run `python -m pytest tests/ -v` and confirm tests pass.
```

#### Prompt 1.2 — Initialize Git

```
The project is running. Now:
1. Run `git init` in the project root
2. Run `git add .` then `git commit -m "Initial scaffold: Flask Hello World"`
3. Tell me the exact commands to connect this to a GitHub repo I'll create
   manually at github.com/[my-username]/runtrack

Do not create the GitHub repo — I'll do that. Just give me the two commands
to run after I create it.
```

-----

### 🟡 PHASE 2 — Database Session

**Goal:** Tables created, seed data in, helper functions tested.

> Start a **new session** for this phase.

#### Prompt 2.1 — Build the database layer

```
Read @CLAUDE.md and @SPEC.md for context.

Build the complete database layer in database.py:

Tables needed:
- athletes: id, name, grade (int), specialty (text), athletic_net_id (text)
- results: id, athlete_id (FK), meet_name, meet_date, event, time_seconds (REAL),
  session_type ('meet' or 'practice'), split_400, split_800, split_1200,
  notes, is_personal_best (boolean, default 0)
- users: id, username (unique), password_hash, role ('athlete' or 'coach'),
  athlete_id (FK nullable)

Also write these helper functions in database.py:
- seconds_to_display(seconds) → "4:32.10"
- display_to_seconds(time_str) → 272.1
- update_personal_bests(athlete_id, event) → recalculates PB after new entry

After writing, write tests in tests/test_utils.py for:
- seconds_to_display(272.1) == "4:32.10"
- display_to_seconds("4:32.10") == 272.1
- Round-trip: display_to_seconds(seconds_to_display(x)) == x for x in [60.0, 272.1, 3600.0]

Run `python -m pytest tests/ -v` and fix any failures before stopping.
Then update docs/data-model.md with the schema.
```

#### Prompt 2.2 — Add seed data

```
Read @database.py and @docs/data-model.md.

Write a script called seed.py that:
1. Calls init_db() to create all tables
2. Inserts 3 fake athletes: "Alex Chen" grade 11 specialty "1600m",
   "Jordan Smith" grade 10 specialty "5K XC", "Sam Rivera" grade 11 specialty "800m"
3. Inserts 8 fake results spread across different dates, events, and session types
   (mix of meet and practice, some PBs, some not)
4. Prints "Seeded successfully — X athletes, Y results"

Run it with `python seed.py` and confirm the output is correct.
Do not add seed.py to the main app — it's a dev-only utility.
```

-----

### 🟠 PHASE 3 — Feature Build Sessions

> Each feature = its own session. Never combine two features in one session.

#### Prompt 3.1 — Time entry form (Week 4)

```
Read @CLAUDE.md, @database.py, @docs/data-model.md, and @templates/base.html.

Build the time entry feature:

1. In app.py, add two routes:
   - GET /add → renders templates/add_time.html
   - POST /add → validates input, saves to results table, redirects to /athlete/<id>

2. In templates/add_time.html, build a form with fields:
   - Athlete (dropdown from athletes table)
   - Event (dropdown: "800m", "1600m", "3200m", "5K XC", "10K XC")
   - Time (text input, format hint: MM:SS.ms e.g. 4:32.10)
   - Meet name (text)
   - Date (date picker)
   - Session type (radio: Meet / Practice)
   - Notes (optional textarea)

3. Validation rules (show friendly error messages, not crashes):
   - Time must be parseable by display_to_seconds()
   - Date cannot be in the future
   - Event and athlete cannot be empty

4. Write a test in tests/test_routes.py that POSTs valid data and confirms
   a 302 redirect happens and the result appears in the DB.

Run `python -m pytest tests/ -v` and fix failures before stopping.
Update docs/api-routes.md with the two new routes.
```

#### Prompt 3.2 — Athlete dashboard + chart (Week 5)

```
Read @CLAUDE.md, @app.py, @database.py, @docs/data-model.md.

Build the athlete dashboard:

1. Route GET /athlete/<int:athlete_id>:
   - Fetch athlete row and all their results ordered by date DESC
   - Mark is_personal_best correctly
   - Render templates/dashboard.html

2. Route GET /athlete/<int:athlete_id>/chart-data?event=1600m:
   - Return JSON: {"labels": ["2026-06-01", ...], "times": [272.1, ...]}
   - Filter by event query param

3. In templates/dashboard.html:
   - Table showing all results (formatted MM:SS, PBs marked with ⭐)
   - Dropdown to select event
   - Chart.js line chart (load from CDN, do NOT download locally)
   - Y-axis must show MM:SS not raw seconds
   - Y-axis must be REVERSED (lower time = top of chart = better)
   - Chart updates when dropdown changes (use fetch() to call chart-data endpoint)

4. Write tests:
   - /athlete/1 returns 200 and contains athlete name
   - /athlete/1/chart-data?event=1600m returns valid JSON with labels and times arrays

Run tests. Update docs/api-routes.md.
```

#### Prompt 3.3 — Meet vs practice comparison (Week 6)

```
Read @CLAUDE.md, @app.py, @database.py, @templates/dashboard.html.

Build the comparison feature:

1. Route GET /athlete/<int:athlete_id>/compare?event=1600m:
   - Query meet times and practice times separately
   - Calculate: avg meet time, avg practice time, gap between them
   - Render templates/compare.html

2. In templates/compare.html:
   - Two-line Chart.js chart: red line = meets, blue line = practice
   - Summary stats box: avg meet, avg practice, gap (in seconds and percentage)
   - Event dropdown that reloads the page with new event param

3. Add a "Compare →" button on dashboard.html linking to /athlete/<id>/compare

4. Write a test: /athlete/1/compare?event=1600m returns 200

Run tests. Update docs/api-routes.md.
```

-----

### 🔴 PHASE 4 — Login System Session

> This is the hardest phase. Budget 2 sessions if needed.

#### Prompt 4.1 — Build authentication

```
Read @CLAUDE.md, @app.py, @database.py, @docs/data-model.md.

Add a complete login system using flask-login:

1. In database.py, add a User class that implements flask-login's UserMixin.
   Load user by ID and by username.

2. In app.py:
   - Initialize LoginManager
   - Route GET/POST /login → validate credentials, set session, redirect to dashboard
   - Route GET /logout → clear session, redirect to /login
   - Route GET /register → form to create new athlete account (coach creates these)

3. Protect routes:
   - /athlete/<id> — requires login, athlete can only see their own id
     (coach can see any id)
   - /add — requires login
   - /team — requires login AND role == 'coach'

4. Password rules: hash with generate_password_hash, verify with check_password_hash.
   Never store or log plain text passwords.

5. Tests:
   - Unauthenticated /athlete/1 redirects to /login
   - Correct login redirects to dashboard
   - Athlete A cannot access /athlete/B_id (gets 403)
   - Coach can access any athlete id

Run `python -m pytest tests/ -v`. Fix all failures before stopping.
Update docs/api-routes.md with auth routes.
```

#### Prompt 4.2 — Coach team view

```
Read @CLAUDE.md, @app.py, @database.py, @templates/base.html.

Build the coach team dashboard:

Route GET /team (coach role only):
- List all athletes with: name, grade, specialty, their PB for each event
- Each athlete name links to /athlete/<id>
- Sort by: athlete grade, then name
- Show a summary row at bottom: team fastest time per event

Template templates/team.html:
- Clean table layout
- PBs shown as MM:SS
- Link to /add to log times for any athlete
- If no results yet for an athlete, show "—" not an error

Test: logged-in coach gets 200 on /team. Logged-in athlete gets 403.

Run tests. Commit with message: "feat: coach team dashboard with role-based access"
```

-----

### 🟣 PHASE 5 — Deploy Session

> This session is about infrastructure, not features.

#### Prompt 5.1 — Prepare for production

```
Read @CLAUDE.md and @requirements.txt.

Prepare RunTrack for deployment to Render.com:

1. Create a Procfile in project root with: web: gunicorn app:app

2. In database.py, update get_db() to check for DATABASE_URL environment variable:
   - If DATABASE_URL exists: connect to PostgreSQL using psycopg2
   - If not: use SQLite (local dev)
   Use os.environ.get('DATABASE_URL')

3. In app.py, set app.secret_key from environment:
   app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-insecure-key')

4. Create a .env.example file (NOT .env) showing required variables:
   DATABASE_URL=postgresql://...
   SECRET_KEY=your-secret-key-here

5. Confirm .env is in .gitignore (never commit secrets)

6. Run `python -m pytest tests/ -v` to confirm nothing broke.

7. Write the exact steps I need to follow on Render.com to deploy —
   in plain English, step by step.
```

#### Prompt 5.2 — Post-deploy verification

```
The app is live at [paste your Render URL here].

Verify the deployment works:
1. Fetch the home page and confirm it returns 200
2. Check that /login loads
3. List any errors visible in the response

Then give me a checklist of manual tests to run in the browser to confirm
the full app works on production before I share it with teammates.
```

-----

### ⚡ PHASE 6 — CSV Import Session

#### Prompt 6.1 — Build Athletic.net import

```
Read @CLAUDE.md, @app.py, @database.py, @docs/data-model.md.

Build a CSV import feature for Athletic.net results:

Route GET/POST /import (requires login):
- GET: render templates/import.html with a file upload form
- POST: accept a CSV file upload, parse it, insert results for the logged-in athlete

The Athletic.net Data Extractor Chrome Extension exports CSVs with columns:
Date, Meet, Event, Mark (time as "4:32.10"), Place, Team

Map these to our DB columns:
- Date → meet_date
- Meet → meet_name
- Event → event (map "1 Mile Run" → "1600m", "5000 Meters" → "5K XC", etc.)
- Mark → time_seconds via display_to_seconds()
- session_type → default to "meet" for imported data

After import:
- Call update_personal_bests() for each event that was imported
- Flash message: "Imported X results successfully. Y rows skipped."
- Skip and log (don't crash) any rows where time parsing fails

Write a test that creates a sample CSV in memory and POSTs it to /import,
confirming results appear in the DB.

Run tests. Update docs/api-routes.md.
```

-----

## Part 5 — Token-Saving Techniques

### Technique 1: The `@` File Reference

Instead of copying code into your prompt, use `@`:

```
❌ Expensive:
"Here is my database.py file: [pastes 200 lines]
Can you add a function to..."

✅ Efficient:
"Read @database.py and add a function to..."
```

### Technique 2: Reference Docs, Not Code

After Phase 2, Claude should read `docs/data-model.md` instead of scanning
`database.py` every time:

```
❌ Expensive:
"Read @database.py and @app.py to understand the schema..."

✅ Efficient:
"Read @docs/data-model.md for the schema, then add a route to @app.py that..."
```

### Technique 3: Plan Mode for Risky Changes

Before touching login, routing, or database schema — always plan first.

```
Step 1 — Enter plan mode (Shift+Tab or type /plan):
"Read @app.py and @database.py. I want to add role-based access control.
What files need to change? What's the safest order to make changes?
List everything — don't write any code yet."

Step 2 — Read the plan. Edit it if anything's wrong.

Step 3 — Exit plan mode and say:
"Implement the plan we just discussed. Run tests after each file change."
```

### Technique 4: One Feature Per Session

```
❌ One big session (context fills, quality drops):
Session: Build login + dashboard + charts + CSV import

✅ One feature per session (clean context every time):
Session 1: Build login system
Session 2: Build dashboard
Session 3: Build charts
Session 4: Build CSV import
```

### Technique 5: Always Give Claude a Test to Run

Claude stops when the work looks done. Without a check it can run, “looks done”
is the only signal available. Give Claude something that produces a pass or fail,
and the loop closes on its own — Claude does the work, runs the check, reads the
result, and iterates until the check passes.

End every prompt with:

```
"Run python -m pytest tests/ -v and fix any failures before stopping."
```

### Technique 6: Commit After Every Session

This forces a clean stopping point and gives you a rollback if the next session
goes wrong.

```
At the end of every session, say:
"Commit all changes with a descriptive message following this format:
feat: [what was added]
Then show me the git log --oneline so I can confirm."
```

-----

## Part 6 — PROGRESS.md Template

Update this file manually at the end of each session. It costs almost no tokens
and gives Claude instant orientation in the next session.

```markdown
# RunTrack — Progress Log

## Current Status
Phase 3 — Week 5 in progress

## What's Done ✅
- [x] Phase 0: SPEC.md written and approved
- [x] Phase 1: Scaffold, GitHub, Flask running
- [x] Phase 2: DB tables, seed data, helper functions, tests passing
- [x] Phase 3 Week 4: Time entry form + results list
- [ ] Phase 3 Week 5: PB tracker + chart — IN PROGRESS

## Known Issues 🐛
- Time formatting doesn't handle hours (not needed for running)
- /athlete/<id> has no 404 handling yet

## Next Session Goal
Complete the Chart.js line chart on dashboard.html with event dropdown.
Route /athlete/<id>/chart-data is built. Need to wire up the frontend JS.

## Active Routes (see docs/api-routes.md for full list)
- GET /          → home (redirects to /login)
- GET/POST /add  → time entry form ✅
- GET /athlete/<id> → athlete dashboard ✅ (chart in progress)

## Test Status
All 7 tests passing as of last commit (abc1234)
```

-----

## Part 7 — Custom Slash Commands

Claude Code supports custom slash commands stored in `.claude/commands/`.
These let you define reusable prompts that run with a single command.

Save these files in `.claude/commands/` and use them by typing `/add-route` etc.

### `.claude/commands/add-route.md`

```
Read @CLAUDE.md, @app.py, @docs/api-routes.md.

Add a new Flask route with these specs:
$ARGUMENTS

Requirements:
- Follow existing route patterns in app.py
- Add login_required decorator if it touches user data
- Write one test in tests/test_routes.py
- Add the route to docs/api-routes.md
- Run python -m pytest tests/ -v and fix any failures
```

### `.claude/commands/add-test.md`

```
Read @CLAUDE.md and the file specified in $ARGUMENTS.

Write comprehensive tests for the function or route described.
Cover: happy path, edge cases, invalid input.
Place tests in the appropriate file in tests/.
Run python -m pytest tests/ -v and confirm all pass.
```

### `.claude/commands/check-db.md`

```
Read @docs/data-model.md and @database.py.

Check that:
1. All tables in data-model.md exist in init_db()
2. All columns match
3. All FK relationships are correct
4. Helper functions handle edge cases (empty results, None values)

Report any mismatches. Fix them and update data-model.md if the code is correct.
```

-----

## Part 8 — What This Teaches You

By the end of the summer, you’ll have practiced these skills that are genuinely
rare — even among professional engineers:

|Skill                              |Where you practiced it                                    |
|-----------------------------------|----------------------------------------------------------|
|**Context engineering**            |CLAUDE.md, docs/, PROGRESS.md                             |
|**Prompt specificity**             |Every phase prompt in this guide                          |
|**Verification-driven development**|Ending every prompt with “run tests”                      |
|**Plan before code**               |Phase mode prompts in Phase 4                             |
|**Token budget awareness**         |One feature per session rule                              |
|**AI-assisted debugging**          |Giving Claude the error, the file, and the expected output|
|**Structured documentation**       |docs/ folder Claude can read efficiently                  |

These are the same patterns used by the engineers building AI products at the
fastest-growing companies right now. The app gets you on the resume.
The workflow gets you the job.

-----

## Quick Reference Card

Print this and tape it above your desk.

```
┌─────────────────────────────────────────────────────────────┐
│            CLAUDE CODE — RUNTRACK QUICK RULES               │
├─────────────────────────────────────────────────────────────┤
│  START every session:  read @CLAUDE.md and @PROGRESS.md     │
│  USE @filename to reference files, not copy-pasting          │
│  ONE feature per session — start fresh each time            │
│  ALWAYS end with: "run pytest and fix any failures"         │
│  PLAN before coding anything that touches 3+ files          │
│  COMMIT after every session with a descriptive message      │
│  UPDATE PROGRESS.md after every session (takes 2 minutes)   │
│  DOCS first — Claude reads docs/ not source code            │
└─────────────────────────────────────────────────────────────┘
```