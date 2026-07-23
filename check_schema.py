# check_schema.py
import sqlite3

DB_PATH = "job_aggregator.db"

def inspect_columns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Query SQLite system catalog for the 'jobs' table structure
        cursor.execute("PRAGMA table_info(jobs);")
        columns = cursor.fetchall()
        
        print("\n📋 CURRENT DATABASE COLUMNS:")
        print("-" * 30)
        for col in columns:
            # col[1] is the column name, col[2] is the data type
            print(f"🔹 {col[1]} ({col[2]})")
        print("-" * 30)
        
        conn.close()
    except Exception as e:
        print(f"❌ Error reading schema: {e}")

if __name__ == "__main__":
    inspect_columns()