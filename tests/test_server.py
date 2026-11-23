import asyncio

import pytest

from chatterbox.commands import roll
from chatterbox.server import ChatServer


async def connect(port):
    r, w = await asyncio.open_connection("127.0.0.1", port)
    await r.readline()  # banner
    return r, w


async def say(w, text):
    w.write((text + "\n").encode())
    await w.drain()


@pytest.mark.asyncio
async def test_broadcast_and_duplicate_names():
    chat = ChatServer()
    server = await asyncio.start_server(chat.handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        ar, aw = await connect(port)
        await say(aw, "alice")
        await ar.readline()  # welcome
        br, bw = await connect(port)
        await say(bw, "alice")
        assert b"taken" in await br.readline()
        await say(bw, "bob")
        await br.readline()
        assert b"bob joined" in await ar.readline()
        await say(bw, "hi there")
        assert b"<bob> hi there" in await ar.readline()
        aw.close()
        bw.close()


def test_roll():
    assert "rolled 2d6" in roll("2d6")
    assert "Usage" in roll("banana")
