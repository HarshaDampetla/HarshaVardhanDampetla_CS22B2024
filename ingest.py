import websocket
import json
import sqlite3
import time
from threading import Thread
from queue import Queue

# --- Configuration ---
SYMBOLS = ["btcusdt", "ethusdt"] # Symbols from the assignment
DB_PATH = 'data/ticks.db'
# ---------------------

# A thread-safe queue to hold messages from websockets
data_queue = Queue()

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    # Enable Write-Ahead Logging (WAL) for concurrent access
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def database_writer():
    """
    A dedicated thread that pulls data from the queue and writes to the DB.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    print("--- Database writer thread started. ---")

    while True:
        try:
            # Get data from the queue (this will block until data is available)
            trade_data = data_queue.get()

            # Insert into database
            cursor.execute(
                "INSERT INTO ticks (timestamp, symbol, price, size) VALUES (?, ?, ?, ?)",
                (trade_data['ts'], trade_data['symbol'], trade_data['price'], trade_data['size'])
            )
            conn.commit()
            
            print(f"Logged: {trade_data['symbol']} @ {trade_data['price']}")

        except sqlite3.IntegrityError:
            # This is expected if a tick with the same timestamp/symbol arrives
            pass
        except Exception as e:
            print(f"DB Writer Error: {e}")
        finally:
            # Mark the task as done
            data_queue.task_done()

def on_message(ws, message):
    """
    Callback function to process incoming WebSocket messages.
    This function should be very fast: parse JSON, add to queue.
    """
    try:
        data = json.loads(message)
        
        # Check if it's a trade event
        if data.get('e') == 'trade':
            # Normalize data
            trade_data = {
                'ts': data['T'],      # Event time (timestamp)
                'symbol': data['s'],
                'price': float(data['p']),
                'size': float(data['q'])
            }
            # Put the data into the queue for the writer thread
            data_queue.put(trade_data)
            
    except Exception as e:
        print(f"Error processing message: {e}\nMessage: {message}")

def on_error(ws, error):
    print(f"WS Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"--- WS Closed (Code: {close_status_code}) --- Retrying in 5s...")
    time.sleep(5)
    start_websocket(ws.symbol) # Simple reconnect logic

def on_open(ws):
    print(f"--- WS Connected: {ws.symbol} ---")
    
def start_websocket(symbol):
    """Starts a WebSocket connection for a given symbol."""
    print(f"Attempting to connect to: {symbol}")
    url = f"wss://fstream.binance.com/ws/{symbol.lower()}@trade"
    ws = websocket.WebSocketApp(url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.symbol = symbol # Attach symbol to ws object for reconnects
    ws.run_forever()

if __name__ == "__main__":
    print(f"Starting data ingestion for symbols: {', '.join(SYMBOLS)}...")
    print(f"Storing data in: {DB_PATH}")

    # Start the single database writer thread
    # daemon=True means it will close when the main program exits
    db_thread = Thread(target=database_writer, daemon=True)
    db_thread.start()

    # Start a separate thread for each symbol's WebSocket connection
    ws_threads = []
    for sym in SYMBOLS:
        thread = Thread(target=start_websocket, args=(sym,))
        thread.start()
        ws_threads.append(thread)
        time.sleep(1) # Stagger connections slightly

    for t in ws_threads:
        t.join()