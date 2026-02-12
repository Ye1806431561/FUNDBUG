import sqlite3
import logging
from typing import List, Dict, Any
from src.db.models import get_connection

logger = logging.getLogger(__name__)

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
