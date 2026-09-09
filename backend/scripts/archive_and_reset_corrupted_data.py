"""
Script to safely archive corrupted paper trading records and initialize a fresh experimental baseline.
"""

import os
import shutil
import sqlite3
from datetime import datetime, timezone

DB_PATH = "data/trading_bot.db"
BACKUP_PATH = "data/trading_bot_corrupted_backup.db"


def archive_and_reset():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} does not exist. Nothing to archive.")
        return

    # 1. Create backup archive of corrupted database
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Archived existing database to: {BACKUP_PATH}")

    # 2. Connect to database and clear corrupted tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trades")
    trades_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM equity_snapshots")
    snapshots_count = cursor.fetchone()[0]

    print(f"Purging {trades_count} trades, {orders_count} orders, and {snapshots_count} old snapshots...")

    cursor.execute("DELETE FROM trades")
    cursor.execute("DELETE FROM orders")
    cursor.execute("DELETE FROM bot_logs WHERE event_type IN ('ORDER_FILLED', 'POSITION_CLOSED')")
    cursor.execute("DELETE FROM equity_snapshots")

    # 3. Seed fresh baseline snapshot ($10,000 USDT testnet capital)
    now_utc = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO equity_snapshots (
            timestamp, total_equity, available_balance, unrealized_pnl,
            realized_pnl, drawdown_pct, high_water_mark, open_positions_count, mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_utc, 10000.0, 10000.0, 0.0, 0.0, 0.0, 10000.0, 0, "PAPER"))

    conn.commit()
    conn.close()

    print("Fresh experiment initialized with $10,000.00 baseline equity.")


if __name__ == "__main__":
    archive_and_reset()
