# Tech Job Aggregator

A personal job aggregation tool built for Caribbean tech professionals 
seeking remote work opportunities worldwide.

## What it does
- Aggregates remote tech job listings from 6 sources daily
- Filters by category, location scope, and keywords
- Flags jobs restricted to specific regions (US only, EU only, etc.)
- Saves interesting jobs and tracks application status

## Sources
- We Work Remotely
- Remotive
- Himalayas
- Jobicy
- Remote First Jobs
- Real Work From Anywhere

## Tech Stack
- Python — scraping, data cleaning, automation
- SQLite / Turso — cloud database
- Streamlit — web interface
- BeautifulSoup — HTML parsing
- feedparser — RSS feed parsing
- GitHub Actions — scheduled scraping (coming soon)

## Project Structure
- `main.py` — scraper orchestration
- `remote_jobs_rss.py` — RSS feed scrapers and cleaners
- `database.py` — database connection and queries
- `clean_db.py` — category normalization
- `main_app.py` — Streamlit UI
- `schema.sql` — database schema

## Running locally
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Add `.env` file with `TURSO_URL` and `TURSO_TOKEN`
4. Run scraper: `python main.py`
5. Launch app: `streamlit run main_app.py`