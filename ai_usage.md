# AI Usage Transparency Report

As permitted by the evaluation assignment, I used Google's Gemini (an LLM) as a collaborative coding assistant to help implement my project design.

My role was to design the end-to-end system architecture, define the components, and specify the logic. The AI's role was to act as a pair programmer, translating my designs into functional code, providing boilerplate, and helping to debug runtime errors.

## 1. Architecture & Project Design

I designed the system's architecture, which consists of two main, decoupled components:

1.  **Ingestion Service (`ingest.py`):** A persistent Python script to handle data collection. To prevent database locking and ensure stability, I designed this service using a **producer-consumer pattern**. I specified that multiple WebSocket threads (producers) would place incoming trade data onto a thread-safe `Queue`, and a single, separate database thread (consumer) would write this data to SQLite.
2.  **Dashboard App (`app.py`):** A Streamlit application to serve as the analytics frontend. I designed this to read from the SQLite database, perform all required analytics (resampling, OLS, z-score), and present them in an interactive dashboard with Plotly charts.

The AI's role was to help write the Python code to implement this pre-defined architecture.

## 2. File-by-File Contributions

### `db_setup.py`
* **My Role:** Specified the need for a setup script to create the `ticks` table with a composite primary key.
* **AI's Role:** Generated the `sqlite3` boilerplate code to execute this schema.

### `ingest.py`
* **My Role:** Designed the multi-threaded, Queue-based architecture to solve the database locking problem.
* **AI's Role:** Implemented my design by writing the `websocket-client` callbacks (`on_message`) to `data_queue.put()` and creating the `database_writer` thread to consume from the queue (`data_queue.get()`) and write to the database.

### `analytics.py`
* **My Role:** Defined all the required analytics functions as per the assignment PDF (e.g., `load_data`, `resample_data`, `compute_ols_hedge_ratio`, `compute_zscore`, `run_adf_test`).
* **AI's Role:** Provided the specific `pandas` and `statsmodels` code snippets to implement each of these defined functions.

### `app.py`
* **My Role:** Designed the complete UI layout, including the sidebar controls, the tabbed interface, and the specific charts required (prices, spread, z-score, correlation). I also specified the need for a live update mechanism and an alerting feature.
* **AI's Role:** Generated the Streamlit code for the UI (e.g., `st.sidebar`, `st.tabs`), the `plotly` code for the charts, and the `st.rerun()` logic for the live updates.

## 3. Debugging

Throughout the development process, I ran the code, identified runtime errors, and provided the traceback logs to the AI. The AI's role was to act as a debugger and suggest the specific code-level fix.

* **Error:** `MissingDataError: exog contains inf or nans`
    * **AI Fix:** Suggested adding `.dropna()` in the OLS function.
* **Error:** `StreamlitDuplicateElementId`
    * **AI Fix:** Explained the need for a unique `key` argument in each `st.plotly_chart` call.
* **Error:** `MediaFileStorageError` (on download)
    * **AI Fix:** Identified that `@st.cache_data` should be removed from the download helper function.
* **Warnings:** `use_container_width` and `Series._getitem_`
    * **AI Fix:** Provided the updated syntax (`width='stretch'` and `.iloc[1]`).

## 4. Documentation

I wrote the project's `README.md` and this `ai_usage.md` document. I used the AI to help format them into clean Markdown.