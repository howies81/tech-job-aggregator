import os
import libsql
from dotenv import load_dotenv

#DB_PATH = os.path.join(os.path.dirname(__file__), 'job_aggregator.db')

load_dotenv()
TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def getConnection():
    """Return a connection to the Turso database."""
    try:
        conn = libsql.connect(
            database = TURSO_URL,
            auth_token = TURSO_TOKEN
        )
        
        return conn
    except Exception as error:
        raise error
    
def init_db():
    """Create the database and tables from schema.sql."""
    with open(SCHEMA_PATH, 'r') as f:
        schema = f.read()

    # Remove single-line comments before splitting
    import re
    schema = re.sub(r'--[^\n]*', '', schema)
    
    # Split schema into individual SQL statements and execute each one to create tables
    statements =[s.strip() for s in schema.split(";") if s.strip()]

    #Start connection
    conn = getConnection()
    for statement in statements:
        conn.execute(statement)
    conn.close()
    print("Database Initialised")

def insert_job(job: dict) -> bool:
    """
    Insert a job into the database.
    Returns True if inserted, False if duplicate (link already exists).
    """
    try:
        sql = """
            INSERT OR IGNORE INTO jobs
                (title, company, loc, is_remote, location_scope,
                job_type, category, job_description, link, job_board,
                date_posted)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values = (
            job["title"],
            job["company"],
            job["loc"],
            job["is_remote"],
            job["location_scope"],
            job["job_type"],
            job.get("category"),
            job["job_description"],
            job["link"],
            job["job_board"],
            job["date_posted"],
            
        )

        conn = getConnection()
        
        cursor = conn.execute(sql, values)
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return False
    
def search_jobs(keywords=None, categories=None, scopes=None, limit=200) -> list:
    """
    Search jobs with optional filters.
    Returns a list of matching rows.
    """
    try:
        sql = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if keywords:
            conditions = " OR ".join(["(title LIKE ? OR company LIKE ? OR job_description LIKE ?)" ] * len(keywords))
            sql += f" AND ({conditions})"
            for kw in keywords:
                params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])

        if categories and "All" not in categories:
            placeholders = ",".join("?" * len(categories))
            sql += f" AND category IN ({placeholders})"
            params.extend(categories)

        if scopes and "All" not in scopes:
            placeholders = ",".join("?" * len(scopes))
            sql += f" AND location_scope IN ({placeholders})"
            params.extend(scopes)

        """ if sources:
            placeholders = ",".join("?" * len(sources))
            sql += f" AND job_board IN ({placeholders})"
            params.extend(sources) """

        sql += " ORDER BY date_scraped DESC LIMIT ?"
        params.append(limit)

        conn = getConnection()
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        columns =[d[0] for d in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]  
    
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return []
    

def save_job(job_id: int, status: str = None) -> bool:
    """Save a job to the saved_jobs table."""

    try:
        sql = """
            INSERT OR IGNORE INTO saved_jobs (job_id, job_status)
            VALUES (?, ?)
        """
        conn = getConnection()
        cursor = conn.execute(sql, (job_id, status))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return False
    
def get_saved_jobs() -> list:
    """Return all saved jobs joined with their full job details."""
    try:
        sql = """
            SELECT j.*, s.job_status, s.date_saved
            FROM saved_jobs AS s
            JOIN jobs AS j ON s.job_id = j.id
            ORDER BY s.date_saved DESC
        """

        conn = getConnection()
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        conn.close()
        return rows
    
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return []
    
def update_saved_job_status(job_id: int, status: str) -> bool:
    """Update the application status of a saved job."""

    try:
        sql = "UPDATE saved_jobs SET job_status = ? WHERE job_id = ?"
        conn = getConnection()
        cursor = conn.execute(sql, (status, job_id))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Unexpected DB error: {e}")
        return False
    
def delete_expired_jobs(days_to_keep: int = 60) -> int:
    """
    Delete jobs older than the specified number of days based on their post date.
    Does NOT delete jobs that have been explicitly bookmarked/saved.
    Returns the number of deleted records.
    """
    try:
        # Protect saved/bookmarked jobs by checking against the saved_jobs table
        sql = """
            DELETE FROM jobs 
            WHERE date_posted < DATE('now', ?)
              AND id NOT IN (SELECT job_id FROM saved_jobs)
        """
        # SQLite modifier expects a string format like '-60 days'
        age_modifier = f"-{days_to_keep} days"
        
        conn = getConnection()
        cursor = conn.execute(sql, (age_modifier,))
        conn.commit()
        conn.close()
        deleted_count = cursor.rowcount
            
        if deleted_count > 0:
            print(f"🧹 Data Retention: Pruned {deleted_count} expired jobs older than {days_to_keep} days.")
        return deleted_count
        
    except Exception as e:
        print(f"Unexpected DB error during data retention: {e}")
        return 0