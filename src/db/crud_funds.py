import sqlite3
import logging
from typing import List, Optional, Dict, Any
from src.db.models import get_connection

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
