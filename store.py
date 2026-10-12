# store.py
import sqlite3
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prevalence (
            date TEXT,
            source TEXT,
            prevalence_proportion REAL,
            prevalence_ratio INTEGER,
            lower_ci REAL,
            upper_ci REAL,
            metric_type TEXT,
            raw_value TEXT,
            PRIMARY KEY (date, source, metric_type)
        )
    """)
    conn.commit()
    conn.close()


def store_records(records: list[dict]):
    conn = sqlite3.connect(DB_PATH)
    for rec in records:
        conn.execute("""
            INSERT OR REPLACE INTO prevalence
            (date, source, prevalence_proportion, prevalence_ratio,
             lower_ci, upper_ci, metric_type, raw_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec.get("date"),
            rec.get("source"),
            rec.get("prevalence_proportion"),
            rec.get("prevalence_ratio"),
            rec.get("lower_ci"),
            rec.get("upper_ci"),
            rec.get("metric_type", "prevalence"),
            str(rec.get("raw_value", "")),
        ))
    conn.commit()
    conn.close()