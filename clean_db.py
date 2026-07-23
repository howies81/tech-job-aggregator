from database import getConnection

def ultimate_clean():
    try:
        conn = getConnection()
        
        
        print("🧼 Normalizing fragmented categories...")
        cursor = conn.execute("SELECT id, title, category FROM jobs WHERE category IS NOT NULL")
        columns = [d[0] for d in cursor.description]
        rows = [dict(zip(columns, r)) for r in cursor.fetchall()]
        updated_count = 0
        
        for row in rows:
          

            raw_cat = row['category']
            job_title = row['title']

            search_text = f"{raw_cat} {job_title}"
            # Convert to lowercase and normalize dividers
            search_text = search_text.lower().replace("-", " ").replace("_", " ")
            
            # 1. Clean up HTML entities explicitly
            if "amp" in search_text:
                search_text = search_text.replace("&amp;", " and ").replace("&amp", " and ").replace("amp", " and ")
            
            # If the category string contains any of these hiring/agency words, 
            # bypass technical categorization and send it straight to 'other'.
            if any(non_tech_word in search_text for non_tech_word in [
                "recruiter", "recruitment", "talent acquisition", "hr ", "human resources", 
                "sourcing specialist", "headhunter", "people ops", "people operations"
            ]):
                clean_cat = "other"

            # 2. Heavy-duty mapping rules based on your exact list
            elif "back end" in search_text or "backend" in search_text:
                clean_cat = "backend"
            elif "front end" in search_text or "frontend" in search_text or "react" in search_text:
                clean_cat = "frontend"
            elif "full stack" in search_text or "fullstack" in search_text:
                clean_cat = "fullstack"
            elif "devops" in search_text or "sysadmin" in search_text or "infrastructure" in search_text or "microsoft 365" in search_text:
                clean_cat = "devops"
            elif "data" in search_text or "analytics" in search_text or "science" in search_text:
                clean_cat = "data_and_analytics"
            elif "software" in search_text or "developer" in search_text or "engineering" in search_text or "python" in search_text or "technical lead" in search_text or "staff" in search_text:
                clean_cat = "software_development"
            elif "design" in search_text or "ux" in search_text or "ui" in search_text or "graphics" in search_text:
                clean_cat = "design"
            elif "artificial intelligence" in search_text or "applied ai" in search_text or " ai " in search_text:
                clean_cat = "artificial_intelligence"
            elif "product" in search_text or "scrum" in search_text or "program" in search_text or "pmo" in search_text:
                clean_cat = "product_management"
            elif "marketing" in search_text or "sales" in search_text or "seo" in search_text:
                clean_cat = "sales_and_marketing"
            elif "customer support" in search_text or "customer service" in search_text or "technical support" in search_text or "account support" in search_text:
                clean_cat = "customer_support"
            else:
                # Group all miscellaneous non-tech jobs into an elegant bucket
                clean_cat = "other"
                
            # Update database if a change happened
            if clean_cat != raw_cat:
                conn.execute("UPDATE jobs SET category = ? WHERE id = ?", (clean_cat, row['id']))
                updated_count += 1
                
        conn.commit()
        print(f"✅ Master normalization complete! Unified {updated_count} fragmented items.")
        conn.close()

    except Exception as e:
        print(f"❌ Error during master clean: {e}")

if __name__ == "__main__":
    ultimate_clean()