# test_integration.py
import os
import time
from database import init_db, search_jobs, get_saved_jobs, save_job, update_saved_job_status, getConnection
from remote_jobs_rss import scrape_feed, FEEDS

def run_integration_test():
    print("=== 1. Setting Up Live Test Database ===")
    # Clean up any old database to start from scratch
    if os.path.exists('job_aggregator.db'):
        os.remove('job_aggregator.db')
        print("Removed old 'job_aggregator.db' to ensure clean environment.")
        
    # This will read schema.sql and create a fresh job_aggregator.db on disk
    init_db()
    
    # Confirm tables are successfully built on your storage drive
    with getConnection() as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print(f"Tables successfully verified on disk: {[t['name'] for t in tables]}")

    print("\n=== 2. Testing Scraper-to-Database Flow ===")
    # We will pick WeWorkRemotely's DevOps feed as a fast, reliable test target
    source = "weworkremotely"
    category = "devops"
    url = FEEDS[source][category]
    
    start_time = time.time()
    inserted_first_run, skipped_first_run = scrape_feed(source, category, url)
    elapsed = time.time() - start_time
    
    print(f"Scrape Complete in {elapsed:.2f}s -> Inserted: {inserted_first_run}, Skipped: {skipped_first_run}")

    print("\n=== 3. Testing Deduplication Logic ===")
    print("Re-running the exact same scrape to test if link UNIQUE constraints hold up...")
    inserted_second_run, skipped_second_run = scrape_feed(source, category, url)
    print(f"Second Run Result -> Inserted: {inserted_second_run}, Skipped/Duplicates: {skipped_second_run}")
    
    if inserted_second_run > 0:
        print("⚠️ Warning: Deduplication failed! Duplicates were allowed into the database.")
    else:
        print("✅ Success: Deduplication works perfectly. Zero duplicate entries inserted.")

    print("\n=== 4. Testing Querying and Pipeline Operations ===")
    # Pull jobs out of the database using your search functionality
    all_jobs = search_jobs(limit=5)
    print(f"Jobs successfully fetched from disk database: {len(all_jobs)}")
    
    if all_jobs:
        first_job = all_jobs[0]
        print(f"Sample Job Entry Found: '{first_job['title']}' at {first_job['company']} via {first_job['job_board']}")
        job_id = first_job['id']
        
        # Test the relationship between 'jobs' and 'saved_jobs' tables
        print("\n--- Bookmarking / Saved Status Test ---")
        saved = save_job(job_id, status='saved')
        print(f"Job ID {job_id} saved: {saved}")
        
        saved_list = get_saved_jobs()
        if saved_list:
            print(f"Confirmed saved job in DB: '{saved_list[0]['title']}' | Status: {saved_list[0]['job_status']}")
            
            # Test updating the interview status pipeline
            updated = update_saved_job_status(job_id, status='interviewing')
            print(f"Job ID {job_id} pipeline updated to 'interviewing': {updated}")
            
            # Re-fetch to guarantee it saved correctly
            updated_saved_list = get_saved_jobs()
            print(f"Final Pipeline Verification Status: {updated_saved_list[0]['job_status']}")
    else:
        print("❌ Error: No jobs were found in the database. Check feed parser or network constraints.")

if __name__ == "__main__":
    run_integration_test()