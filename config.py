# config.py
import os
from datetime import date, timedelta

# Paths
BASE_DIR = r"C:\covid-dashboard"
DB_PATH = os.path.join(BASE_DIR, "data", "covid_prevalence.db")
JSON_PATH = os.path.join(BASE_DIR, "data", "prevalence.json")

# UKHSA API
UKHSA_BASE = "https://api.ukhsa-dashboard.data.gov.uk"

# Date range: last 120 days (covers the current wave plus a buffer)
DATE_TO = date.today().isoformat()
DATE_FROM = (date.today() - timedelta(days=120)).isoformat()