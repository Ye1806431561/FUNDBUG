import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from src.db.models import get_connection

# Configure logging
logger = logging.getLogger(__name__)

def insert_fund(fund_code: str, fund_name: str, fund_type: str = None, latest_nav: float = None, nav_date: str = None) -> bool:
    """Insert or update fund basic information."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO funds (fund_code, fund_name, fund_type, latest_nav, nav_date, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fund_code) DO UPDATE SET
                fund_name = excluded.fund_name,
                fund_type = COALESCE(excluded.fund_type, funds.fund_type),
                latest_nav = COALESCE(excluded.latest_nav, funds.latest_nav),
                nav_date = COALESCE(excluded.nav_date, funds.nav_date),
                updated_at = CURRENT_TIMESTAMP
        """, (fund_code, fund_name, fund_type, latest_nav, nav_date))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error inserting fund {fund_code}: {e}")
        return False
    finally:
        conn.close()

def get_fund(fund_code: str) -> Optional[Dict[str, Any]]:
    """Get fund details by fund code."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM funds WHERE fund_code = ?", (fund_code,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Error getting fund {fund_code}: {e}")
        return None
    finally:
        conn.close()

def get_all_funds() -> List[Dict[str, Any]]:
    """Get all funds."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM funds")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error getting all funds: {e}")
        return []
    finally:
        conn.close()

def update_fund_nav(fund_code: str, latest_nav: float, nav_date: str) -> bool:
    """Update fund NAV."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE funds 
            SET latest_nav = ?, nav_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE fund_code = ?
        """, (latest_nav, nav_date, fund_code))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error updating fund NAV for {fund_code}: {e}")
        return False
    finally:
        conn.close()

# --- Holdings Operations ---

def insert_holdings(fund_code: str, holdings_data: List[Dict[str, Any]]) -> bool:
    """
    Insert batch of holdings.
    holdings_data expected keys: stock_code, stock_name, weight, report_date
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Prepare data for executemany
        data_to_insert = [
            (fund_code, h['stock_code'], h.get('stock_name'), h['weight'], h['report_date'])
            for h in holdings_data
        ]
        
        cursor.executemany("""
            INSERT INTO holdings (fund_code, stock_code, stock_name, weight, report_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(fund_code, stock_code, report_date) DO UPDATE SET
                weight = excluded.weight,
                stock_name = COALESCE(excluded.stock_name, holdings.stock_name)
        """, data_to_insert)
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error inserting holdings for {fund_code}: {e}")
        return False
    finally:
        conn.close()

def get_holdings_by_fund(fund_code: str, report_date: str = None) -> List[Dict[str, Any]]:
    """Get holdings for a fund, optionally filtered by report date."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if report_date:
            cursor.execute("""
                SELECT * FROM holdings 
                WHERE fund_code = ? AND report_date = ?
                ORDER BY weight DESC
            """, (fund_code, report_date))
        else:
            # If no date specified, just return all
             cursor.execute("""
                SELECT * FROM holdings 
                WHERE fund_code = ? 
                ORDER BY report_date DESC, weight DESC
            """, (fund_code,))
            
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error getting holdings for {fund_code}: {e}")
        return []
    finally:
        conn.close()

def get_latest_holdings(fund_code: str) -> List[Dict[str, Any]]:
    """Get the most recent holdings for a fund."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # First find the latest report date for this fund
        cursor.execute("SELECT MAX(report_date) as max_date FROM holdings WHERE fund_code = ?", (fund_code,))
        result = cursor.fetchone()
        if not result or not result['max_date']:
            return []
            
        latest_date = result['max_date']
        return get_holdings_by_fund(fund_code, latest_date)
    except sqlite3.Error as e:
        logger.error(f"Error getting latest holdings for {fund_code}: {e}")
        return []
    finally:
        conn.close()

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

# --- Watchlist Operations ---

def add_to_watchlist(fund_code: str, fund_name: str = None) -> bool:
    """Add a fund to user watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_watchlist (fund_code, fund_name)
            VALUES (?, ?)
            ON CONFLICT(fund_code) DO NOTHING
        """, (fund_code, fund_name))
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Error adding {fund_code} to watchlist: {e}")
        return False
    finally:
        conn.close()

def remove_from_watchlist(fund_code: str) -> bool:
    """Remove a fund from user watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_watchlist WHERE fund_code = ?", (fund_code,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Error removing {fund_code} from watchlist: {e}")
        return False
    finally:
        conn.close()

def get_watchlist() -> List[Dict[str, Any]]:
    """Get all funds in watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_watchlist ORDER BY added_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error getting watchlist: {e}")
        return []
    finally:
        conn.close()

def is_in_watchlist(fund_code: str) -> bool:
    """Check if a fund is in the watchlist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user_watchlist WHERE fund_code = ?", (fund_code,))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"Error checking watchlist for {fund_code}: {e}")
        return False
    finally:
        conn.close()
