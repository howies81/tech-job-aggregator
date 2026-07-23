-- Job Aggregator Schema
-- Tables: Jobs, Saved Jobs

CREATE TABLE IF NOT EXISTS jobs(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,        -- job title
    company     TEXT,
    loc         TEXT,
    is_remote   INTEGER DEFAULT 0,        -- 0 - False, 1 - True
    location_scope  TEXT,             -- 'local', 'remote_world', 'remote_us_only', 'remote_latam_c'
    job_type    TEXT,                 -- 'FT (Full-Time)', 'CON (Contract)', 'FREE (Freelance)', 'PT (Part-Time)' 
    category    TEXT,                 -- data, software, design, devops
    job_description TEXT,             -- full job desscription
    link        TEXT UNIQUE NOT NULL, -- deduplication key; no 2 jobs share same link
    job_board   TEXT,                 -- 'indeed', 'caribbeanjobs', 'getworktt', 'weworkremotely', 'flexjobs' etc
    date_posted TEXT,
    date_scraped TEXT DEFAULT (DATE('now'))

);

CREATE TABLE IF NOT EXISTS saved_jobs(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL,
    job_status  TEXT DEFAULT 'saved', -- 'saved', 'applied', 'interviewing', 'rejected', 'offer'
    date_saved  TEXT DEFAULT (DATE('now')),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- Index for faster search queries
CREATE INDEX IF NOT EXISTS idx_jobs_title    ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
CREATE INDEX IF NOT EXISTS idx_jobs_source   ON jobs(job_board);
CREATE INDEX IF NOT EXISTS idx_jobs_scope    ON jobs(location_scope);