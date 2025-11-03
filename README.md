# Quant Developer Analytics Dashboard

This project is a real-time analytics application built for the Quant Developer Evaluation. [cite_start]It ingests live tick data from Binance, stores it in an SQLite database, computes quantitative analytics, and presents them in an interactive Streamlit dashboard[cite: 3].

## Architecture

[cite_start]*(Insert your `architecture.png` image here)* [cite: 43]

The system is composed of four main Python components:

1.  **`db_setup.py`**: A one-time script that creates the `data/` directory and initializes the `ticks.db` SQLite database with the correct table schema.
2.  **`ingest.py`**: A persistent data ingestion service. [cite_start]It uses the `websocket-client` library to connect to the Binance WebSocket stream for multiple symbols (e.g., `btcusdt`, `ethusdt`)[cite: 12]. To handle concurrent data streams safely, it uses a thread-safe **Queue**. WebSocket threads act as producers, placing trade data into the queue, while a single, dedicated database thread acts as a consumer, writing data to the SQLite database. This design prevents database locking errors.
3.  **`analytics.py`**: A module containing all core quantitative functions. [cite_start]It uses `pandas` for data loading and resampling [cite: 14] [cite_start]and `statsmodels` for statistical calculations like OLS regression and the ADF test[cite: 15].
4.  **`app.py`**: The main Streamlit application. [cite_start]It serves as the frontend, loading data from `ticks.db`, passing it to the `analytics.py` functions, and visualizing the results using interactive Plotly charts[cite: 21, 24].

## 📊 Features Implemented

* **Real-Time Data Ingestion**: Connects to Binance WebSocket for live trade data[cite: 12].
* [cite_start]**Timeframe Resampling**: Aggregates tick data into 1s, 30s, 1min, or 5min OHLC bars[cite: 14].
* [cite_start]**OLS Hedge Ratio**: Calculates the hedge ratio between two selected symbols using Ordinary Least Squares regression[cite: 15].
* **Pair Analytics**: Computes and plots the pair's spread and normalized Z-Score[cite: 15, 24].
* [cite_start]**Rolling Correlation**: Calculates and plots the rolling correlation between the two symbols[cite: 15].
* [cite_start]**Statistical Tests**: Includes an OLS regression summary and an Augmented Dickey-Fuller (ADF) test to check the spread for stationarity[cite: 15].
* **Live Alerting**: A "Live View" tab shows the most recent Z-Score and displays a prominent alert if it breaches a user-defined threshold[cite: 17, 19].
* [cite_start]**Interactive Charts**: All charts are built with Plotly, supporting zoom, pan, and hover functionalities[cite: 26].
* [cite_start]**Data Export**: A "Data Export" tab allows the user to download the processed analytics data (prices, spread, z-score) as a CSV file[cite: 20].

##  Setup & Dependencies

This project uses Python. All dependencies are listed in `requirements.txt`.

1.  **Clone the repository:**
    ```bash
    git clone [your-repo-url]
    cd quant_project/quant_app
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # (or venv\Scripts\activate on Windows)
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database (Run this ONCE):**
    ```bash
    python db_setup.py
    ```
    *This will create the `data/ticks.db` file.*

## How to Run

You must run **two processes simultaneously** in separate terminals.

1.  **Terminal 1: Start the Data Ingestion**
    *Make sure your virtual environment is active.*
    ```bash
    python ingest.py
    ```
    *You will see log messages as trades are saved. Leave this terminal running.*

2.  **Terminal 2: Start the Streamlit App**
    *Open a new terminal and activate the virtual environment.*
    ```bash
    streamlit run app.py
    ```
    *This will automatically open the dashboard in your web browser. Note: It may take 5-10 minutes of data collection for the statistical analytics (like OLS) to have enough data to run without warnings.*

##  AI Usage Transparency

[cite_start]*(Per the assignment[cite: 42], you must fill this section out yourself. Here is a template based on our conversation.)*

[cite_start]I used Google's Gemini (an LLM) to assist in this project, as permitted by the assignment[cite: 50]. The AI's role was that of a technical assistant and pair programmer.

* **Scaffolding:** Generated the initial multi-file project structure (`app.py`, `ingest.py`, etc.).
* **Architecture:** Refined the architecture, suggesting a **Queue-based** system for `ingest.py` to solve database locking errors.
* **Code Implementation:** Provided the Python code for:
    * Connecting to the WebSocket (`websocket-client`).
    * Setting up the Streamlit UI layout and Plotly charts.
    * Implementing the analytics functions in `analytics.py` using `pandas` and `statsmodels`.
* **Debugging:** Helped diagnose and fix runtime errors, such as `database is locked`, `MissingDataError` from statsmodels, and `StreamlitDuplicateElementId`.
* **Documentation:** Generated this `README.md` file based on the final code.
