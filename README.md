# Hospitalist Job Bot

A personal job-search assistant for finding Hospitalist / Hospital Medicine
physician openings in the **Orange County, CA** area (Irvine, Mission Viejo,
Newport Beach, and nearby cities), scoring them against your preferences
(7-on/7-off, day shift, full-time / part-time / per-diem), drafting a
tailored cover letter from your CV, and staging everything for your review
before anything is sent to an employer.

## Why "review, then apply" instead of fully automatic submission?

This tool **does not blind-submit applications**. Instead it:

1. Searches configured sources for matching openings.
2. Scores and de-duplicates them.
3. Drafts a tailored cover letter per opening.
4. Writes everything to a review queue (`data/jobs.db` + a generated
   `data/review.md` report) for you to look at.
5. Only jobs you mark `approved` get submitted (by email, when the posting
   provides an application email address; otherwise the bot hands you the
   direct application link + drafted materials to submit yourself).

Reasons for this design, not just caution for its own sake:

- Most job boards' Terms of Service prohibit automated bots that submit
  applications without a human in the loop, and many use CAPTCHAs / bot
  detection that a script legitimately cannot and should not try to bypass.
- A 14-year hospitalist with partner status is a strong, specific candidate
  — a templated blind auto-apply is more likely to hurt your candidacy than
  help it if it goes out with the wrong hospital name or a generic pitch.
  A 10-second human review avoids that risk entirely while still saving you
  the job-hunting legwork.

## How it works

```
hospitalist_job_bot/
  config.py        # loads config.yaml + secrets from environment
  models.py         # JobPosting / ApplicationStatus data model
  matcher.py         # scores & filters postings against your criteria
  store.py            # SQLite-backed dedupe + status tracking
  coverletter.py        # drafts a tailored cover letter from resume.yaml
  review.py               # builds data/review.md and applies approvals
  sources/
    base.py               # JobSource interface
    adzuna.py               # Adzuna job-search API (general aggregator)
    workday.py               # Workday CXS API (many hospital systems use Workday
                              # for their public career sites; this calls the
                              # same public JSON endpoint the career page itself
                              # loads in your browser)
  apply/
    email_apply.py            # sends an application email w/ resume attached
  cli.py                        # `python -m hospitalist_job_bot ...`
config.yaml                      # search criteria, locations, sources
resume.yaml                       # your background, used in cover letters
.github/workflows/job_search.yml   # optional daily scheduled run via GitHub Actions
```

## Setup

1. **Add your CV.** Drop your resume PDF/DOCX into `resume/` (see
   `resume/README.md`) and fill in `resume.yaml` with the structured facts
   used in the drafted cover letters (years of experience, current
   employer, board certification, etc. — pre-filled with what you told me;
   double check it).

2. **Install dependencies.**

   ```bash
   pip install -r requirements.txt
   ```

3. **Get an Adzuna API key (free).** Sign up at
   https://developer.adzuna.com/ and set:

   ```bash
   export ADZUNA_APP_ID=...
   export ADZUNA_APP_KEY=...
   ```

   (Adzuna aggregates postings from Indeed, hospital systems, and physician
   job boards, and has a documented, ToS-compliant API — unlike scraping
   LinkedIn/Indeed directly, which their terms prohibit.)

4. **(Optional) Configure email sending**, for the "apply by email" path:

   ```bash
   export SMTP_HOST=smtp.gmail.com
   export SMTP_PORT=587
   export SMTP_USER=usman.ali@gmail.com
   export SMTP_PASSWORD=...       # use an app password, not your real password
   ```

5. **Run a search:**

   ```bash
   python -m hospitalist_job_bot search
   python -m hospitalist_job_bot review     # writes data/review.md
   ```

   Open `data/review.md`, and for jobs you like, mark them approved:

   ```bash
   python -m hospitalist_job_bot approve <job_id>
   python -m hospitalist_job_bot apply <job_id>
   ```

## Configuring your criteria

Edit `config.yaml`. It's pre-filled with:

- **Titles:** Hospitalist, Hospital Medicine Physician, Hospital Medicine
- **Locations:** Irvine, Mission Viejo, Newport Beach, Orange, Santa Ana,
  Anaheim, Costa Mesa, Fountain Valley, Laguna Hills, Huntington Beach,
  Tustin, Garden Grove, Westminster, Lake Forest — all Orange County, CA
- **Employment types:** full_time, part_time, per_diem
- **Schedule preference (boosts score, doesn't exclude):** "7 on / 7 off",
  day shift
- **Excluded employers:** your current employer (Providence Torrance / San
  Pedro) is excluded by default since you're looking to relocate, not stay.

## Running it on a schedule

`.github/workflows/job_search.yml` runs `search` + `review` once a day via
GitHub Actions and commits the updated `data/review.md`, so you get a daily
digest without keeping a server running. Add `ADZUNA_APP_ID` /
`ADZUNA_APP_KEY` (and SMTP secrets if you want email digests) as repository
secrets to enable it.

## Limitations, honestly stated

- Direct scraping of Indeed/LinkedIn is intentionally **not** implemented —
  both explicitly prohibit automated access in their Terms of Service.
  Adzuna is used instead because it's a licensed aggregator with a public
  API that legitimately includes postings from those and other boards.
- Automatic *submission* only works for postings with a listed application
  email. Most hospital-system ATS platforms (Workday, Taleo, iCIMS) require
  filling a multi-step web form, often behind a CAPTCHA — the bot will not
  attempt to bypass that. For those, it gives you the direct link and your
  drafted materials so you can submit in under a minute.
