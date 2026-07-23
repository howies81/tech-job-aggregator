# test_turso.py
from database import getConnection

conn = getConnection()
total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
print(f"Total jobs in Turso: {total}")

print("\nPer source:")
for row in conn.execute("SELECT job_board, COUNT(*) as c FROM jobs GROUP BY job_board ORDER BY c DESC").fetchall():
    print(f"  {row[0]}: {row[1]}")
conn.close()