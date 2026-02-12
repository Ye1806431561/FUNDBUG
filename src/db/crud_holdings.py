import sqlite3
import logging
from typing import List, Dict, Any
from src.db.models import get_connection

logger = logging.getLogger(__name__)

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
