# Troubleshooting

## 1. Multiprocessing permission or duplicate-process issues
### Problem
While testing on Windows, multiple backend processes were sometimes left running at the same time.
This caused inconsistent dashboard behavior, duplicated updates, and confusing status transitions.

### Solution
- ensured the backend uses:
  - `if __name__ == "__main__":`
  - `multiprocessing.freeze_support()`
- stopped duplicate Python processes and restarted the project with exactly one backend instance and one dashboard instance

## 2. Dashboard slider values changing unexpectedly
### Problem
The dashboard auto-refreshes every second.
Originally, slider values could appear to reset or change unexpectedly because the UI kept reloading while reading parameter values from disk.

### Solution
- updated the Streamlit dashboard to use `st.session_state`
- persisted slider values through a dedicated save callback
- kept `data/params.json` as the backend-facing parameter source

## 3. Recovered logs not clearly visible
### Problem
Recovered logs were being counted internally, but they were not easy to recognize in the live log stream.
Also, early corruption logic damaged the entire log too aggressively, making recovery opportunities less visible.

### Solution
- changed corruption behavior so the log level token is corrupted first
- updated the live log stream renderer to highlight recovered entries as `RECOVERED`
- added a `Recovered from:` detail line for recovered items

## 4. Dashboard showing stale data when backend is stopped
### Problem
If `state.json` remained on disk after the backend stopped, the dashboard could continue showing old information.

### Solution
- added stale-state detection in the dashboard
- if `state.json` is missing or older than a short threshold, the dashboard shows `WAITING` and an offline message

## 5. Encoding issues in documentation
### Problem
Some earlier text content became unreadable due to encoding problems.

### Solution
- rewrote the documentation files in clean UTF-8 text
- kept the final repository documentation in simple English for submission clarity
