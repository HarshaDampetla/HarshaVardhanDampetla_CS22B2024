import sqlite3
import os

DB_DIR = 'data'
DB_PATH = os.path.join(DB_DIR, 'ticks.db')

# Create data directory if it doesn't exist
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
    print(f"Created directory: {DB_DIR}")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the main table for tick data
    # Using timestamp (ms) and symbol as a composite primary key 
    # ensures we don't store duplicate ticks for the same symbol.
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ticks (
        timestamp INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        price REAL NOT NULL,
        size REAL NOT NULL,
        PRIMARY KEY (timestamp, symbol)
    )
    ''')
    
    conn.commit()
    print(f"Database '{DB_PATH}' and table 'ticks' created successfully.")

except sqlite3.Error as e:
    print(f"An error occurred: {e}")

finally:
    if conn:
        conn.close()