# run_etl.py
import json
import logging
import sqlite3
import subprocess
from pathlib import Path

from config import DB_PATH, JSON_PATH
from fetchers import fetch_ukhsa, fetch_buds, fetch_disease_sh
from store import init_db, store_records

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("etl.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

REPO_DIR = Path(r"C:\covid-dashboard")


def export_json():
    """Export the prevalence table to a JSON file."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT date, source, prevalence_proportion, prevalence_ratio,
               lower_ci, upper_ci, metric_type, raw_value
        FROM prevalence
        ORDER BY date ASC
    """).fetchall()
    conn.close()

    data = [dict(r) for r in rows]
    Path(JSON_PATH).write_text(
        json.dumps(data, indent=2, default=str), encoding="utf-8"
    )
    logger.info(f"Exported {len(data)} rows to {JSON_PATH}")


def git_push():
    """Commit and push the updated JSON to GitHub."""
    try:
        subprocess.run(
            ["git", "add", "data/prevalence.json"],
            cwd=REPO_DIR, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Update prevalence data"],
            cwd=REPO_DIR, check=True, capture_output=True, text=True,
        )
        subprocess.run(
            ["git", "push"],
            cwd=REPO_DIR, check=True, capture_output=True, text=True,
        )
        logger.info("Pushed prevalence.json to GitHub")
    except subprocess.CalledProcessError as e:
        # A "nothing to commit" exit is benign
        stderr = (e.stderr or "") + (e.stdout or "")
        if "nothing to commit" in stderr.lower():
            logger.info("No changes to commit")
        else:
            logger.error(f"Git push failed: {stderr}")


def main():
    init_db()

    # --- UKHSA ---
    for metric in [
        "COVID-19_testing_positivityByDay",
        "COVID-19_healthcare_admissionByDay",
        "COVID-19_healthcare_ICUadmissionByDay",
    ]:
        try:
            df = fetch_ukhsa(metric)
            records = []
            for _, row in df.iterrows():
                records.append({
                    "date": row.get("date"),
                    "source": "UKHSA",
                    "metric_type": metric,
                    "raw_value": str(row.get("value")),
                })
            store_records(records)
            logger.info(f"UKHSA {metric}: stored {len(records)} rows")
        except Exception as e:
            logger.error(f"UKHSA {metric} failed: {e}")

    # --- BuDS ---
    try:
        buds = fetch_buds()
        if buds and buds.get("date"):
            store_records([{
                "date": buds["date"],
                "source": "BuDS",
                "prevalence_proportion": buds["prevalence_proportion"],
                "prevalence_ratio": buds["prevalence_ratio"],
                "metric_type": "prevalence",
                "raw_value": buds.get("url", ""),
            }])
            logger.info(f"BuDS: 1 in {buds['prevalence_ratio']}")
        else:
            logger.warning("BuDS: no data extracted — check page structure")
    except Exception as e:
        logger.error(f"BuDS failed: {e}")

    # --- disease.sh ---
    try:
        ds = fetch_disease_sh()
        store_records([{
            "date": ds["date"],
            "source": "disease.sh",
            "metric_type": "cases",
            "raw_value": str(ds.get("cases")),
        }])
        logger.info(f"disease.sh: {ds.get('cases')} cases")
    except Exception as e:
        logger.error(f"disease.sh failed: {e}")

    export_json()
    git_push()


if __name__ == "__main__":
    main()