# SPM Countdown Auto-Poster

Automated daily countdown bot for the Sijil Pelajaran Malaysia (SPM) examinations. Every day at 00:00 (Malaysia Time / UTC+8), this bot posts the countdown image along with the target captions to Threads and Twitter (X).

---

## Project Structure

```
├── .github/
│   └── workflows/
│       └── spm_countdown.yml    # GitHub Actions workflow
├── images/
│   ├── 100.png                   # Countdown images (100 down to 0)
│   └── ...
├── .env.example                 # Environment variables template
├── .gitignore                   # Git exclusion rules
├── LICENSE                      # Project license
├── post_countdown.py            # Main automation and posting script
├── requirements.txt             # Python dependencies
└── test_countdown.py            # Unit test suite
```

---

## Setup & Configuration

### 1. Local Installation

```bash
git clone https://github.com/WelsonLiong/spmcountdown.git
cd spmcountdown
pip install -r requirements.txt
```

### 2. Environment Variables

Create a local `.env` file from the template:

```bash
cp .env.example .env
```

Fill in the required tokens:

```ini
THREADS_ACCESS_TOKEN=your_long_lived_threads_access_token_here
THREADS_USER_ID=me

TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
```

### 3. Adjusting the Target Exam Date

To set or update the target exam date, modify `TARGET_DATE` directly in `post_countdown.py`:

```python
TARGET_DATE = date(2026, 11, 23)
```

### 4. GitHub Repository Secrets

Under your GitHub repository **Settings** > **Secrets and variables** > **Actions**, add:

- `THREADS_ACCESS_TOKEN` (Long-Lived Meta Threads Access Token)
- `THREADS_USER_ID` (Default: `me`)
- `GH_PAT` (GitHub Personal Access Token with `repo` scope — allows GitHub Actions to automatically update `THREADS_ACCESS_TOKEN` when refreshed on Day 50)
- `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET` (Optional if Twitter is enabled)

---

## Countdown Window & Token Auto-Refresh

- **Countdown Window**: Active between 100 days remaining and 0 days remaining. If triggered earlier than 100 days, it safely exits without errors.
- **Automated Token Refresh (Day 50)**:
  - Meta Threads long-lived access tokens expire after 60 days.
  - When the countdown reaches 50 days remaining, the script calls Meta's official token refresh endpoint (`GET https://graph.threads.com/refresh_access_token?grant_type=th_refresh_token&access_token=...`).
  - This renews the token for another 60 days, covering the remaining 50 days to Day 0.
  - If `GH_PAT` is configured in repository secrets, GitHub Actions automatically writes the renewed token back into `secrets.THREADS_ACCESS_TOKEN` using `gh secret set`.

---

## Automation via External Cron (00:00 Daily UTC+8)

To trigger the GitHub Action every day at 00:00 UTC+8 (Malaysia Time), use a free web cron service (e.g., [cron-job.org](https://cron-job.org/)) because GitHub Actions automation is not reliable:

1. Create a GitHub Personal Access Token (PAT) with `repo` / `workflow` permissions at [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens).
2. Create a new cron job in [cron-job.org](https://cron-job.org/):
   - **URL**: `https://api.github.com/repos/WelsonLiong/spmcountdown/actions/workflows/spm_countdown.yml/dispatches`
   - **Schedule**: Every day at `00:00` (Timezone: `Asia/Kuala_Lumpur (UTC+8)`)
   - **Request Method**: `POST`
   - **Headers**:
     - `Authorization`: `Bearer <YOUR_GITHUB_PAT>`
     - `Accept`: `application/vnd.github+json`
     - `User-Agent`: `SPM-Countdown-Cron`
   - **Request Body**:
     ```json
     {
       "ref": "main"
     }
     ```

---

## Verification & Testing

Run unit tests:

```bash
python test_countdown.py
```

Run a dry run for today:

```bash
python post_countdown.py --dry-run
```

Simulate a specific date:

```bash
python post_countdown.py --dry-run --date 2026-11-22
```
