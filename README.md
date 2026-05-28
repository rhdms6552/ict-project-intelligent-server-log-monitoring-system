# Intelligent Server Log Monitoring System

## Overview
This project implements a real-time server log monitoring pipeline under simulated network constraints.
It was developed for an ICT Applied Technology individual project.

The system covers the full pipeline:
- synthetic log generation
- network delay, drop, and corruption simulation
- log collection and buffering
- corrupted log recovery
- rule-based status decision
- real-time Streamlit dashboard

## Repository Structure
```text
/
├── src/                     # all source code
├── dashboard/               # web GUI code
├── data/                    # sample or synthetic data
├── README.md
└── TROUBLESHOOTING.md
```

## Core Logic
### 1. Data Generation
- `src/log_generator.py` generates synthetic logs in real time.
- Log format:
  `[YYYY-MM-DD HH:MM:SS] LEVEL message`
- Level distribution:
  - INFO 60%
  - WARNING 25%
  - ERROR 12%
  - CRITICAL 3%

### 2. Network Constraint Simulation
- `src/network_constraint.py` simulates:
  - delay
  - random drop
  - log corruption
- Parameters are controlled through `data/params.json` and the dashboard sliders.

### 3. Log Processing
- `src/log_processor.py` buffers logs and stores:
  - latest 20-log sliding window
  - latest 200 log history
  - total received, dropped, corrupted, and recovered counts
  - error-rate time series for the last 60 seconds

### 4. Recovery
- `src/ai_recovery.py` uses `regex + difflib`.
- The main target is recovery of corrupted log level tokens such as:
  - `ERR0R -> ERROR`
  - `W?RNING -> WARNING`

### 5. Decision Engine
- `src/decision_engine.py` classifies the system into:
  - `CRITICAL`: at least one CRITICAL log in the recent 20 logs
  - `WARNING`: at least three ERROR logs and no CRITICAL
  - `STABLE`: otherwise
- It also calculates an `anomaly_score` between `0.0` and `1.0`.

### 6. Dashboard
- `dashboard/dashboard.py` is a Streamlit dashboard.
- It visualizes:
  - system status
  - anomaly score
  - log level counts
  - recovery statistics
  - error-rate graph
  - live log stream
  - constraint controls

## Data Sharing Design
- `multiprocessing.Queue`:
  log generator -> backend pipeline
- `data/state.json`:
  backend -> dashboard
- `data/params.json`:
  dashboard -> backend

## How to Run
### Backend
```powershell
cd src
python main.py
```

### Dashboard
```powershell
cd ..
streamlit run dashboard/dashboard.py
```

## Required Packages
```bash
pip install streamlit pandas
```

## Demo / Video Link
Mandatory submission item:

`Add your video link here before final submission`

Example:
`https://youtu.be/your-video-id`

## Notes
- The dashboard shows a `WAITING` state if the backend is not running or `state.json` is stale.
- Recovered logs are shown as `RECOVERED` entries in the live log stream.
- Because logs are generated randomly, the system may move between `STABLE`, `WARNING`, and `CRITICAL` in real time.
