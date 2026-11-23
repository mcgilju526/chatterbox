"""Terminal chat client with colored names. Usage: python -m chatterbox.client [host] [port]"""
import asyncio
import hashlib
import os
import re
import sys

RESET = "\033[0m"
PALETTE = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96]
MSG_RE = re.compile(r"^<([^>]+)>")


def colorize(line: str) -> str:
    if line.startswith("*"):
        return f"\033[2m{line}{RESET}"  # dim system/emote lines
    m = MSG_RE.match(line)
    if m:
        color = PALETTE[int(hashlib.md5(m.group(1).encode()).hexdigest(), 16) % len(PALETTE)]
        return f"\033[{color}m{m.group(0)}{RESET}{line[m.end():]}"
    return line


async def run(host: str, port: int) -> None:
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except OSError as e:
        print(f"Could not connect to {host}:{port}: {e}")
        return

    async def receive() -> None:
        while line := await reader.readline():
            print("\r\033[K" + colorize(line.decode(errors="replace").rstrip()))
        print("\nDisconnected.")

    async def send() -> None:
        loop = asyncio.get_running_loop()
        while True:
            text = await loop.run_in_executor(None, sys.stdin.readline)
            if not text:
                break
            writer.write(text.encode())
            await writer.drain()
            if text.strip() == "/quit":
                break

    tasks = [asyncio.create_task(receive()), asyncio.create_task(send())]
    await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    writer.close()
    for t in tasks:
        t.cancel()


def main() -> None:
    os.system("")  # enables ANSI colors in Windows terminals
    host = sys.argv[1] if len(sys.argv) > 1 else os.getenv("CHAT_HOST", "127.0.0.1")
    port = int(sys.argv[2]) if len(sys.argv) > 2 else int(os.getenv("CHAT_PORT", "5000"))
    try:
        asyncio.run(run(host, port))
    except KeyboardInterrupt:
        pass
    os._exit(0)  # the stdin reader thread can't be cancelled


if __name__ == "__main__":
    main()
