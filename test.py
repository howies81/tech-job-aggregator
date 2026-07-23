import feedparser
import re
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from datetime import datetime

JOBICY_TYPE_MAP = {

    "Full Time": "FT",
    "Full-Time": "FT",
    "Part Time": "PT",
    "Part-Time": "PT",
    "Contract": "CON",
    "Freelance": "FREE",
    "Internship": "FT",
}

wwr_url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
remotive_url = "https://remotive.com/remote-jobs/feed/software-development"
himalayas_url = "https://himalayas.app/jobs/rss"
jobicy_url = "https://jobicy.com/feed/job_feed?job_categories=data-science"
remote_first_url = "https://remotefirstjobs.com/rss/jobs/python.rss"
real_work_from_anywhere_url = "https://www.realworkfromanywhere.com/remote-frontend-jobs/rss.xml"

feed = feedparser.parse(real_work_from_anywhere_url)

print(feed.entries[0].keys())
print(len(feed.entries))

#Check to see what are the keys in the RSS feed
for key, value in feed.entries[0].items():
    print(f"{key}           {value}")

job_titles_seen = set()
#job_locations_seen = set()
for entry in feed.entries:
    job_titles_seen.add(entry.get("title", "MISSING"))
    #job_locations_seen.add(entry.get("job_listing_location", ""))

print(job_titles_seen)
#print(job_locations_seen)

#-----------------------------------------------------
# WEWORKREMOTELY
#-----------------------------------------------------
title_raw = feed.entries[0].get("title", "").strip()

if not title_raw:
    #return None
    print("ERROR!")

title_full = title_raw.split("at")[0].strip()
company = feed.entries[0].get("author", "").strip()
title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                            fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
loc = None
summary = feed.entries[0].get("summary", "")

soup = BeautifulSoup(summary, "html.parser")

    # Extract headquarters from first <p> tag

""" first_p = soup.find("p")
text = first_p.get_text() """


    
# Strip all HTML for clean description
job_description = soup.get_text(separator=" ", strip=True)
job_description = GoogleTranslator(source="auto", target="english").translate(job_description[:4999])

def get_location_scope(title: str, job_description: str) -> str:
    """Infer location scope from title and description text."""
    text = (title + " " + job_description).lower()

    if any(p in text for p in [
        "usa only", "us only", "united states only",
        "must be us", "us-based", "us based",
        "lower 48", "north america only"
    ]):
        return "remote_us_only"
    
    if any(p in text for p in [
        "uk only", "united kingdom only", "united-kingdom only", "uk-based", "uk based",
        "must be uk", "must be united kingdom", "must be united-kingdom"

    ]):
        return "remote_uk_only"
    
    if any(p in text for p in[
         "eu only", "european union only", "european union only", "eu-based",
        "eu-based", "must be eu", "must be european union",
        "must be european-union" 
    ]):
        return "remote_eu_only"
    
    if any(p in text for p in [
        "latam only", "latin america only", "latam-based"
    ]):
        return "remote_latam"

    if any(p in text for p in [
        "anywhere in the world", "worldwide", "work from anywhere",
        "global", "all timezones", "any timezone"
    ]):
        return "remote_worldwide"
    
    if any(p in text for p in [
        "time zone", "timezone", "time-zone",
        "gmt+", "gmt-", "utc+", "utc-",
        "cet", "central european",
        "+/- 2 hours", "+/- 3 hours", "+/- 4 hours",
        "within 2 hours", "within 3 hours"
    ]):
        return "remote_tz_restricted"

    return "remote_worldwide"

def get_job_type(title: str, job_description: str) -> str:
    """Infer job type from title and description text."""
    text = (title + " " + job_description).lower()

    if any(p in text for p in [ "competitive based on experience",
        "competitive salary",
        "contractor",
        "independent contractor",
        "1099",]):
        return "CON"
    
    if any(p in text for p in ["freelance", "freelancer", "independent",
    "per hour", "/hr", "/hour", "hourly rate"]):
        return "FREE"
    
    if any(p in text for p in ["part-time", "part time"]):
        return "PT"
    return "FT"  # default — most remote jobs are full time

def parse_date(entry) ->(str):
    """Convert feedparser's date tuple to YYYY-MM-DD string."""
    if hasattr(entry,'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
    return datetime.now().strftime('%Y-%m-%d')

def get_jobicy_location_scope(raw_location: str) -> str:
    loc = raw_location.lower()

    if "worldwide" in loc or "anywhere" in loc:
        return "remote_worldwide"
    if "latam" in loc:
        return "remote_latam"
    if "emea" in loc:
        return "remote_emea"
    if "usa" in loc or "us" in loc.split(","):
        return "remote_us_only"
    if "uk" in loc:
        return "remote_uk_only"
    if "europe" in loc:
        return "remote_europe"
    
    return "remote_location_restricted"

def get_jobicy_job_type(raw_value: str) -> str:
    return JOBICY_TYPE_MAP.get(raw_value.strip(), "FT")

loc_scope = get_location_scope(title_extracted, job_description)
job_type = get_job_type(title_extracted, job_description)

 # Get category from tags
tags = feed.entries[0].get("tags", [])
category = tags[0].get("term", "")


#Get job link
link = feed.entries[0].get("link", "").strip()

#Job board
job_board = "real_work_from_anywhere"

#Date of job posting
date_posted = parse_date(feed.entries[0])

""" for entry in feed.entries:
    job = {
                "title":            entry.get("title", "").split(":")[1].strip(),
                "company":          entry.get("title", "").split(":")[0].strip(),
                "location":         entry.get("region", "").strip(),
                "is_remote":        1,
            }
    break """

job = {
                 "title":            title_extracted,
                "company":          company,
                "location":         loc,
                "is_remote":        1,
                "location_scope":   loc_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted
            }

print(f"\n\n{job['title']}\n {job['company']}\n {job['location']}\n\
      \n{job['job_description']}\n{job['location_scope']}\n{job['job_type']}\
      \n{job['category']}\n{job['link']}\n{job['job_board']}\n{job['date_posted']}")

#-----------------------------------------------------
# REMOTIVE
#-----------------------------------------------------
""" for entry in feed.entries:
    job = {
                "title":            entry.get("title", "").strip(),
                "company":          entry.get("company", "").strip()
            } 
    print(f"{job['title']}     {job['company']}") """