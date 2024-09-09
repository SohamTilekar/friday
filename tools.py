import datetime
from langchain_core.tools import tool as tool_decorator
from typing import Any, Callable
import random as rand
from langchain.agents import load_tools


@tool_decorator
def current_time():
    """\
    Use this tool to get the current time in 24-hour clock format: HH:MM
    Args:
        None
    """
    return "current time is " + datetime.datetime.now().strftime("%H:%M")

@tool_decorator
def current_date():
    """\
    Use this tool to get the current date in the format: DD/Month/YYYY
    Args:
        None
    """
    return "current date is " + datetime.datetime.now().strftime("%d/%B/%Y")

@tool_decorator
def randint(a: int, b: int):
    """\
    Use this tool to get a random integer between a and b (inclusive).
    Args:
        a: The lower bound of the range.
        b: The upper bound of the range.
    """
    return "random number generated is " + str(rand.randint(a, b))

@tool_decorator
def random():
    """\
    Use this tool to get a random float between 0 and 1.
    Args:
        None
    """
    return "random number between 0 & 1 is " + f"{rand.random():.5f}"

emoji_map = {
  "Smile": "1f600",
  "Smile-with-big-eyes": "1f603",
  "Grin": "1f604",
  "Grinning": "1f601",
  "Laughing": "1f606",
  "Grin-sweat": "1f605",
  "Joy": "1f602",
  "Rofi": "1f923",
  "Loudly-crying": "1f62d",
  "Wink": "1f609",
  "Heart-face": "1f970",
  "Heart-eyes": "1f60d",
  "Star-struck": "1f929",
  "Partying-face": "1f973",
  "Melting": "1fae0",
  "Upside-down-face": "1f643",
  "Slightly-smile": "1f642",
  "Happy-cry": "1f972",
  "Holding-back-tears": "1f979",
  "Blush": "1f60a",
  "Warm-smile": "263a_fe0f",
  "Relieved": "1f60c",
  "Smirk": "1f60f",
  "Drool": "1f924",
  "Yum": "1f60b",
  "Stuck-out-tongue": "1f61b",
  "Squinting-tongue": "1f61d",
  "Winky-tongue": "1f61c",
  "Zany-face": "1f92a",
  "Woozy": "1f974",
  "Pensive": "1f614",
  "Pleading": "1f97a",
  "Grimacing": "1f62c",
  "Expressionless": "1f611",
  "Neutral-face": "1f610",
  "Zipper-face": "1f910",
  "Salute": "1fae1",
  "Thinking-face": "1f914",
  "Shushing-face": "1f92b",
  "Hand-over-mouth": "1fae2",
  "Smiling-eyes-with-hand-over-mouth": "1f92d",
  "Yawn": "1f971",
  "Hug-face": "1f917",
  "Peeking": "1fae3",
  "Screaming": "1f631",
  "Raised-eyebrow": "1f928",
  "Monocle": "1f9d0",
  "Unamused": "1f612",
  "Exhale": "1f62e_200d_1f4a8",
  "Triumph": "1f624",
  "Angry": "1f620",
  "Rage": "1f621",
  "Cursing": "u1f92c",
  "Sad": "1f61e",
  "Sweat": "1f613",
  "Worried": "1f61f",
  "Concerned": "1f625",
  "Cry": "1f622",
  "Big-frown": "2639_fe0f",
  "Frown": "1f641",
  "Anxious-with-sweat": "1f630",
  "Scared": "1f628",
  "Anguished": "1f627",
  "Surprised": "1f62f",
  "Astonished": "1f632",
  "Flushed": "1f633",
  "Mind-blown": "1f92f",
  "X-eyes": "1f635",
  "Dizzy-face": "1f635_200d_1f4ab",
  "Shaking-face": "1fae8",
  "Cold-face": "1f976",
  "Hot-face": "1f975",
  "Sick": "1f922",
  "Vomit": "1f92e",
  "Sleep": "1f634",
  "Sleepy": "1f62a",
  "Mask": "1f637",
  "Halo": "1f607",
  "Clown": "1f921",
  "Nerd-face": "u1f913",
  "Money-face": "1f911"
}

@tool_decorator
def emojify(face_type: str) -> None:
    """\
    Use this tool to get an emoji based on the face type.
    Args:
        face_type: The type of face you want to generate an emoji for.
            Possible face types:
            - Smile
            - Smile-with-big-eyes
            - Grin
            - Grinning
            - Laughing
            - Grin-sweat
            - Joy
            - Rofi
            - Loudly-crying
            - Wink
            - Heart-face
            - Heart-eyes
            - Star-struck
            - Partying-face
            - Melting
            - Upside-down-face
            - Slightly-smile
            - Happy-cry
            - Holding-back-tears
            - Blush
            - Warm-smile
            - Relieved
            - Smirk
            - Drool
            - Yum
            - Stuck-out-tongue
            - Squinting-tongue
            - Winky-tongue
            - Zany-face
            - Woozy
            - Pensive
            - Pleading
            - Grimacing
            - Expressionless
            - Neutral-face
            - Zipper-face
            - Salute
            - Thinking-face
            - Shushing-face
            - Hand-over-mouth
            - Smiling-eyes-with-hand-over-mouth
            - Yawn
            - Hug-face
            - Peeking
            - Screaming
            - Raised-eyebrow
            - Monocle
            - Unamused
            - Exhale:
            - Triumph
            - Angry
            - Rage
            - Cursing
            - Sad
            - Sweat
            - Worried
            - Concerned
            - Cry
            - Big-frown
            - Frown
            - Anxious-with-sweat
            - Scared
            - Anguished
            - Surprised
            - Astonished
            - Flushed
            - Mind-blown
            - X-eyes
            - Dizzy-face:
            - Shaking-face
            - Cold-face
            - Hot-face
            - Sick
            - Vomit
            - Sleep
            - Sleepy
            - Mask
            - Halo
            - Clown
            - Nerd-face
            - Money-face
    """
    print(face_type)
    print(emoji_map.get(face_type))
    return emoji_map.get(face_type), face_type # type: ignore

tools: list[Callable] = [
    current_time,
    current_date,
    randint,
    random,
]
tools.extend(load_tools(["stackexchange"]))
