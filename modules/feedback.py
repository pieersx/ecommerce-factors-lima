import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "feedback.json")


def load_feedback() -> List[Dict]:
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_feedback(entry: Dict[str, Any]) -> bool:
    records = load_feedback()
    entry["timestamp"] = datetime.utcnow().isoformat()
    records.append(entry)
    try:
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_feedback_summary() -> Dict[str, Any]:
    records = load_feedback()
    if not records:
        return {"total": 0, "avg_rating": None, "entries": []}

    ratings = [r.get("rating") for r in records if r.get("rating") is not None]
    avg = sum(ratings) / len(ratings) if ratings else None

    return {
        "total": len(records),
        "avg_rating": round(avg, 2) if avg else None,
        "entries": records[-5:],  # últimas 5
    }