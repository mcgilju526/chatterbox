"""Fun slash-command logic, kept free of networking so it is easy to test."""
import random

SHRUG = r"¯\_(ツ)_/¯"
EIGHT_BALL = [
    "It is certain.", "Without a doubt.", "Signs point to yes.",
    "Ask again later.", "Cannot predict now.", "Don't count on it.",
    "My sources say no.", "Very doubtful.",
]
HELP = """\
Commands:
  /nick <name>   change your name
  /who           list who is online
  /me <action>   emote
  /roll [NdM]    roll dice (default 1d6)
  /8ball <q>     consult the oracle
  /shrug         ¯\\_(ツ)_/¯
  /help          this message
  /quit          leave"""


def roll(spec: str = "") -> str:
    spec = (spec or "1d6").lower()
    try:
        n, m = (int(x) for x in spec.split("d"))
    except ValueError:
        return "Usage: /roll NdM  (e.g. /roll 2d20)"
    if not (1 <= n <= 20 and 2 <= m <= 1000):
        return "Keep it to 1-20 dice with 2-1000 sides."
    rolls = [random.randint(1, m) for _ in range(n)]
    return f"rolled {spec}: {rolls} = {sum(rolls)}"


def eight_ball() -> str:
    return random.choice(EIGHT_BALL)
