# main.py
import os
import time
from clean_db import ultimate_clean
from database import init_db, getConnection, delete_expired_jobs
from remote_jobs_rss import scrape_feed, FEEDS

def run_global_sync():
    print("=========================================")
    print("🚀 TECH JOB AGGREGATOR - HARVESTER ENGINE")
    print("=========================================\n")
    
    # 1. Automatically ensure the operational database is initialized
    try:
        conn = getConnection()
        #Check if tables exist, if not create them
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        table_names = [t[0] for t in tables]
        if 'jobs' not in table_names:
            print("📁 Jobs database table not found. Running initialization...")
            conn.close()
            init_db()
        else:
            conn.close()
            print("✅ Database connection verified.")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
        

    total_inserted = 0
    total_skipped = 0
    start_time = time.time()
    
    print(f"\n🔄 Beginning global sync across {len(FEEDS)} job platforms...")
    
    # 2. Iterate through platforms (weworkremotely, remotive, etc.)
    for source, categories in FEEDS.items():
        print(f"\n📦 Platform: {source.upper()}")
        print("-" * 30)
        
        # Iterate through specific categories under each platform
        for category, feed_url in categories.items():
            try:
                inserted, skipped = scrape_feed(source, category, feed_url)
                total_inserted += inserted
                total_skipped += skipped
                # Optional: slight delay between feeds to be polite to RSS servers
                time.sleep(0.5) 
            except Exception as e:
                print(f"  ❌ Error scraping [{source}] [{category}]: {e}")

    print("\n🧼 Running database maintenance rules...")
    # Change 30 to 60 or 90 depending on how long you want to browse expired listings
    delete_expired_jobs(days_to_keep=60)

    # 3. Compile and print execution statistics
    elapsed_time = time.time() - start_time
    print("\n=========================================")
    print("📊 GLOBAL SYNC COMPLETED PROFILE")
    print("=========================================")
    print(f"⏱️ Total Execution Time: {elapsed_time:.2f} seconds")
    print(f"✨ New Jobs Inserted:    {total_inserted}")
    print(f"♻️ Duplicates Skipped:  {total_skipped}")
    print(f"📚 Total Items Checked:  {total_inserted + total_skipped}")
    print("=========================================\n")

    ultimate_clean()
if __name__ == "__main__":
    run_global_sync()