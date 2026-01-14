# Monopoly Engine + Minimal Web UI

## Requirements
- Python 3.9+
- pip

## Install
```bash
python -m pip install -r requirements.txt
```

## Run the web app
```bash
python -m uvicorn app:app --reload
```
Open `http://localhost:8000` in your browser.

## Run CLI simulation (optional)
```bash
python cli.py --players Alice Bob --turns 20 --auto-buy
```

## Run tests
```bash
pytest -q
```

## Python venv
# 1) Make sure venv support is installed
sudo apt update
sudo apt install -y python3-venv python3-full

# 2) Create a virtual environment
python3 -m venv .venv

# 3) Activate it
source .venv/bin/activate

# 4) Upgrade pip tools (inside venv)
python -m pip install --upgrade pip setuptools wheel

# 5) Install your deps
pip install -r requirements.txt

