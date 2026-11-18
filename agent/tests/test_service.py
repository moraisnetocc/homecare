import asyncio
import sqlite3
from homecore_agent.service import handle_health, init_database


def test_init_database_is_idempotent(tmp_path):
    path = str(tmp_path / "data" / "agent.sqlite3")
    init_database(path)
    init_database(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone() == ("1",)


def test_health_endpoint():
    async def check():
        server = await asyncio.start_server(handle_health, "127.0.0.1", 0)
        async with server:
            port = server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
            await writer.drain()
            data = await reader.read()
            writer.close()
            await writer.wait_closed()
            assert b"200 OK" in data
            assert b'"status": "ok"' in data
    asyncio.run(check())
