"""Minimal local agent foundation: offline-first, no cloud/HA dependency."""
import asyncio
import json
import logging
import os
import signal
import sqlite3
from pathlib import Path

log = logging.getLogger("homecore.agent")


def init_database(path: str) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        db.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', '1')")


async def handle_health(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request = await asyncio.wait_for(reader.readline(), timeout=3)
        path = request.decode("ascii", errors="replace").split(" ")[1] if b" " in request else ""
        healthy = path == "/health"
        payload = json.dumps({"status": "ok", "service": "homecore-agent"} if healthy else {"error": "not_found"}).encode()
        writer.write(
            (b"HTTP/1.1 200 OK\r\n" if healthy else b"HTTP/1.1 404 Not Found\r\n")
            + b"Content-Type: application/json\r\nCache-Control: no-store\r\n"
            + f"Content-Length: {len(payload)}\r\nConnection: close\r\n\r\n".encode()
            + payload
        )
        await writer.drain()
    except (asyncio.TimeoutError, ConnectionError, IndexError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()


async def run() -> None:
    logging.basicConfig(level=os.getenv("HOMECORE_LOG_LEVEL", "INFO").upper())
    db_path = os.getenv("HOMECORE_AGENT_DB", "./data/agent.sqlite3")
    host = os.getenv("HOMECORE_AGENT_HOST", "127.0.0.1")
    port = int(os.getenv("HOMECORE_AGENT_PORT", "8081"))
    init_database(db_path)
    server = await asyncio.start_server(handle_health, host, port)
    log.info("HomeCore Agent started: host=%s port=%d", host, port)
    async with server:
        await server.serve_forever()
