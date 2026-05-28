"""
core/storage.py
All file I/O using pandas DataFrames.
Sessions are stored in data/sessions.csv
"""

import os
import pandas as pd
from datetime import datetime

DATA_DIR      = os.path.join(os.path.dirname(__file__), "..", "data")
SESSION_FILE  = os.path.join(DATA_DIR, "sessions.csv")

COLUMNS = ["vehicle_number", "vehicle_type", "slot_id", "station",
           "entry_time", "exit_time", "duration_hrs", "fee"]


def _ensure_csv():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(SESSION_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(SESSION_FILE, index=False)


def save_session(vehicle, slot_id: str, station: str,
                 exit_time: datetime, fee: float):
    _ensure_csv()
    duration = (exit_time - vehicle.entry_time).total_seconds() / 3600
    row = pd.DataFrame([{
        "vehicle_number": vehicle.number,
        "vehicle_type"  : vehicle.vehicle_type,
        "slot_id"       : slot_id,
        "station"       : station,
        "entry_time"    : vehicle.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
        "exit_time"     : exit_time.strftime("%Y-%m-%d %H:%M:%S"),
        "duration_hrs"  : round(duration, 2),
        "fee"           : round(fee, 2),
    }])
    row.to_csv(SESSION_FILE, mode="a", header=False, index=False)


def load_sessions() -> pd.DataFrame:
    _ensure_csv()
    df = pd.read_csv(SESSION_FILE)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df["exit_time"]   = pd.to_datetime(df["exit_time"])
    df["entry_time"]  = pd.to_datetime(df["entry_time"])
    df["date"]        = df["exit_time"].dt.date
    df["hour"]        = df["exit_time"].dt.hour
    df["fee"]         = pd.to_numeric(df["fee"], errors="coerce").fillna(0)
    df["duration_hrs"]= pd.to_numeric(df["duration_hrs"], errors="coerce").fillna(0)
    return df


def daily_summary(df: pd.DataFrame, date=None) -> dict:
    if date is None:
        date = datetime.now().date()
    day_df = df[df["date"] == date] if not df.empty and "date" in df.columns else pd.DataFrame()
    return {
        "date"              : str(date),
        "total_sessions"    : len(day_df),
        "total_revenue"     : round(day_df["fee"].sum(), 2) if not day_df.empty else 0,
        "two_wheeler_count" : len(day_df[day_df["vehicle_type"] == "2W"]) if not day_df.empty else 0,
        "four_wheeler_count": len(day_df[day_df["vehicle_type"] == "4W"]) if not day_df.empty else 0,
        "tw_revenue"        : round(day_df[day_df["vehicle_type"] == "2W"]["fee"].sum(), 2) if not day_df.empty else 0,
        "fw_revenue"        : round(day_df[day_df["vehicle_type"] == "4W"]["fee"].sum(), 2) if not day_df.empty else 0,
        "avg_duration"      : round(day_df["duration_hrs"].mean(), 2) if not day_df.empty else 0,
    }


def search_vehicle_history(df: pd.DataFrame, number: str) -> pd.DataFrame:
    number = number.strip().upper()
    if df.empty:
        return pd.DataFrame()
    return df[df["vehicle_number"] == number].sort_values("exit_time", ascending=False)
