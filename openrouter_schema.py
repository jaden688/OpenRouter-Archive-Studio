"""Create the minimum local OpenRouter archive schema on first launch."""
import sqlite3
from pathlib import Path


def initialize_database(database: str | Path) -> None:
    """Create an empty, usable archive without overwriting an existing database."""
    path = Path(database)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id TEXT PRIMARY KEY,
                created_at_utc TEXT,
                created_at_local TEXT,
                date_utc TEXT,
                date_local TEXT,
                model TEXT,
                provider_name TEXT,
                api_type TEXT,
                tokens_prompt INTEGER,
                tokens_completion INTEGER,
                native_tokens_prompt INTEGER,
                native_tokens_completion INTEGER,
                native_tokens_reasoning INTEGER,
                native_tokens_cached INTEGER,
                total_cost REAL,
                usage REAL,
                finish_reason TEXT,
                native_finish_reason TEXT,
                generation_time_ms INTEGER,
                latency_ms INTEGER,
                streamed INTEGER,
                cancelled INTEGER,
                is_byok INTEGER,
                session_id TEXT,
                request_id TEXT,
                upstream_id TEXT,
                metadata_status INTEGER,
                content_status INTEGER,
                prompt_messages_json TEXT,
                prompt_text TEXT,
                completion_text TEXT,
                reasoning_text TEXT,
                error_json TEXT,
                raw_metadata_json TEXT,
                raw_content_json TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS english_translations (
                generation_id TEXT,
                field_name TEXT,
                translated_text TEXT,
                translated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (generation_id, field_name)
            )
        """)
        conn.commit()
    finally:
        conn.close()
