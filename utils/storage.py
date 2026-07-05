"""Persistencia local SQLite para auditorías, correcciones y feedback."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "pec_auditor.db"


def database_path() -> Path:
    return Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB)))


def connection() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    conn = connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                url TEXT NOT NULL,
                pages_reviewed INTEGER NOT NULL DEFAULT 0,
                is_ecommerce INTEGER NOT NULL DEFAULT 1,
                qualification_status TEXT NOT NULL DEFAULT 'qualified',
                ecommerce_evidence_json TEXT NOT NULL DEFAULT '[]',
                confidence_score INTEGER NOT NULL DEFAULT 0,
                confidence_label TEXT NOT NULL DEFAULT 'No disponible',
                confidence_reasons_json TEXT NOT NULL DEFAULT '[]',
                brand_assets_json TEXT NOT NULL DEFAULT '{}',
                ai_review_json TEXT,
                warnings_json TEXT NOT NULL,
                pec_score REAL NOT NULL,
                classification TEXT NOT NULL,
                dimensions_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS factor_results (
                audit_id INTEGER NOT NULL,
                factor_id TEXT NOT NULL,
                name TEXT NOT NULL,
                dimension TEXT NOT NULL,
                status TEXT NOT NULL,
                score REAL NOT NULL,
                evidence TEXT NOT NULL,
                source_url TEXT NOT NULL,
                manual_correction TEXT,
                recommendation TEXT NOT NULL,
                PRIMARY KEY (audit_id, factor_id),
                FOREIGN KEY (audit_id) REFERENCES audits(id)
            );
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL
            );
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(audits)").fetchall()}
        if "pages_reviewed" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN pages_reviewed INTEGER NOT NULL DEFAULT 0")
        if "is_ecommerce" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN is_ecommerce INTEGER NOT NULL DEFAULT 1")
        if "qualification_status" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN qualification_status TEXT NOT NULL DEFAULT 'qualified'")
        if "ecommerce_evidence_json" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN ecommerce_evidence_json TEXT NOT NULL DEFAULT '[]'")
        if "confidence_score" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN confidence_score INTEGER NOT NULL DEFAULT 0")
        if "confidence_label" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN confidence_label TEXT NOT NULL DEFAULT 'No disponible'")
        if "confidence_reasons_json" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN confidence_reasons_json TEXT NOT NULL DEFAULT '[]'")
        if "brand_assets_json" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN brand_assets_json TEXT NOT NULL DEFAULT '{}'")
        if "ai_review_json" not in columns:
            conn.execute("ALTER TABLE audits ADD COLUMN ai_review_json TEXT")
        conn.commit()
    finally:
        conn.close()


def save_audit(result: dict) -> int:
    initialize_database()
    conn = connection()
    try:
        cursor = conn.execute(
            """INSERT INTO audits(
                   created_at, url, pages_reviewed, is_ecommerce, qualification_status, ecommerce_evidence_json,
                   confidence_score, confidence_label, confidence_reasons_json, brand_assets_json, ai_review_json,
                   warnings_json, pec_score, classification, dimensions_json
               )
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                result["url"],
                result.get("pages_reviewed", 0),
                1 if result.get("is_ecommerce", True) else 0,
                result.get("qualification_status", "qualified"),
                json.dumps(result.get("ecommerce_evidence", []), ensure_ascii=False),
                result.get("confidence_score", 0),
                result.get("confidence_label", "No disponible"),
                json.dumps(result.get("confidence_reasons", []), ensure_ascii=False),
                json.dumps(result.get("brand_assets", {}), ensure_ascii=False),
                json.dumps(result.get("ai_review"), ensure_ascii=False) if result.get("ai_review") else None,
                json.dumps(result.get("warnings", []), ensure_ascii=False),
                result["pec_score"],
                result["classification"],
                json.dumps(result["dimension_scores"], ensure_ascii=False),
            ),
        )
        audit_id = int(cursor.lastrowid)
        conn.executemany(
            """INSERT INTO factor_results(audit_id, factor_id, name, dimension, status, score, evidence,
               source_url, manual_correction, recommendation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    audit_id,
                    factor["id"], factor["name"], factor["dimension"], factor["status"], factor["score"],
                    factor["evidence"], factor["source_url"], factor.get("manual_correction"), factor["recommendation"],
                )
                for factor in result["factors"]
            ],
        )
        conn.commit()
        return audit_id
    finally:
        conn.close()


def list_audits(limit: int = 50) -> list[dict]:
    initialize_database()
    conn = connection()
    try:
        rows = conn.execute(
            "SELECT id, created_at, url, pages_reviewed, pec_score, classification FROM audits ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def get_audit(audit_id: int) -> dict | None:
    initialize_database()
    conn = connection()
    try:
        audit = conn.execute("SELECT * FROM audits WHERE id = ?", (audit_id,)).fetchone()
        if not audit:
            return None
        factors = conn.execute("SELECT * FROM factor_results WHERE audit_id = ? ORDER BY factor_id", (audit_id,)).fetchall()
    finally:
        conn.close()
    result = dict(audit)
    result["warnings"] = json.loads(result.pop("warnings_json"))
    result["is_ecommerce"] = bool(result.get("is_ecommerce", 1))
    result["ecommerce_evidence"] = json.loads(result.pop("ecommerce_evidence_json", "[]") or "[]")
    result["confidence_reasons"] = json.loads(result.pop("confidence_reasons_json", "[]") or "[]")
    result["brand_assets"] = json.loads(result.pop("brand_assets_json", "{}") or "{}")
    ai_review_raw = result.pop("ai_review_json", None)
    result["ai_review"] = json.loads(ai_review_raw) if ai_review_raw else None
    result["dimension_scores"] = json.loads(result.pop("dimensions_json"))
    result["factors"] = [{**dict(row), "id": row["factor_id"]} for row in factors]
    return result


def save_feedback(rating: int, comment: str) -> None:
    initialize_database()
    conn = connection()
    try:
        conn.execute(
            "INSERT INTO feedback(created_at, rating, comment) VALUES (?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), rating, comment.strip()),
        )
        conn.commit()
    finally:
        conn.close()
