# fetchers.py
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from config import UKHSA_BASE, DATE_FROM, DATE_TO


def fetch_ukhsa(metric: str) -> pd.DataFrame:
    """Fetch a single metric from the UKHSA Data Dashboard API."""
    url = (
        f"{UKHSA_BASE}/themes/infectious_disease/sub_themes/respiratory/"
        f"topics/COVID-19/geography_types/Nation/geographies/England/"
        f"metrics/{metric}"
    )
    params = {"date_from": DATE_FROM, "date_to": DATE_TO}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    payload = r.json()
    # UKHSA returns results under the "results" key
    df = pd.DataFrame(payload.get("results", []))
    df["source"] = "UKHSA"
    df["metric_type"] = metric
    return df


def fetch_buds() -> dict:
    """Scrape the latest BuDS weekly risk assessment.

    BuDS publishes weekly posts at URLs of the form:
    https://buds.org.uk/covid-19-risk-assessment-week-ending-27-september-2026/
    The headline figure is "1 in every X people in England now infected".
    """
    listing_url = "https://buds.org.uk/covid-19-risk-assessment/"
    r = requests.get(listing_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Find the first matching assessment link (most recent first)
    latest_link = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "covid-19-risk-assessment-week-ending" in href:
            latest_link = href
            break

    if not latest_link:
        return {}

    r2 = requests.get(latest_link, timeout=30)
    soup2 = BeautifulSoup(r2.text, "html.parser")
    text = soup2.get_text(" ", strip=True)

    # Extract "1 in every X" ratio
    match = re.search(r"1 in every ([\d,]+) people", text)
    ratio = int(match.group(1).replace(",", "")) if match else None

    # Extract the date from the URL slug
    dt = None
    date_match = re.search(
        r"week-ending-(\d+)-([a-z]+)-(\d{4})", latest_link, re.IGNORECASE
    )
    if date_match:
        day = date_match.group(1)
        month = date_match.group(2).capitalize()
        year = date_match.group(3)
        try:
            dt = datetime.strptime(
                f"{day} {month} {year}", "%d %B %Y"
            ).date()
        except ValueError:
            dt = None

    return {
        "source": "BuDS",
        "date": str(dt) if dt else None,
        "prevalence_ratio": ratio,
        "prevalence_proportion": 1 / ratio if ratio else None,
        "url": latest_link,
    }


def fetch_disease_sh() -> dict:
    """Fetch UK aggregate data from disease.sh (no auth required)."""
    url = "https://disease.sh/v3/covid-19/countries/UK"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    return {
        "source": "disease.sh",
        "date": str(pd.Timestamp.today().date()),
        "cases": data.get("cases"),
        "active": data.get("active"),
        "tests": data.get("tests"),
        "hospitalizations": data.get("hospitalizations"),
    }