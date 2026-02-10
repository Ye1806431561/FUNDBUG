import pytest
from datetime import datetime, timedelta
from src.db import crud

def test_fund_operations():
    # Insert fund
    assert crud.insert_fund("001", "Test Fund 1", "Stock", 1.23, "2023-01-01") is True
    
    # Get fund
    fund = crud.get_fund("001")
    assert fund is not None
    assert fund['fund_name'] == "Test Fund 1"
    assert fund['latest_nav'] == 1.23
    
    # Update fund
    assert crud.update_fund_nav("001", 1.25, "2023-01-02") is True
    fund = crud.get_fund("001")
    assert fund['latest_nav'] == 1.25
    assert fund['nav_date'] == "2023-01-02"
    
    # Get all funds
    crud.insert_fund("002", "Test Fund 2", "Mix", 1.0, "2023-01-01")
    all_funds = crud.get_all_funds()
    assert len(all_funds) == 2

def test_holdings_operations():
    crud.insert_fund("001", "Test Fund")
    
    holdings = [
        {"stock_code": "S1", "stock_name": "Stock A", "weight": 10.5, "report_date": "2023-12-31"},
        {"stock_code": "S2", "stock_name": "Stock B", "weight": 20.0, "report_date": "2023-12-31"}
    ]
    
    # Insert holdings
    assert crud.insert_holdings("001", holdings) is True
    
    # Get holdings
    saved = crud.get_holdings_by_fund("001", "2023-12-31")
    assert len(saved) == 2
    assert saved[0]['fund_code'] == "001"
    
    # specific order check (weight desc)
    assert saved[0]['stock_code'] == "S2" # 20.0
    assert saved[1]['stock_code'] == "S1" # 10.5
    
    # Get latest holdings
    latest = crud.get_latest_holdings("001")
    assert len(latest) == 2

def test_nav_history_operations():
    crud.insert_fund("001", "Test Fund")
    
    # Insert NAVs
    crud.insert_nav("001", "2023-01-01", 1.0, 1.0, 0.0)
    crud.insert_nav("001", "2023-01-02", 1.01, 1.01, 1.0)
    
    # Get history
    history = crud.get_nav_history("001")
    assert len(history) == 2
    assert history[0]['nav_date'] == "2023-01-02" # Date Descending
    
    # Get latest
    latest = crud.get_latest_nav("001")
    assert latest['nav'] == 1.01

def test_nav_estimates_cleanup():
    crud.insert_fund("001", "Test Fund")
    
    # Insert old estimates (8 days ago)
    old_time = datetime.now() - timedelta(days=8)
    
    # Since insert_estimate uses CURRENT_TIMESTAMP, we need to manually insert old records
    # or patch datetime. But easier to use direct SQL for setup in test or modify insert temporarily.
    # We can't easily modify SQL. 
    # Let's direct insert using connection from crud (which uses our mock)
    # Wait, we can't access connection easily unless we expose it.
    
    # Alternative: Use crud.insert_estimate and then manually update the timestamp in DB
    crud.insert_estimate("001", 1.0)
    
    # Manually update time to be old
    from src.db.models import get_connection
    # We need the path from fixture, but we don't have it here directly without requesting it.
    # Use crud.get_connection() which is patched
    conn = crud.get_connection() 
    cursor = conn.cursor()
    cursor.execute("UPDATE nav_estimates SET estimate_time = datetime('now', '-8 days')")
    conn.commit()
    conn.close()
    
    # Insert a fresh one
    crud.insert_estimate("001", 1.1)
    
    # Cleanup
    deleted = crud.cleanup_old_estimates(days=7)
    assert deleted >= 1
    
    # Check remaining
    estimates = crud.get_estimate_errors("001") # this filters by actual_nav IS NOT NULL, so won't show
    # But we can query
    conn = crud.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as c FROM nav_estimates")
    count = cursor.fetchone()['c']
    conn.close()
    assert count == 1 # Only the fresh one remains

def test_watchlist_operations():
    # Add
    assert crud.add_to_watchlist("001", "Fund 1") is True
    assert crud.is_in_watchlist("001") is True
    
    # Duplicate add (should not fail, just do nothing)
    assert crud.add_to_watchlist("001", "Fund 1") is True
    
    # Get
    wl = crud.get_watchlist()
    assert len(wl) == 1
    assert wl[0]['fund_code'] == "001"
    
    # Remove
    assert crud.remove_from_watchlist("001") is True
    assert crud.is_in_watchlist("001") is False
    assert len(crud.get_watchlist()) == 0
