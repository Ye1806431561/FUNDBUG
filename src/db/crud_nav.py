import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from src.db.models import get_connection

logger = logging.getLogger(__name__)

# --- NAV History Operations ---

def insert_nav(fund_code: str, nav_date: str, nav: float, acc_nav: float = None, daily_return: float = None) -> bool:
    """Insert or update historical NAV record."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nav_history (fund_code, nav_date, nav, acc_nav, daily_return)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fund_code, nav_date) DO UPDATE SET
                nav = excluded.nav,
                acc_nav = COALESCE(excluded.acc_nav, nav_history.acc_nav),
                daily_return = COALESCE(excluded.daily_return, nav_history.daily_return)
        """, (fund_code, nav_date, nav, acc_nav, daily_return))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error inserting NAV history for {fund_code} on {nav_date}: {e}")
        return False
    finally:
        conn.close()

def get_nav_history(fund_code: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Get history NAVs ordered by date descending."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM nav_history 
            WHERE fund_code = ? 
            ORDER BY nav_date DESC 
            LIMIT ?
        """, (fund_code, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error getting NAV history for {fund_code}: {e}")
        return []
    finally:
        conn.close()

def get_latest_nav(fund_code: str) -> Optional[Dict[str, Any]]:
    """Get the most recent NAV record."""
    history = get_nav_history(fund_code, limit=1)
    return history[0] if history else None

# --- NAV Estimates Operations ---

def insert_estimate(fund_code: str, estimated_nav: float, estimated_return: float = None) -> bool:
    """Insert a new realtime estimate."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO nav_estimates (fund_code, estimate_time, estimated_nav, estimated_return)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?)
        """, (fund_code, estimated_nav, estimated_return))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error inserting estimate for {fund_code}: {e}")
        return False
    finally:
        conn.close()

def update_actual_nav(fund_code: str, nav_date: str, actual_nav: float) -> bool:
    """
    Update estimates with actual NAV and calculate error.
    Matches estimates that happened on the same day as nav_date.
    Assumption: estimate_time is stored in UTC/Local depending on config, but likely needs date matching.
    SQLite `date(estimate_time)` extracts the date part.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Update records where date(estimate_time) matches nav_date
        # Calculate error_rate = (estimated - actual) / actual * 100
        cursor.execute("""
            UPDATE nav_estimates 
            SET actual_nav = ?, 
                error_rate = (estimated_nav - ?) / ? * 100
            WHERE fund_code = ? AND date(estimate_time) = ?
        """, (actual_nav, actual_nav, actual_nav, fund_code, nav_date))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error updating actual NAV for {fund_code}: {e}")
        return False
    finally:
        conn.close()

def get_estimate_errors(fund_code: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent estimates that have error rates calculated (i.e. have actual_nav)."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM nav_estimates 
            WHERE fund_code = ? AND actual_nav IS NOT NULL
            ORDER BY estimate_time DESC
            LIMIT ?
        """, (fund_code, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error getting estimate errors for {fund_code}: {e}")
        return []
    finally:
        conn.close()

def cleanup_old_estimates(days: int = 7) -> int:
    """Delete estimates older than `days`."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("DELETE FROM nav_estimates WHERE estimate_time < ?", (cutoff_date,))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
    except sqlite3.Error as e:
        logger.error(f"Error cleaning up old estimates: {e}")
        return 0
    finally:
        conn.close()
