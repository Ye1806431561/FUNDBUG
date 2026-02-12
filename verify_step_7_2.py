import asyncio
import sqlite3
from datetime import datetime, timedelta
from src.db.crud import cleanup_old_estimates
from src.db.models import init_db, get_connection

def verify_cleanup():
    print("--- Verifying Step 7.2: Data Cleanup Verification ---")
    
    # Ensure DB exists
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Insert dummy records
    # Fund must exist to satisfy foreign key
    cursor.execute("INSERT OR IGNORE INTO funds (fund_code, fund_name) VALUES (?, ?)", ('999999', 'Test Fund'))
    
    now = datetime.now()
    old_date = now - timedelta(days=8, hours=1) # 8+ days ago
    recent_date = now - timedelta(days=1)       # 1 day ago
    
    # Insert old record
    cursor.execute("""
        INSERT INTO nav_estimates (fund_code, estimate_time, estimated_nav, estimated_return)
        VALUES (?, ?, ?, ?)
    """, ('999999', old_date, 1.0, 0.0))
    
    # Insert recent record
    cursor.execute("""
        INSERT INTO nav_estimates (fund_code, estimate_time, estimated_nav, estimated_return)
        VALUES (?, ?, ?, ?)
    """, ('999999', recent_date, 1.0, 0.0))
    
    conn.commit()
    
    # Verify insertion
    cursor.execute("SELECT COUNT(*) FROM nav_estimates WHERE fund_code = '999999'")
    count = cursor.fetchone()[0]
    print(f"Inserted {count} test records.")
    
    # 2. Trigger cleanup
    print("Triggering cleanup_old_estimates(days=7)...")
    cleanup_old_estimates(days=7)
    
    # 3. Verify results
    cursor.execute("SELECT estimate_time FROM nav_estimates WHERE fund_code = '999999'")
    rows = cursor.fetchall()
    
    remaining_dates = [datetime.fromisoformat(row['estimate_time']) for row in rows] # sqlite3.Row access
    
    # Check if old record is gone
    old_record_exists = any(d.date() == old_date.date() for d in remaining_dates)
    # Check if recent record is present
    recent_record_exists = any(d.date() == recent_date.date() for d in remaining_dates)
    
    if not old_record_exists:
        print("✅ Old record (8 days ago) successfully removed.")
    else:
        print("❌ Old record FAILED to remove.")
        
    if recent_record_exists:
        print("✅ Recent record (1 day ago) preserved.")
    else:
        print("❌ Recent record was ACCIDENTALLY removed.")
        
    # Validation logic
    if not old_record_exists and recent_record_exists:
        print("✅ Step 7.2 Verification PASSED!")
    else:
        print("❌ Step 7.2 Verification FAILED!")
        exit(1)
        
    # Cleanup test data
    cursor.execute("DELETE FROM nav_estimates WHERE fund_code = '999999'")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    verify_cleanup()
