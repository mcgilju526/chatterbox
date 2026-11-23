"""Asyncio chat server. Line-based protocol: one UTF-8 message per line."""
import asyncio
import logging
import os
import re
import signal

from .commands import HELP, SHRUG, eight_ball, roll

log = logging.getLogger("chatterbox")
MAX_LINE = 1024
NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{2,16}$")


class ChatServer:
    def __init__(self) -> None:
        self.clients: dict[asyncio.StreamWriter, str] = {}

    async def broadcast(self, text: str, skip: asyncio.StreamWriter | None = None) -> None:
        for w in list(self.clients):
            if w is not skip:
                await self.send(w, text)

    @staticmethod
    async def send(w: asyncio.StreamWriter, text: str) -> None:
        try:
            w.write((text + "\n").encode())
            await w.drain()
        except (ConnectionError, OSError):
            pass

    def name_taken(self, name: str) -> bool:
        return name.lower() in (n.lower() for n in self.clients.values())

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        try:
            name = await self.login(reader, writer)
            if name is None:
                return
            self.clients[writer] = name
            log.info("%s joined from %s (%d online)", name, peer, len(self.clients))
            await self.broadcast(f"* {name} joined the chat", skip=writer)
            await self.send(writer, f"* Welcome, {name}! Type /help. {len(self.clients)} online.")
            await self.chat_loop(reader, writer)
        except (ConnectionError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
            pass
        finally:
            name = self.clients.pop(writer, None)
            if name:
                log.info("%s left", name)
                await self.broadcast(f"* {name} left the chat")
            writer.close()

    async def login(self, reader, writer) -> str | None:
        await self.send(writer, "Welcome to Chatterbox! Pick a name (2-16 chars: letters, digits, _ -):")
        for _ in range(5):
            line = await reader.readline()
            if not line:
                return None
            name = line.decode(errors="replace").strip()
            if not NAME_RE.match(name):
                await self.send(writer, "Invalid name, try again:")
            elif self.name_taken(name):
                await self.send(writer, "That name is taken, try again:")
            else:
                return name
        return None

    async def chat_loop(self, reader, writer) -> None:
        while line := await reader.readline():
            text = line.decode(errors="replace").strip()
            if not text:
                continue
            name = self.clients[writer]
            if not text.startswith("/"):
                await self.broadcast(f"<{name}> {text}")
                continue
            cmd, _, arg = text[1:].partition(" ")
            arg = arg.strip()
            match cmd.lower():
                case "quit":
                    return
                case "help":
                    await self.send(writer, HELP)
                case "who":
                    await self.send(writer, "* Online: " + ", ".join(sorted(self.clients.values())))
                case "me" if arg:
                    await self.broadcast(f"* {name} {arg}")
                case "shrug":
                    await self.broadcast(f"<{name}> {SHRUG}")
                case "roll":
                    await self.broadcast(f"* {name} {roll(arg)}")
                case "8ball" if arg:
                    await self.broadcast(f"<{name}> asks: {arg}\n* 🎱 {eight_ball()}")
                case "nick":
                    if not NAME_RE.match(arg) or self.name_taken(arg):
                        await self.send(writer, "* Invalid or taken name.")
                    else:
                        self.clients[writer] = arg
                        await self.broadcast(f"* {name} is now known as {arg}")
                case _:
                    await self.send(writer, "* Unknown command. Try /help.")


async def serve(host: str, port: int) -> None:
    chat = ChatServer()
    server = await asyncio.start_server(chat.handle, host, port, limit=MAX_LINE)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):  # K8s sends SIGTERM on pod shutdown
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows
            pass
    log.info("Chatterbox listening on %s:%d", host, port)
    async with server:
        try:
            await stop.wait()
        except asyncio.CancelledError:
            pass
        await chat.broadcast("* Server is shutting down. Bye!")
    log.info("Shut down cleanly")


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(serve(os.getenv("HOST", "0.0.0.0"), int(os.getenv("PORT", "5000"))))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
