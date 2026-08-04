import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional


class MetadataStore:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.database = workspace / "knowledge.db"

    def initialize(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS records (
                    kind TEXT NOT NULL,
                    id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (kind, id)
                )
                """
            )

    def put(self, kind: str, record: Dict[str, Any]) -> Dict[str, Any]:
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO records(kind, id, payload) VALUES (?, ?, ?)",
                (kind, record["id"], json.dumps(record, ensure_ascii=False)),
            )
        return record

    def put_many(self, records: List[Any]) -> None:
        with self._connect() as connection:
            connection.executemany(
                "INSERT OR REPLACE INTO records(kind, id, payload) VALUES (?, ?, ?)",
                [
                    (kind, record["id"], json.dumps(record, ensure_ascii=False))
                    for kind, record in records
                ],
            )

    def get(self, kind: str, record_id: str) -> Dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload FROM records WHERE kind = ? AND id = ?",
                (kind, record_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown {kind}: {record_id}")
        return json.loads(row[0])

    def find_one(self, kind: str, field: str, value: str) -> Optional[Dict[str, Any]]:
        for record in self.list(kind):
            if record.get(field) == value:
                return record
        return None

    def list(self, kind: str) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM records WHERE kind = ? ORDER BY id", (kind,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        if not self.database.parent.exists():
            raise RuntimeError("Workspace is not initialized; run `knowledge init`")
        return sqlite3.connect(str(self.database))
