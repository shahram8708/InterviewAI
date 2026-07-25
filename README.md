# InterviewAI Pro

> Your personal AI interviewer — voice-first, resume-aware, and company-specific. Practice like it's real, improve with data.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-8E75FF?style=for-the-badge&logo=google&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-Enabled-5A0FC8?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Live Demo:** `http://localhost:5000` after install · **PWA Ready** · **Dark / Light / High Contrast**

---

## 📑 Table of Contents

- [About The Project](#-about-the-project)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#a-prerequisites)
  - [Installation](#b-installation)
  - [Environment Variables](#c-environment-variables)
  - [Running the Project](#d-running-the-project)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Acknowledgements](#-acknowledgements)
- [Contact / Author](#-contact--author)

---

## 📖 About The Project

I built InterviewAI Pro because mock interviews are usually generic, awkward, and forget everything you said 2 minutes ago. This platform fixes that.

You log in with just your name and your own Gemini API key (encrypted at rest), upload a resume PDF, and the system extracts your skills, experience, projects, and career level using Gemini vision + PyMuPDF. Then you configure a target role, company, experience level, interview type, and interviewer persona — from a Friendly Recruiter to a strict FAANG-style interrogator.

From there it feels real: Web Speech API captures your voice, SpeechSynthesis speaks the interviewer's questions back, and a compressed context memory keeps the last 2 exchanges verbatim while summarizing older ones. Every answer gets evaluated live for strong/average/weak/incorrect,Filler-word detection, WPM, and confidence signals. When you're done, you get a full report with 6 category scores, strengths, weaknesses, suggested answers, and company-specific recommendations.

It's for job seekers, freshers, career switchers, and anyone who wants measurable progress — with streaks, badges, history, and a progress dashboard that never invents data. If you have no interviews yet, it honestly shows empty states.

## ✨ Key Features

- **Gemini 2.5 Flash-powered interviews** — dynamic question generation, answer evaluation, and final report scoring, all persona-aware
- **Resume intelligence** — PDF validation (type + max pages 10), text extraction via PyMuPDF, structured JSON parsing (skills, education, experience, projects, certifications, technologies, strengths, career_level, summary)
- **Company research with Search Grounding** — uses `google_search` tool to fetch culture, interview patterns, common questions, hiring process for your target company
- **Voice-first practice** — Web Speech API SpeechRecognition (continuous + interim) with 3s silence auto-submit, speechSynthesis with persona-tuned rate/pitch, fallback to text input
- **Compressed memory context** — `context_service.py` keeps running strengths/weaknesses, compresses old Q&A into gist to preserve token budget
- **Real-time speech analytics** — filler words (`umm, uhh, like, basically, you know...`), WPM, confidence indicators, session-level aggregation
- **Scoring & feedback engine** — 6 dimensions (overall, communication, technical, confidence, problem_solving, leadership, behavioral) + objective WPM/filler adjustments
- **Gamification that is truthful** — 9 badges (`First Steps`, `High Five`, `Perfect Ten`, `Perfectionist 95+`, `On Fire 3-day`, `Unstoppable 7-day`, `Paced Perfectly 140-160 WPM`, `Smooth Talker <1% fillers`, `Company Expert 3x same company`) derived from real `BadgeDefinition` catalog
- **Progress & analytics** — score trend (last 20), weekly grouping, streak calc (today/yesterday tolerant), category averages, skill gap deduping
- **Security-first** — Fernet encryption for API keys, Talisman CSP + HSTS, rate limiting (login 10/hour, resume 10/day, api 60/min), CSP nonce, log redaction filter for `AIza*`
- **PWA + Accessibility** — `manifest.json` standalone, `sw.js` cache-first for static / network-first for /api, dark/light/system themes, high contrast, reduced motion support, skip-to-content link

## 🧰 Tech Stack

### Frontend
- **Bootstrap 5.3.3** + **Bootstrap Icons 1.11.3** (CDN via `cdn.jsdelivr.net`)
- **Custom CSS** `app/static/css/main.css` — CSS variables, dark/light themes, glass effects, interview room animations (`pulse-ring`, `waveform`, `mic-pulse`)
- **Vanilla JavaScript** — no frameworks
  - `app.js` — PWA install prompt, theme resolver, high-contrast toggle, CSRF helper, `apiFetch` wrapper
  - `interview.js` — 364 lines: recognition, synthesis, silence timer, transcript bubbles, turn counter, end flow
  - `dashboard.js` — crisp canvas score charts (devicePixelRatio aware) + tooltips
  - `resume.js` — drag & drop zone, 5MB client validation, analyzing state
- **Web Speech API** — `SpeechRecognition` / `webkitSpeechRecognition` + `speechSynthesis`
- **PWA** — `manifest.json` (start_url `/dashboard`, theme `#0A1628`) + `sw.js` (v1 cache: `/`, css, js, manifest, icon.svg)

### Backend
- **Flask** (factory in `app/__init__.py`) — blueprints: `auth`, `main`, `resume`, `interview`, `analytics`, `api`, `errors`
- **Flask-SQLAlchemy** — models with composite indexes for analytics
- **Flask-WTF / CSRFProtect** — CSRF with time limit 3600s, exempt only for `/api`
- **Flask-Session** — filesystem sessions, signed, HttpOnly, Lax/Strict, permanent 86400s
- **Flask-Limiter** — `get_remote_address`, memory storage, per-env limits
- **Flask-Talisman** — CSP `default-src 'self'`, scripts inline allowed, fonts from `gstatic`, frame DENY, HSTS off in debug
- **python-dotenv** — loaded FIRST in `run.py` before app import
- **cryptography Fernet** — encryption key from env, key redaction logging filter
- **google-genai** — `genai.Client(api_key=...)`, `gemini-2.5-flash`, `response_mime_type="application/json"`, tools `[GoogleSearch()]`
- **PyMuPDF (fitz)** — PDF open, page count check (max 10 default), text extraction + image render at 200 DPI
- **Pillow** — image handling dependency
- **WTForms** — future form validation
- **Gunicorn** — production server listed in requirements

### Database
- **SQLite by default** — `sqlite:///instance/app.db` via `DATABASE_URL`
- **SQLAlchemy models:**
  - `User` — full_name, encrypted_api_key (LargeBinary), theme, high_contrast, speech_locale
  - `ResumeProfile` — to_context_dict(), is_active toggle, JSON arrays for skills/education/experience
  - `InterviewSession` — composite indexes on (user_id, status), (user_id, completed_at), (user_id, started_at), `compressed_context` JSON, filler maps
  - `InterviewTurn` — sequence_number, question_category, filler_words_in_turn JSON, word_count, speaking_duration
  - `FeedbackReport` — 6 scores + strengths/weaknesses/missed/suggested/company_recs/improvement/resume_suggestions
  - `ProgressSnapshot` — indexed (user_id, period_start_date), weekly aggregation
  - `Badge` — indexed (user_id, badge_type) + (user_id, earned_at)
  - `SkillGap` — severity, related_session
  - `CompanyPack` — curated packs
- Auto `db.create_all()` + `_ensure_indexes(checkfirst=True)` on startup

### DevOps / Other
- **Config hierarchy** — `Config`, `DevelopmentConfig`, `ProductionConfig` + `config_map`
- **Logging** — RotatingFileHandler 10MB x5, WARNING file / INFO console, KeyRedactionFilter
- **Dirs auto-ensured** — `instance/`, `instance/sessions`, `instance/uploads`, `instance/logs`
- **.env.example** — documented template
- **.gitignore** — comprehensive Python/venv/build/logs/instance/env/IDE/OS coverage

## 📁 Project Structure

```text
InterviewAI/
├── run.py                          # Entry point — load_dotenv FIRST, create_app(), host 0.0.0.0:5000, use_reloader=False
├── requirements.txt                # Flask + extensions + genai + PyMuPDF + Pillow + gunicorn
├── .env.example                    # Template for all env vars
├── .gitignore                      # Python, venv, instance, uploads, logs, env, IDE
├── README.md                       # This file
└── app/
    ├── __init__.py                 # App factory: ensure_dirs, init extensions (db/csrf/limiter/sess/talisman + CSP), blueprints, error handlers, template helpers, db init, sw.js route
    ├── config.py                   # Config classes reading env: SECRET_KEY, ENCRYPTION_KEY (Fernet), DATABASE_URL (sqlite:///instance/app.db), SESSION, MAX_CONTENT_LENGTH, RATE_LIMITS, GEMINI_MODEL=gemini-2.5-flash
    ├── extensions.py               # Singleton instances: db, csrf, limiter(key=get_remote_address), sess, talisman
    ├── models/
    │   ├── __init__.py             # Re-exports all models for create_all discovery
    │   ├── user.py                 # User: id, full_name, encrypted_api_key, theme, high_contrast, speech_locale, voice_speed, relations
    │   ├── resume.py               # ResumeProfile: original_filename, is_active, skills/education/experience/projects JSON, to_context_dict()
    │   ├── interview.py            # InterviewSession (status, compressed_context, company_research, filler_word_counts, avg_wpm property) + InterviewTurn (sequence_number, evaluation_label, ai_notes)
    │   └── feedback.py             # FeedbackReport, ProgressSnapshot (indexed user+period), Badge (indexed user+badge_type), SkillGap, CompanyPack
    ├── routes/
    │   ├── __init__.py             # empty placeholder
    │   ├── auth.py                 # /login GET/POST (validate name/key, validate_api_key call, encrypt, session fixation clear), /logout, /onboarding/api-key-guide
    │   ├── main.py                 # / (landing or dashboard redirect), /dashboard (stats+recent+badges+skill gaps+trend), /about, /settings (profile/prefs/rotate_key), /security, /offline
    │   ├── resume.py               # /resume/upload GET/POST (validate_pdf, decrypt key, deactivate old, process_resume), /resume/profile GET, /resume/profile/update POST
    │   ├── interview.py            # /interview/configure GET/POST (sanitize + Other->custom logic, personas dict friendly/strict/technical/faang), /interview/start POST (research_company + build_initial_context), /interview/session/<id> GET (status check redirect if completed)
    │   ├── analytics.py            # /interview/session/<id>/report (builds report_data with categories, qa_pairs, wpm), /history (company/type/status filters), /progress (category averages + weekly), /achievements (build_achievements)
    │   ├── api.py                  # /api/* JSON, login required, CSRF exempt, rate limited — see API docs below
    │   └── errors.py               # handle_400/404/413/500 -> templates/errors/*.html
    ├── services/
    │   ├── __init__.py             # imports analytics_service
    │   ├── gemini_service.py       # get_client(), validate_api_key (minimal OK call), analyze_resume (prompt -> JSON), generate_interview_question (40/30/20/10 distribution rule), evaluate_answer (strong/average/weak/incorrect + follow_up_needed), generate_feedback_report (6 scores + lists), generate_resume_suggestions
    │   ├── resume_service.py       # validate_pdf (extension + fitz open + max pages), convert_pdf_to_images (200 DPI Matrix), process_resume (temp save + text extract + analyze_resume + ResumeProfile create + cleanup)
    │   ├── context_service.py      # build_initial_context (resume.summary + session config), compress_exchange (50 char snippets), update_context (last 2 verbatim, older compressed, running strengths/weaknesses), get_stage (introduction <0% -> resume_discussion <30% -> technical/behavioral <70% -> behavioral <90% -> closing)
    │   ├── research_service.py     # research_company (GenAI + google_search tool, fallback when company N/A)
    │   ├── scoring_service.py      # generate_scores (AI + objective WPM adjustment), calculate_objective_metrics, detect_skill_gaps (<60 thresholds), check_and_award_badges (uses BADGE_DEFINITIONS + get_user_statistics), update_progress_snapshot (ISO week date, fixes datetime vs date bug), calculate_streak
    │   ├── analytics_service.py    # 548 lines — core truth source: get_completed_session_dates, calculate_current_streak (today/yesterday tolerant), longest streak, _get_session_speech_metrics (Python aggregation of JSON filler maps), get_user_statistics (status counts CASE, company max single via group_by lower), get_category_averages, get_score_trend (20 limit), get_weekly_activity (12 weeks buckets), get_recent_activity_comparison (7-day windows), get_recent_sessions (5), get_skill_gap_summary (collapse same skill + count), get_active_resume, build_achievements (progress % calc, sorted locked last)
    │   ├── badge_catalog.py        # frozen BadgeDefinition dataclass, MIN_WORDS_FOR_FLUENCY=50, IDEAL_WPM 140-160, 9 BADGE_DEFINITIONS with lambda conditions + progress lambdas
    │   ├── security_service.py     # encrypt/decrypt_api_key (Fernet via app config), KeyRedactionFilter (regex AIza[0-9A-Za-z-_]{35} -> [REDACTED]), validate_key_format
    │   └── voice_support.py        # FILLER_WORDS list 12 items, count_filler_words (regex word boundary), calculate_wpm, analyze_speech (-> filler_words, wpm, word_count, confidence {has_hesitation, fluent 120-160 & <5% fillers})
    ├── static/
    │   ├── css/main.css            # 704 lines: CSS vars --color-primary-dark #0A1628 ... accent #4FC0D0 cta #F27121, light theme override, high contrast, glass, persona-card selected, interview-room, speaking-indicator pulse-ring, listening-indicator waveform, transcript-bubble interviewer/candidate, mic-button states idle/listening.processing, stage-progress, score-gauge, scrollbar
    │   ├── js/
    │   │   ├── app.js              # PWA beforeinstallprompt, iOS detection, resolveTheme system/dark/light, applyTheme to html+body+modals meta, high contrast toggle, reduced motion, flash auto-dismiss 5s, validation, sw register /static/sw.js, password toggle, esc modal close, smooth scroll, getCSRFToken meta, apiFetch wrapper with X-CSRFToken
    │   │   ├── interview.js        # Live room: Silence 3s, timer, sessionData JSON parse, SpeechRecognition continuous interim, fallback to text, speakText persona rate/pitch + GC guard + failsafe length*100, next-question -> transcript + speak + mic idle, submit-answer, handleResponse (should_continue), end endpoint redirect to report_url, UI transcript bubbles fade-in, mic states pulse-red
    │   │   ├── dashboard.js        # Canvas score-chart: parse dataset.scores JSON, hi-DPI backing, bar width slot logic, gradient accent->primary, resize debounce 150ms, bootstrap tooltips init
    │   │   └── resume.js           # Upload zone dragover class, drop handling DataTransfer, 5MB validation, analyzing-state toggle, profile edit toggle
    │   ├── icons/icon.svg          # PWA icon (192+512)
    │   ├── manifest.json           # name InterviewAI Pro, short_name InterviewAI, start_url /dashboard, display standalone, bg #0A1628
    │   └── sw.js                   # CACHE_NAME v1, ASSETS: /, css, js, manifest, icon; install skipWaiting cache.addAll; activate delete old; fetch: /api network-first offline JSON, /static cache-first, navigate network-first fallback /
    ├── templates/
    │   ├── base.html               # Nav: brand robot icon, Dashboard/Interview/History/Progress/Achievements/Settings/Logout when logged, About/API Key Guide/Login when not, install-pwa btn d-none, theme toggle moon, contrast toggle, flash alerts loop, main block, footer with institution branding conditional, bootstrap 5.3.3 bundle + app.js
    │   ├── main/
    │   │   ├── landing.html        # Hero display-3 Master Your Interview, feature cards AI/ Voice/ Feedback/ Company, how-it-works 4 steps, CTA
    │   │   ├── dashboard.html      # statistics: completed, best, streak, wpm ; recent_sessions cards, active_resume, badges, skill_gaps, score_trend canvas
    │   │   ├── about.html          # conditional branding
    │   │   ├── settings.html       # forms action update_profile/update_prefs/rotate_key, theme selector, speech locale, voice_speed
    │   │   ├── security.html       # explains Fernet, CSP, rate limits, no storage without key
    │   │   └── offline.html        # PWA offline fallback
    │   ├── auth/
    │   │   ├── login.html          # full_name + api_key form, link to guide
    │   │   └── api_key_guide.html  # step-by-step Gemini key creation
    │   ├── resume/
    │   │   ├── upload.html         # dropZone JS drag & drop: uploadContent vs fileSelectedContent, progress bar, PDF only 5MB badge, submit btn disabled until file
    │   │   └── profile.html        # displays skills tags, timeline experience, edit form
    │   ├── interview/
    │   │   ├── configure.html      # job_role select + custom, company_name select + custom, experience_levels loop, interview_types, personas cards (name/desc) + radio
    │   │   ├── confirm.html        # shows persona_name + job_role + company etc. POST to /interview/start
    │   │   └── session.html        # interview-data script type json, micBtn, transcriptArea, micStatus subtitles, timer, confidenceMeter, progressBar, textControls fallback, stopAnsweringBtn, confirmEnd
    │   ├── analytics/
    │   │   ├── report.html         # report dict: role/company/date/overall_score/categories dict Communication..Behavioral, strengths/weaknesses/improvement/wpm/filler_words/company_insights/qa_pairs loop Q+A+feedback+suggested
    │   │   ├── history.html        # sessions loop history-card, filters company/type/status inputs
    │   │   ├── progress.html       # category_averages sorted, weekly_activity buckets, activity comparison, score_trend canvas
    │   │   └── achievements.html   # earned_count/total_count/completion_percent, achievements loop badge-card earned vs grayscale, progress_current/target/percent bar
    │   └── errors/
    │   │       ├── 400.html, 404.html, 413.html, 500.html  # branded error pages, no stack trace
    └── utils/
        ├── __init__.py             # empty
        ├── decorators.py           # login_required (session user_id check -> auth.login), resume_required (active ResumeProfile check -> resume.upload_get)
        ├── helpers.py              # get_current_user (db.session.get), format_duration mm:ss, format_date B d Y, get_score_color >=85 success >=70 warning else danger
        └── validators.py           # validate_name 2-150 regex [\w\s.-], validate_api_key_format 10-100, validate_job_role non-empty <150, validate_company_name <150, sanitize_input strip HTML tags + whitespace normalize
```

## 🚀 Getting Started

### a. Prerequisites

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **pip** — usually bundled with Python
- **Git** — [Download](https://git-scm.com/downloads)
- **A Google Gemini API Key** — create at [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Modern browser** — Chrome/Edge recommended for full Web Speech API support

Check versions:

```bash
python --version
pip --version
git --version
```

### b. Installation

```bash
# 1. Clone the repo
git clone https://github.com/shahram8708/InterviewAI.git
cd InterviewAI

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy env template
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env

# 6. Generate required secrets
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# -> copy output as ENCRYPTION_KEY

# 7. Edit .env (see table below)

# 8. Run
python run.py
```

Open `http://localhost:5000` — DB `instance/app.db` is auto-created on first run.

### c. Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | App mode — `development` enables debug, no HTTPS force | `development` |
| `FLASK_SECRET_KEY` | Flask session signing secret — set to long random string | `a-very-random-64-char-string-here` |
| `ENCRYPTION_KEY` | Fernet key for API key encryption (44-byte base64) — generate via `Fernet.generate_key()` | `kX5mP...==` |
| `DATABASE_URL` | SQLAlchemy URI — defaults to sqlite file | `sqlite:///instance/app.db` |
| `SESSION_TYPE` | Flask-Session backend | `filesystem` |
| `MAX_UPLOAD_SIZE_MB` | Max PDF upload size (MB) — also sets Flask `MAX_CONTENT_LENGTH` | `10` |
| `RATE_LIMIT_LOGIN_PER_HOUR` | Login attempts per IP per hour | `10` |
| `RATE_LIMIT_RESUME_UPLOADS_PER_DAY` | Resume uploads per IP per day | `10` |
| `RATE_LIMIT_API_CALLS_PER_MINUTE` | API calls per minute | `60` |
| `ENABLE_INSTITUTION_BRANDING` | Toggle institutional footer brand | `false` |
| `INSTITUTION_NAME` | Custom footer text when branding enabled | `My University` |

Relevant config defaults from `app/config.py`:
- `GEMINI_MODEL = gemini-2.5-flash`
- `MAX_PDF_PAGES = 10`
- `SESSION_FILE_DIR = instance/sessions`, `UPLOAD_FOLDER = instance/uploads`, `PERMANENT_SESSION_LIFETIME = 86400`
- `RATELIMIT_STORAGE_URI = memory://`

### d. Running the Project

**Development (with debug, no HTTPS force, reloader off intentionally):**

```bash
python run.py
# or
FLASK_ENV=development python run.py
```

App runs on `0.0.0.0:5000` by default, override via `PORT` env.

**Production:**

```bash
# Collect secrets in .env with FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:8000 run:app
# Or with explicit config name:
# gunicorn -w 4 --env FLASK_ENV=production run:app
```

> Note: `run.py` does `load_dotenv()` BEFORE importing `app` — this is intentional so `Config` reads env first. Reloader is disabled to avoid double DB init.

## 💡 Usage

### 1. Login with your own key
Go to `/login`, enter your full name (2-150 chars, alphanumeric + ` . - _`) and Gemini API key. The key is format-validated then verified via a minimal `generate_content` call. On success it's Fernet-encrypted, user is upserted, session cleared/regenerated to prevent fixation, `user_id` stored.

### 2. Upload resume
Visit `/resume/upload`. Drag & drop PDF (client validates type + 5MB). Server validates again with PyMuPDF (openable + `len(doc) <= MAX_PDF_PAGES`). Text extracted via `page.get_text()` loop, sent to Gemini prompt that returns JSON with 9 keys. Any old active resume is deactivated (`is_active=False`), new profile saved with `raw_extracted_text`.

```html
<!-- Drop zone flow from upload.html -->
<div id="dropZone">
  <div id="uploadContent">Drag & drop PDF</div>
  <div id="fileSelectedContent" class="d-none">fileName.pdf</div>
</div>
```

### 3. Configure interview
`/interview/configure` shows: job_role list + custom, company_name list + custom (Other handling), experience_levels `Fresher, 1-2 Years, 3-5 Years, 5+ Years`, interview_types `HR, Technical, Behavioral, System Design, Mixed Round`, personas:

- `friendly`: Friendly Recruiter, encouraging
- `strict`: Strict Hiring Manager, formal
- `technical`: Senior Technical Lead, deep probing
- `faang`: FAANG Interviewer, rigorous analytical

POST to `/interview/configure` validates, sanitizes (`sanitize_input` strips HTML tags), shows confirm screen.

### 4. Live interview loop
POST `/interview/start` triggers:
- `research_company(api_key, company, role, level)` with `google_search` tool, fallback to generic if N/A
- create `InterviewSession status=in_progress total_questions_target=10`
- `build_initial_context(resume, session)` + merge company research
- redirect to `/interview/session/<id>`

Inside `session.html`:
- JS reads `session_data` JSON (id, persona, total_questions)
- `SpeechRecognition continuous interim en-US`, 3s silence auto-submit
- `speakText` with persona rate/pitch: friendly 0.9/1.1, strict 1.0/0.9, else 1.1, plus GC guard
- Flow: `POST /api/interview/<id>/next-question` → TTS → mic idle → answer → `POST /submit-answer` (analyze_speech: filler/WPM) → `evaluate_answer` Gemini → `update_context + stage` → should_continue? → loop or `POST /end` → redirect to report

Text fallback appears if browser has no SpeechRecognition.

### 5. Review feedback
`/interview/session/<id>/report` shows:
- overall_score + 6 categories
- `wpm`, `filler_word_counts` dict sorted, `company_insights`
- `qa_pairs` {question, user_answer, feedback, suggested_answer}
- strengths/weaknesses/improvement_plan
- `turns` ordered by `sequence_number`

### 6. Track progress
- `/dashboard` — `get_user_statistics`, recent 5 sessions, active resume, recent badges, skill gap summary (max 5), score_trend 20 points
- `/history` — filter via query params `?company=Google&type=Technical Interview&status=completed`
- `/progress` — category_averages strongest first, weekly_activity 12 weeks buckets, activity comparison 7-day rolling windows with score_change only when both windows have data
- `/achievements` — completion % + per-badge progress bar, earned_at from Badge table, grayscale when locked

## 📡 API Documentation

All `/api/*` require login (session `user_id`). CSRF exempt for fetch (token still sent via `X-CSRFToken` header from meta). Rate limited.

| Method | URL | Description | Request Body | Response |
|--------|-----|-------------|--------------|----------|
| `POST` | `/api/interview/<session_id>/next-question` | Generate next question via Gemini from compressed_context | `{}` | `200 {question, category, stage, turn_number, total_target}` <br> `400 session not active` <br> `401 auth required` <br> `403 not yours` <br> `404 not found` |
| `POST` | `/api/interview/<session_id>/submit-answer` | Submit answer, analyze speech, evaluate via Gemini, update context/stage/filler | `{"answer": "text", "speaking_duration": 12.5}` | `200 {evaluation: strong/average/weak/incorrect, ai_response, ai_notes, should_continue bool, category, stage, turn_number, total_target, strengths_so_far[], weaknesses_so_far[], speech_metrics: {wpm, filler_words dict, confidence: {has_hesitation, fluent_delivery}}}` |
| `POST` | `/api/interview/<session_id>/end` | Finalize session, generate FeedbackReport, detect skill gaps, award badges, update weekly snapshot | `{}` | `200 {status: completed, report_url: /interview/session/<id>/report, overall_score}` |
| `POST` | `/api/speech/analyze` | Standalone filler/WPM analysis (used for testing) | `{"text": "umm ...", "duration": 10}` | `200 {filler_words dict, wpm int, word_count int, confidence_indicators}` |
| `GET` | `/api/interview/<session_id>/status` | Current session state | — | `200 {status, job_role, company_name, current_stage, turn_count, total_target, started_at iso}` |

**Auth endpoints (non-API but important):**

| Method | URL | Description |
|--------|-----|-------------|
| `GET` `POST` | `/login` | Form `full_name`, `api_key` -> validates format, calls `validate_api_key`, encrypts, upserts User, session regeneration |
| `GET` | `/logout` | `session.clear()` -> redirect landing |
| `GET` | `/onboarding/api-key-guide` | Guide template |

**Interview config:**

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/interview/configure` | `login_required` + `resume_required`, renders configure.html with levels/types/personas |
| `POST` | `/interview/configure` | Validate sanitized job_role/company etc. -> render confirm.html with persona_name |
| `POST` | `/interview/start` | Decrypt key, research_company, create InterviewSession, build_initial_context, commit -> redirect session_view |
| `GET` | `/interview/session/<id>` | Check ownership, if completed redirect to report, else render session.html with `session_data` JSON |

**Analytics & Main:**

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/` | Landing if anon, else redirect dashboard |
| `GET` | `/dashboard` | `login_required` stats + recent + resume + badges + skill gaps + trend |
| `GET` `/POST` | `/settings` | `action=update_profile/update_prefs/rotate_key`, validates, commits |
| `GET` | `/about`, `/security`, `/offline` | Static pages, branding conditional |
| `GET` | `/interview/session/<id>/report` | Build qa_pairs from turns, wpm calc |
| `GET` | `/history?company=&type=&status=` | Filtered list newest first |
| `GET` | `/progress` | Trends + weekly + comparison |
| `GET` | `/achievements` | Evaluates BADGE_DEFINITIONS vs stats |

## ⚙️ Configuration

- `app/config.py` hierarchy: `Config` base reads env with sensible defaults, `DevelopmentConfig` sets `DEBUG True, SESSION_COOKIE_SECURE False`, `ProductionConfig` `DEBUG False, SECURE True, SAMESITE Strict`.
- `app/__init__.py` `_ensure_directories` ensures `instance/sessions`, `instance/uploads` from `SESSION_FILE_DIR` and `UPLOAD_FOLDER`.
- `_init_extensions` builds CSP dict: `default-src self`, `script-src self unsafe-inline cdn.jsdelivr.net fonts.googleapis.com`, `style-src self unsafe-inline cdn.jsdelivr.net fonts.googleapis.com`, `font-src self gstatic cdnjs`, `img-src self data: blob:`, `connect-src self cdn.jsdelivr.net`, `media-src self blob:`, `worker-src self`. Talisman `force_https = not debug`.
- `_register_template_helpers` injects `enable_branding`, `institution_name`, and filters `format_duration`, `format_date`, `score_color`.
- `_configure_logging` creates `instance/logs/app.log` RotatingFileHandler with `KeyRedactionFilter`.
- `UPLOAD_FOLDER` temp saves PDF before `fitz` processing, cleaned in `finally`.
- Frontend theming is client-side localStorage `theme` dark|light|system, applied to `data-bs-theme` attribute + meta theme-color. High contrast toggles `data-high-contrast`.

Customizable without code: env vars (above), `app/templates/main/about.html` branding, `app/services/badge_catalog.py` thresholds (`MIN_WORDS_FOR_FLUENCY_BADGE`, `IDEAL_WPM_RANGE`), `app/services/voice_support.py` `FILLER_WORDS` list, `PERSONAS` dict in `routes/interview.py`, CSS vars in `main.css`.

## 🧪 Testing

No automated test suite was found in the repository (no `tests/`, `pytest.ini`, `test_*.py`, etc.). Honest state!

How to manually test:
```bash
# 1. Login flow
# - Invalid name should flash 400, invalid key format 400, bad key 401

# 2. Resume upload
# - Upload non-PDF -> error, >10 pages -> error
# - Valid PDF -> redirect /resume/profile with extracted fields

# 3. Interview flow
# - Try /interview/configure without resume -> should redirect to /resume/upload (resume_required)
# - Start interview, hit /api/interview/<id>/status -> should show in_progress
# - Speak answer, check transcript bubbles, filler detection
# - End interview -> should award badges if conditions met and create FeedbackReport

# 4. Analytics
# - /dashboard should show zeros when no data, real averages when data exists
# - /achievements progress bars should match badge_catalog conditions

# 5. Speech endpoint
curl -X POST http://localhost:5000/api/speech/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "umm basically like you know", "duration": 5}'
```

Recommended future: add `pytest` + `pytest-flask` for routes, mock Gemini client, test `analytics_service` streak logic.

## 🚀 Deployment

**No Dockerfile or docker-compose.yml present** — but `gunicorn` is ready.

### Option 1: Traditional VPS (Ubuntu)

```bash
sudo apt update && sudo apt install python3-venv nginx -y
git clone https://github.com/shahram8708/InterviewAI.git
cd InterviewAI
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: set FLASK_ENV=production, FLASK_SECRET_KEY random, ENCRYPTION_KEY generated, DATABASE_URL path
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Run with gunicorn
gunicorn -w 4 -b 127.0.0.1:8000 run:app

# Nginx proxy -> 127.0.0.1:8000, set HTTPS, Talisman will force_https in production
```

### Option 2: Render / Railway / Fly.io

- Set env vars in dashboard (include `PORT`, `FLASK_ENV=production`, `FLASK_SECRET_KEY`, `ENCRYPTION_KEY`)
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn run:app`
- Persistence: mount `instance/` volume if provider allows, else use external DB by setting `DATABASE_URL` to Postgres URL (SQLAlchemy supports, but code currently uses SQLite-specific `func.date` — test before switching)

### Option 3: Docker (create this yourself since not in repo)

```dockerfile
# Dockerfile example you can add
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p instance/uploads instance/sessions instance/logs
ENV FLASK_ENV=production
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "run:app"]
```

```bash
docker build -t interviewai .
docker run -p 8000:8000 --env-file .env -v $(pwd)/instance:/app/instance interviewai
```

Cloud notes:
- **Vercel**: Not ideal (filesystem sessions/uploads). Would need rewrite session type + S3 uploads.
- **Heroku**: Use `heroku config:set` for env, add `gunicorn` procfile: `web: gunicorn run:app`
- Security in production: ensure `SESSION_COOKIE_SECURE=True`, `SAMESITE=Strict`, `force_https=True` (already handled when `FLASK_ENV!=development`).

## 🤝 Contributing

Love this direction? Contributions are super welcome.

1. **Fork** the repo — click Fork button on GitHub
2. **Branch**: `git checkout -b feature/amazing-idea`
3. **Commit** small, focused commits: `git commit -m "feat: add weekly email summary"`
4. **Push**: `git push origin feature/amazing-idea`
5. **PR**: Open a Pull Request against `main`, describe what and why, include screenshots for UI changes

Code style:
- Python: PEP8, docstrings for services, keep pure functions in `services/` — they are tested most
- JS: Vanilla, no bundler, keep `apiFetch` for CSRF, avoid inline scripts without `csp_nonce()`
- Templates: Bootstrap utility classes, `text-light` vs `text-body` careful for light theme, use `font-heading` for headings
- Never log raw API keys — `KeyRedactionFilter` does it but be mindful

Bug report template:
```markdown
**Describe bug**: ...
**Steps**: 1. Login 2. Upload ... 3. See error
**Expected**: ...
**Logs**: paste from instance/logs/app.log (keys auto-redacted)
**Env**: browser, python version, FLASK_ENV
```

Feature request:
- Open issue with `enhancement` label, describe user story: "As a fresher, I want ... so that ..."
- Or add TODO comment in code and PR it — I collect them for roadmap

## 🗺️ Roadmap

Based on TODOs, gaps, and obvious next steps from code:

- [x] Resume PDF upload + Gemini structuring
- [x] Company research with Search grounding
- [x] Voice interview loop + compressed context memory
- [x] 6-score feedback report + speech metrics
- [x] Badges, streaks, progress analytics (truthful aggregations)
- [x] PWA manifest + service worker + offline page
- [x] Dark/light/high-contrast/reduced motion accessibility
- [ ] **Tests** — add pytest suite for `analytics_service` (streak logic) and `voice_support`
- [ ] **Resume suggestions persistence** — `generate_resume_suggestions` exists but `resume_suggestions` column in report never populated, integrate in report.html
- [ ] **CompanyPack seeding UI** — model exists, no admin CRUD yet
- [ ] **Audio recording option** — currently transcript only, could save `blob` from `media-src` for replay
- [ ] **Multi-language support** — `speech_locale` in User model + recognition.lang default en-US, but UI still English only
- [ ] **Email reminders for streak** — requires background job (Celery/RQ)
- [ ] **Dockerfile + docker-compose + Postgres optional** — add production-ready container
- [ ] **Import/Export user data** — GDPR leaning, JSON dump of sessions
- [ ] **Enhanced security page** — dynamic display of current CSP/Rate limits from config

## 📄 License

No `LICENSE` file was found in the repository. Defaulting to **All Rights Reserved** to the author until a license is added.

If you are the author: consider adding MIT license to allow reuse:
```text
MIT License — permits use, modification, distribution, private/commercial, with attribution.
```
To add: create `LICENSE` file with MIT text and set badge above to MIT.

## 🙏 Acknowledgements

- **Google Gemini** — `gemini-2.5-flash` via `google-genai` Python SDK is the brain: question gen, answer eval, resume extract, company research with `GoogleSearch()` tool
- **Flask ecosystem** — Flask, SQLAlchemy, WTF, Session, Limiter, Talisman — solid production scaffolding
- **PyMuPDF** — `fitz` for fast PDF text + image rendering without heavy OCR
- **Bootstrap** — 5.3.3 responsive UI, icons 1.11.3, plus custom CSS vars for dark navy theme `#0A1628` → surface `#111827`
- **Web Speech API** — browser-native STT/TTS keeping latency low, no external voice API cost
- **Cryptography** — Fernet symmetric encryption for at-rest key safety
- Inspiration from real FAANG interview loops (persona names reflect that), and from brute-force mock platforms that lack resume awareness

## 📬 Contact / Author

- **GitHub**: [@shahram8708](https://github.com/shahram8708) — author of InterviewAI repo
- **Project Link**: https://github.com/shahram8708/InterviewAI
- **Email**: Not found in repo — use GitHub issues for contact

If you built something cool with this, open a discussion — I'd genuinely love to see your interview reports and what badges people earn first. The first interview is the hardest; this project makes the second one easier.