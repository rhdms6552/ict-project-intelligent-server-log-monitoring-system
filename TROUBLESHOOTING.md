# Troubleshooting

This document summarizes the major bugs and issues encountered during development and how they were solved.

## 1. Duplicate Backend Processes on Windows

### Symptoms
- The dashboard values changed in unexpected ways.
- `state.json` was updated too frequently or inconsistently.
- The system status sometimes changed in a confusing way because multiple `main.py` processes were running at the same time.

### Cause
The backend uses `multiprocessing` on Windows. During repeated testing, old Python backend processes were not always stopped before starting a new one. As a result, several backend instances wrote to the same `data/state.json` file.

### Solution
- Added the Windows multiprocessing guard in `src/main.py`:
  - `if __name__ == "__main__":`
  - `multiprocessing.freeze_support()`
- Stopped duplicate Python processes during testing.
- Restarted the project with only one backend instance and one Streamlit dashboard instance.

### Verification
After cleanup, only one backend process updated `state.json`, and dashboard values became consistent again.

## 2. Streamlit Slider Values Changed Unexpectedly

### Symptoms
- `Delay`, `Drop Rate`, and `Corruption Rate` sometimes appeared to change or reset during dashboard refresh.
- This made the live demo difficult because the selected values did not always feel stable.

### Cause
The dashboard refreshes every second with `st.rerun()`. The first version loaded slider values directly from `data/params.json` on every rerun, which could conflict with Streamlit's widget state.

### Solution
- Updated `dashboard/dashboard.py` to use `st.session_state` for slider values.
- Added a dedicated callback to save changed slider values to `data/params.json`.
- Kept `params.json` as the backend-facing source of network constraint parameters.

### Verification
After this change, slider values stayed stable during automatic dashboard refreshes, and backend parameter updates still worked.

## 3. Recovered Logs Were Not Clearly Visible

### Symptoms
- The `Recovered` counter increased internally, but blue `RECOVERED` logs were hard to see in the dashboard.
- During the demo, it was not obvious where the AI-based recovery result appeared.

### Cause
The original live log stream rendering did not make recovered entries visually prominent enough. Also, the early corruption logic damaged the whole log too randomly, so recoverable level-token corruption did not appear often enough.

### Solution
- Changed `src/network_constraint.py` so the log level token is corrupted first.
- Kept the log structure mostly intact so `ai_recovery.py` can parse and recover the level token.
- Updated `dashboard/dashboard.py` so recovered entries are displayed as blue `RECOVERED` rows.
- Added a `Recovered from:` line to show the corrupted original value.

### Verification
After increasing `Corruption Rate`, recovered logs appeared in the `Live Log Stream`, and the `Recovered` counter increased as expected.

## 4. Dashboard Showed Stale Data When Backend Was Stopped

### Symptoms
- If the backend stopped, the dashboard still displayed the last old values from `state.json`.
- This made it look like the system was still running even when the backend was offline.

### Cause
The dashboard only checked whether `state.json` existed. It did not check whether the file was still being updated.

### Solution
- Added stale-state detection in `dashboard/dashboard.py`.
- If `state.json` is missing or older than a short threshold, the dashboard shows:
  - `WAITING`
  - an offline message
  - empty counters and logs

### Verification
When the backend is stopped, the dashboard now changes to a waiting/offline state instead of showing outdated data.

## 5. Live Log Stream Displayed Raw HTML-like Text

### Symptoms
- At one point, the live log stream displayed HTML-like text instead of clean colored log rows.
- This made the dashboard harder to read during presentation rehearsal.

### Cause
The log stream used HTML rendering, but the output was not handled cleanly enough for the Streamlit version being used.

### Solution
- Escaped dynamic log text with Python's `html.escape`.
- Switched the log stream rendering to `st.html`.
- Preserved color labels for `INFO`, `WARNING`, `ERROR`, `CRITICAL`, `DROPPED`, and `RECOVERED`.

### Verification
The log stream now displays clean colored rows instead of raw HTML fragments.

## 6. Documentation Encoding Problem

### Symptoms
- Some Korean text in `README.md` and `TROUBLESHOOTING.md` became unreadable due to encoding issues.

### Cause
The text was written or viewed with inconsistent character encoding.

### Solution
- Rewrote the final documentation in clean UTF-8 compatible English.
- Kept the repository documentation simple and submission-focused.

### Verification
The final `README.md` and `TROUBLESHOOTING.md` are readable on GitHub and in the local editor.

## 7. GitHub Authentication Issue During Submission

### Symptoms
- The initial `git push` failed with an authentication error.
- The saved GitHub credential existed but was not accepted by GitHub.

### Cause
The stored credential was outdated or not usable for modern GitHub authentication.

### Solution
- Refreshed GitHub authentication using Git Credential Manager.
- Re-ran the GitHub repository creation and push process after login.

### Verification
The repository was successfully pushed to GitHub after authentication was refreshed.
