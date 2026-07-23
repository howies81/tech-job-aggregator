from database import getConnection

with getConnection() as conn:
    print("--- Scope Breakdown ---")
    for r in conn.execute("SELECT location_scope, COUNT(*) as count FROM jobs GROUP BY location_scope").fetchall():
        print(f"{r['location_scope']}: {r['count']}")
        
    print("\n--- Platform Breakdown ---")
    for r in conn.execute("SELECT job_board, COUNT(*) as count FROM jobs GROUP BY job_board").fetchall():
        print(f"{r['job_board']}: {r['count']}")