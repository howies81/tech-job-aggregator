import feedparser
import os
from datetime import datetime
from database import insert_job
from langdetect import detect
from deep_translator import GoogleTranslator
from bs4 import BeautifulSoup
import re

##-------------------------
# RSS fEEDS
##-------------------------

FEEDS ={
    "weworkremotely": {
    "software":   "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "frontend":   "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "backend":    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "fullstack":  "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "devops":     "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "design":     "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "marketing":  "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
    "other":      "https://weworkremotely.com/categories/all-other-remote-jobs.rss",
},

    "remotive": {
       "software_development":   "https://remotive.com/remote-jobs/feed/software-development",
       "design":                 "https://remotive.com/remote-jobs/feed/design",
       "product_management":     "https://remotive.com/remote-jobs/feed/product",
       "artificial_intelligence":"https://remotive.com/remote-jobs/feed/artificial-intelligence",
       "data_and_analytics":     "https://remotive.com/remote-jobs/feed/data",
       "devops":                 "https://remotive.com/remote-jobs/feed/devops",
       "engineering":            "https://remotive.com/remote-jobs/feed/engineering",
       "information_technology": "https://remotive.com/remote-jobs/feed/information-technology",
       "other":                  "https://remotive.com/remote-jobs/feed/all-others",
},

    "himalayas": {
        "general":                "https://himalayas.app/jobs/rss",
    },

    "jobicy": {
        "data_science_and_analytics": "https://jobicy.com/feed/job_feed?job_categories=data-science",
        "web_and_app_design":         "https://jobicy.com/feed/job_feed?job_categories=web-app-design",
        "devops_and_infrastructure":  "https://jobicy.com/feed/job_feed?job_categories=admin",
        "software_engineering":       "https://jobicy.com/feed/job_feed?job_categories=engineering",
    },
    
    "remote_first_jobs": {
        "python":                     "https://remotefirstjobs.com/rss/jobs/python.rss",
        "data_science":               "https://remotefirstjobs.com/rss/jobs/data-science.rss",
        "data":                       "https://remotefirstjobs.com/rss/jobs/data.rss",
        "software_development":       "https://remotefirstjobs.com/rss/jobs/software-development.rss",

    },

    "real_work_from_anywhere": {
        "fullstack":                  "https://www.realworkfromanywhere.com/remote-fullstack-jobs/rss.xml",
        "frontend":                   "https://www.realworkfromanywhere.com/remote-frontend-jobs/rss.xml",
        "backend":                    "https://www.realworkfromanywhere.com/remote-backend-jobs/rss.xml",
        "software_development":       "https://www.realworkfromanywhere.com/remote-software-developer-jobs/rss.xml",
        "design":                     "https://www.realworkfromanywhere.com/remote-design-jobs/rss.xml",
        "devops":                     "https://www.realworkfromanywhere.com/remote-devops-and-sysadmin-jobs/rss.xml"
    },


}

#For Jobicy RSS feeds, this is the mapping table for mapping the job type
# from the RSS feed to the right database entry

JOBICY_TYPE_MAP = {

    "Full Time": "FT",
    "Full-Time": "FT",
    "Part Time": "PT",
    "Part-Time": "PT",
    "Contract": "CON",
    "Freelance": "FREE",
    "Internship": "FT",
}

#All of the RSS feeds have a published_parsed category, which provides the date
# the job was posted on the job board. This function changes the format of the date
# to YYYY-MM-DD

def parse_date(entry) ->(str):
    """Convert feedparser's date tuple to YYYY-MM-DD string."""
    if hasattr(entry,'published_parsed') and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6]).strftime('%Y-%m-%d')
        except (TypeError, ValueError):
            pass
    return datetime.now().strftime('%Y-%m-%d')

def parse_wwr_summary(summary: str) -> tuple[str, str]:
    """
    Extract (location, clean job description) from WWR summary HTML.
    Returns (loc, job_description)
    """

    soup = BeautifulSoup(summary, "html.parser")

     # Extract headquarters from first <p> tag
    loc = None
    first_p = soup.find("p")
    if first_p:
        text = first_p.get_text()
        if "Headquarters:" in text:
            loc = text.replace("Headquarters:", "").split("URL:")[0].strip()
        
    # Strip all HTML for clean description
    job_description = soup.get_text(separator=" ", strip=True)

    return loc, job_description

def to_english(text: str) -> str:
    """Detect language and translate to English if necessary."""
    if not text or len(text) < 20:
        return text
    try:
        if detect(text) == 'en':
            return text
        return GoogleTranslator(source="auto", target="english").translate(text)
    except:
        return text

def get_location_scope(title: str, job_description: str) -> str:
    """Infer location scope from title and description text."""
    text = (title + " " + job_description).lower()

    # 1. Check for hard restrictions FIRST (Most specific rules)
    if any(p in text for p in [
        "usa only", "us only", "united states only", "us-only",
        "must be us", "us-based", "us based", "lower 48", 
        "north america only", "us residents", "citizenship required",
        "eligible to work in the us", "must be physically located in the us"
    ]):
        return "remote_us_only"
    
    if any(p in text for p in [
        "uk only", "united kingdom only", "united-kingdom only", "uk-based", "uk based",
        "must be uk", "must be united kingdom", "must be united-kingdom"
    ]):
        return "remote_uk_only"
    
    if any(p in text for p in [
        "eu only", "european union only", "eu-based",
        "must be eu", "must be european union", "must be european-union" 
    ]):
        return "remote_eu_only"
    
    # 2. Check for intermediate constraints
    if any(p in text for p in [
        "latam only", "latin america only", "latam-based", "caribbean only"
    ]):
        return "remote_latam"

    if any(p in text for p in [
        "time zone", "timezone", "time-zone",
        "gmt+", "gmt-", "utc+", "utc-", " est ", " pst ",
        " cet ", "central european",
        "+/- 2 hours", "+/- 3 hours", "+/- 4 hours",
        "within 2 hours", "within 3 hours"
    ]):
        return "remote_tz_restricted"

    # 3. Check for broad catch-alls LAST
    if any(p in text for p in [
        "anywhere in the world", "worldwide", "work from anywhere",
        "global", "all timezones", "any timezone"
    ]):
        return "remote_worldwide"

    # Default fallback if nothing else is specified
    return "remote_location_restricted"

def get_job_type(title: str, job_description: str) -> str:
    """Infer job type from title and description text."""
    text = (title + " " + job_description).lower()

    if any(p in text for p in [ "competitive based on experience",
        "competitive salary",
        "contractor",
        "independent contractor",
        "1099",]):
        return "CON"
    
    if any(p in text for p in ["freelance", "freelancer", "independent", "/hr", "per hour"]):
        return "FREE"
    if any(p in text for p in ["part-time", "part time"]):
        return "PT"
    return "FT"  # default — most remote jobs are full time



def clean_wwr_entry(entry, source) -> dict | None:
    title_raw = entry.get("title", "").strip()

    if not title_raw:
        return None

    title_full = title_raw.split(":", 1)[1].strip()
    company = title_raw.split(":", 1)[0].strip()
    title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                             fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
    
    # Parse summary HTML
    summary = entry.get("summary", "")
    loc, job_description = parse_wwr_summary(summary)

    # Translate if not English
    title = to_english(title_extracted)
    job_description = to_english(job_description)
    
    # Infer fields
    location_scope = get_location_scope(title_raw, job_description)
    job_type = get_job_type(title_raw, job_description)

     # Get category from tags
    tags = entry.get("tags", [])
    category = tags[0]["term"].lower().replace(" ", "_") if tags else "other"

    #Get job link
    link = entry.get("link", "").strip()

    #Job board
    job_board = source

    #Date of job posting
    date_posted = parse_date(entry)

    if not title or not link:
        return None

    job = {
                 "title":           title,
                "company":          company,
                "loc":              loc,
                "is_remote":        1,
                "location_scope":   location_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted

            }
    
    return job
    
def clean_remotive_entry(entry, source) -> dict:
    title_raw = entry.get("title", "").strip()

    if not title_raw:
        return None

    title_full = title_raw
    company = entry.get("company", "").strip()
    title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                                fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
    location = entry.get("region", "").strip()
    summary = entry.get("summary", "")

    soup = BeautifulSoup(summary, "html.parser")

   # Translate if not English
    title = to_english(title_extracted)
    job_description = soup.get_text(separator=" ", strip=True)
    job_description = to_english(job_description)
    #job_description = GoogleTranslator(source="auto", target="english").translate(job_description[:4999])


    location_scope = get_location_scope(title_raw, job_description)
    job_type = get_job_type(title_raw, job_description)

    # Get category from tags
    tags = entry.get("tags", [])
    category = tags[0]["term"].lower().replace(" ", "_") if tags else "other"

    #Get job link
    link = entry.get("link", "").strip()

    #Job board
    job_board = source

    #Date of job posting
    date_posted = parse_date(entry)

    if not title or not link:
        return None

    job = {
                 "title":           title,
                "company":          company,
                "loc":              location,
                "is_remote":        1,
                "location_scope":   location_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted

            }
    
    return job

def clean_himalayas_entry(entry, source) -> dict:
    title_raw = entry.get("title", "").strip()

    if not title_raw:
        return None
        

    title_full = title_raw
    company = entry.get("himalayasjobs_companyname", "").strip()
    title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                                fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
    title_extracted = to_english(title_extracted)
    loc = entry.get("himalayasjobs_locationrestriction", "").strip()
    summary = entry.get("content", "")

    if summary and isinstance(summary, list):
        html_markup = summary[0].get("value", "")
    else:
        html_markup = entry.get("summary", "")


    soup = BeautifulSoup(html_markup, "html.parser")

    job_description = soup.get_text(separator=" ", strip=True)
    job_description = to_english(job_description)
    #job_description = GoogleTranslator(source="auto", target="english").translate(job_description[:4999])

    loc_scope = get_location_scope(title_raw, job_description)
    job_type = get_job_type(title_raw, job_description)

    # Get category from tags
    tags = entry.get("tags", [])
    category = tags[0]["term"].lower().replace(" ", "_") if tags else "other"

    #Get job link
    link = entry.get("link", "").strip()

    #Job board
    job_board = source

    #Date of job posting
    date_posted = parse_date(entry)

    if not title_extracted or not link:
        return None

    job = {
                 "title":            title_extracted,
                "company":          company,
                "loc":              loc,
                "is_remote":        1,
                "location_scope":   loc_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted
            }
    
    return job

def get_jobicy_job_type(raw_value: str) -> str:
    return JOBICY_TYPE_MAP.get(raw_value.strip(), "FT")

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
    

def clean_jobicy_entry(entry, source):
    title_raw = entry.get("title", "").strip()

    if not title_raw:
        return None
        

    title_full = title_raw
    company = entry.get("job_listing_company", "").strip()
    title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                                fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
    title_extracted = to_english(title_extracted)
    loc = entry.get("job_listing_location", "").strip()
    summary = entry.get("content", "")

    if summary and isinstance(summary, list):
        html_markup = summary[0].get("value", "")
    else:
        html_markup = entry.get("summary", "")


    soup = BeautifulSoup(html_markup, "html.parser")

    # Strip all HTML for clean description
    job_description = soup.get_text(separator=" ", strip=True)
    job_description = to_english(job_description)
    #job_description = GoogleTranslator(source="auto", target="english").translate(job_description[:4999])

    loc_scope = get_jobicy_location_scope(loc)
    job_listing = entry.get("job_listing_job_type", "").strip()
    job_type = get_jobicy_job_type(job_listing)

    # Get category from tags
    tags = entry.get("summary_detail", {})
    parts = tags.get("base", "").split("=", 1)
    category = parts[1].strip() if len(parts) > 1 else "other"

    #Get job link
    link = entry.get("link", "").strip()

    #Job board
    job_board = source

    #Date of job posting
    date_posted = parse_date(entry)

    if not title_extracted or not link:
        return None

    job = {
                 "title":            title_extracted,
                "company":          company,
                "loc":              loc,
                "is_remote":        1,
                "location_scope":   loc_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted
            }
    
    return job

def clean_remote_first_jobs_entry(entry, source):
    title_raw = entry.get("title", "").strip()

    if not title_raw:
        return None
        

    if " at " in title_raw:
        title_full, company = title_raw.split(" at ", 1)
        title_full, company = title_full.strip(), company.strip()
    else:
        title_full, company = title_raw, None

    
    title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                                fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
    title_extracted = to_english(title_extracted)
    loc = None
    summary = entry.get("summary", "")

    soup = BeautifulSoup(summary, "html.parser")


    job_description = soup.get_text(separator=" ", strip=True)
    job_description = to_english(job_description)
    #job_description = GoogleTranslator(source="auto", target="english").translate(job_description[:4999])

    loc_scope = get_location_scope(title_extracted, job_description)
    job_type = get_job_type(title_extracted, job_description)

    # Get category from tags
    tags = entry.get("summary_detail", {})
    if tags and isinstance(tags, dict):
        category_1 = tags['base'].split("/jobs/",1)[1].strip()
        category = category_1.split(".",1)[0].strip()
    else:
        category = "other"

    #Get job link
    link = entry.get("link", "").strip()

    #Job board
    job_board = source

    #Date of job posting
    date_posted = parse_date(entry)

    if not title_extracted or not link:
        return None

    job = {
                 "title":            title_extracted,
                "company":          company,
                "loc":         loc,
                "is_remote":        1,
                "location_scope":   loc_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted
            }
    
    return job

def clean_real_work_from_anywhere_entry(entry, source):
    title_raw = entry.get("title", "").strip()

    if not title_raw:
        return None
        

    title_full = title_raw.split(" at ")[0].strip()
    company = entry.get("author", "").strip()
    title_extracted = re.sub(r'\s*[-–]\s*(usa only|us only|uk only|europe only|100% remote|\
                                fully remote).*$','', title_full, flags=re.IGNORECASE).strip()
    title_extracted = to_english(title_extracted)
    loc = None
    summary = entry.get("summary", "")

    soup = BeautifulSoup(summary, "html.parser")

    job_description = soup.get_text(separator=" ", strip=True)
    job_description = to_english(job_description)
    #job_description = GoogleTranslator(source="auto", target="english").translate(job_description[:4999])

    loc_scope = get_location_scope(title_extracted, job_description)
    job_type = get_job_type(title_extracted, job_description)

    # Get category from tags
    tags = entry.get("tags", [])
    category = tags[0].get("term", "")


    #Get job link
    link = entry.get("link", "").strip()

    #Job board
    job_board = source

    #Date of job posting
    date_posted = parse_date(entry)

    if not title_extracted or not link:
        return None

    job = {
                 "title":            title_extracted,
                "company":          company,
                "loc":         loc,
                "is_remote":        1,
                "location_scope":   loc_scope,
                "job_type":         job_type,
                "category":         category,
                "job_description":  job_description,
                "link":             link,
                "job_board":        job_board,
                "date_posted":      date_posted
            }
    
    return job
    

def scrape_feed(source: str, category: str, url: str) -> tuple[int, int]:
    """
    Scrape a single RSS feed. 
    Returns (inserted, skipped) counts.
    """
    
    inserted = 0
    skipped = 0

    print(f"  Scraping [{source}] [{category}]...")
    feed = feedparser.parse(url)

    for entry in feed.entries:
        if source == "weworkremotely":
            job = clean_wwr_entry(entry, source)

        elif source == "remotive":
            job = clean_remotive_entry(entry, source)

        elif source == "himalayas":
            job = clean_himalayas_entry(entry, source)

        elif source == "jobicy":
            job = clean_jobicy_entry(entry, source)

        elif source == "remote_first_jobs":
            job = clean_remote_first_jobs_entry(entry, source)

        elif source == "real_work_from_anywhere":
            job = clean_real_work_from_anywhere_entry(entry, source)

        else:
            skipped += 1
            continue

        was_inserted = insert_job(job)
        if was_inserted:
            inserted += 1
        else:
            skipped += 1

    return inserted, skipped