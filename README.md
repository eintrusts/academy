# EinTrust Academy

The learning management system (LMS) for [EinTrust](https://www.eintrusts.com): sustainability, ESG and climate
training for clients, partners and the public.

Built with [Streamlit](https://streamlit.io) and SQLite, so it runs on Streamlit Community Cloud or any small server.

## Features

**Learners**
- Course catalogue with search and filters (category, level, free/paid)
- Course pages with outcomes, curriculum, instructor and price
- Free enrollment, Razorpay checkout or an enrollment request for paid courses
- Course player with articles (Markdown), videos (YouTube/Vimeo links or uploads), PDFs and downloads, external links and quizzes
- Progress tracking with a progress bar per course, and automatic move to the next module
- Graded quizzes with a pass mark, answer review and explanations
- PDF certificates on completion, with a unique ID and a public verification page (`/verify?id=EINT-…`)
- Profile editing and password change

**Admins**
- Dashboard: learners, enrollments, completions, revenue, monthly enrollments, per-course performance
- Course authoring: details, categories, levels, pricing, cover image, publish/draft, pass mark
- Module authoring: add, edit, reorder and delete; attach files; build quizzes
- Learner management: search, CSV export, manual enrollment, password reset, deactivate accounts
- Enrollment requests (approve/reject), transaction log, issued certificates
- One-click **starter catalogue**: four draft courses (ESG fundamentals, GHG accounting, BRSR, net zero) with lessons and quizzes, for your consultants to review and publish

## Run locally

```bash
pip install -r requirements.txt
mkdir -p .streamlit && cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit it
streamlit run academy.py
```

Sign in as admin from **Sign in → Admin** with the `ADMIN_PASSWORD` from your secrets. Then open
**Manage courses → Starter content** to load the sample catalogue.

## Configuration

Set these in `.streamlit/secrets.toml`, in the Streamlit Cloud *Secrets* panel, or as environment variables:

| Setting | Required | Purpose |
|---|---|---|
| `ADMIN_PASSWORD` | yes | Password for the admin console. Admin sign-in is disabled until it is set. |
| `APP_URL` | recommended | Public URL of the app (e.g. `https://academy.eintrusts.com`). Printed on certificates for verification, and used as the payment return URL. |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | optional | Turn on online checkout for paid courses via Razorpay Payment Links. Without them, paid courses take enrollment requests for admins to approve (invoice or bank transfer). |
| `ACADEMY_DB_PATH` | optional | Location of the SQLite database (default `academy.db`). |

Branding (name, logo, website, course categories) lives in `lms/config.py`.

## Deploying

- **Streamlit Community Cloud:** point it at `academy.py` and add the secrets. Its file system is not
  persistent, so the SQLite database is reset whenever the app restarts or redeploys. Use it for demos only,
  or switch to a hosted database before going live.
- **Any VM or container (recommended for production):** run `streamlit run academy.py --server.port 8501`
  behind a reverse proxy with HTTPS (for example at `academy.eintrusts.com`), and set `ACADEMY_DB_PATH` to a
  persistent, backed-up volume.

## Upgrading from the earlier prototype

An existing `academy.db` from the earlier version upgrades in place on first start. New columns and tables are
added, duplicate enrollments are merged, and courses stay published. Learners' plaintext passwords are rehashed
(PBKDF2-SHA256) the first time each learner signs in.

## Project layout

```
academy.py              entry point: page config and navigation
lms/config.py           branding and secrets
lms/db.py               schema, migrations and all queries
lms/auth.py             password hashing and validation
lms/certificates.py     PDF certificates
lms/payments.py         Razorpay and manual enrollment requests
lms/seed.py             starter sustainability courses
lms/ui.py               shared styling and components
lms/views/              public, learner and admin pages
tests/                  pytest suite
```

Run the tests with `pip install pytest && pytest`.

## Known limitations

- Sessions are held by Streamlit, so reloading the browser tab signs the user out.
- Learners have no self-service password reset by email. Admins reset passwords from **Learners**.
- Uploaded files are stored in the database. For large video libraries, host the videos on YouTube or Vimeo
  (unlisted) and paste the link instead.
