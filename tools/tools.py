import os
from langchain_community.tools import (
    DuckDuckGoSearchRun,
    WikipediaQueryRun,
    tool as tool_decorator,
)
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.retrievers import ArxivRetriever
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_core import messages
import asyncio
import threading
import datetime
from difflib import get_close_matches
from groq import Groq
import google.generativeai as genai
from langchain_core.tools import tool as tool_decorator
from typing import Callable
import random as rand
from langchain.agents import load_tools
import time
from config import __ai_dir__
import PIL.Image as PILI
from tools.gmail import *
from tools.reminder import run_reminders, create_reminder, cancel_reminder
import llms
from pathlib import Path
from global_shares import global_shares
from config import load_config

groq_api, _ = load_config()


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
    "Heart": "1f970",
    "Heart-eyes": "1f60d",
    "Star-struck": "1f929",
    "Partying": "1f973",
    "Melting": "1fae0",
    "Upside-down": "1f643",
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
    "Zany": "1f92a",
    "Woozy": "1f974",
    "Pensive": "1f614",
    "Pleading": "1f97a",
    "Grimacing": "1f62c",
    "Expressionless": "1f611",
    "Neutral": "1f610",
    "Zipper": "1f910",
    "Salute": "1fae1",
    "Thinking": "1f914",
    "Shushing": "1f92b",
    "Hand-over-mouth": "1fae2",
    "Smiling-eyes-with-hand-over-mouth": "1f92d",
    "Yawn": "1f971",
    "Hug": "1f917",
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
    "Dizzy": "1f635_200d_1f4ab",
    "Shaking": "1fae8",
    "Cold": "1f976",
    "Hot": "1f975",
    "Sick": "1f922",
    "Vomit": "1f92e",
    "Sleep": "1f634",
    "Sleepy": "1f62a",
    "Mask": "1f637",
    "Halo": "1f607",
    "Clown": "1f921",
    "Nerd": "u1f913",
    "Money": "1f911",
}


@tool_decorator
def emojify(face_type: str) -> tuple[None | str, str]:
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
            - Heart
            - Heart-eyes
            - Star-struck
            - Partying
            - Melting
            - Upside-down
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
            - Zany
            - Woozy
            - Pensive
            - Pleading
            - Grimacing
            - Expressionless
            - Neutral
            - Zipper
            - Salute
            - Thinking
            - Shushing
            - Hand-over-mouth
            - Smiling-eyes-with-hand-over-mouth
            - Yawn
            - Hug
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
            - Dizzy:
            - Shaking
            - Cold
            - Hot
            - Sick
            - Vomit
            - Sleep
            - Sleepy
            - Mask
            - Halo
            - Clown
            - Nerd
            - Money
    """
    # Find the closest match for the face_type
    closest_match = get_close_matches(face_type, emoji_map.keys(), n=1)

    if closest_match:
        return emoji_map.get(closest_match[0]), closest_match[0]
    else:
        return None, face_type


from pathlib import Path
from itertools import islice


space = "    "
branch = "│   "
tee = "├── "
last = "└── "


def dir_tree(
    dir_path: Path,
    level: int = -1,
    limit_to_directories: bool = False,
    length_limit: int = 1000,
):
    """Given a directory Path object print a visual tree structure"""
    dir_path = Path(dir_path)  # accept string coerceable to Path
    files = 0
    directories = 0

    def inner(dir_path: Path, prefix: str = "", level=-1):
        nonlocal files, directories
        if not level:
            return  # 0, stop iterating
        if limit_to_directories:
            contents = [d for d in dir_path.iterdir() if d.is_dir()]
        else:
            contents = list(dir_path.iterdir())
        pointers = [tee] * (len(contents) - 1) + [last]
        for pointer, path in zip(pointers, contents):
            if path.is_dir():
                yield prefix + pointer + path.name
                directories += 1
                extension = branch if pointer == tee else space
                yield from inner(path, prefix=prefix + extension, level=level - 1)
            elif not limit_to_directories:
                yield prefix + pointer + path.name
                files += 1

    result = [dir_path.name]
    iterator = inner(dir_path, level=level)
    for line in islice(iterator, length_limit):
        result.append(line)
    if next(iterator, None):
        result.append(f"... length_limit, {length_limit}, reached, counted:")
    result.append(
        f"\n{directories} directories" + (f", {files} files" if files else "")
    )
    return "\n".join(result)


client = Groq(api_key=groq_api)


@tool_decorator
def query_image(query: str, path: str | list[str]):
    """\
    Use this tool to query an image from the web and save it to the specified path.
    Args:
        query: query about the image e.g. 'what is in the image?'
        path: path of the image e.g. 'user_upload/image_id.png' pass as a string for querying only 1 image for querying multiple images pass the list of string.
    Returns:
        The answer to the query about the image.
    """
    if isinstance(path, str):
        img_file = PILI.open(__ai_dir__ / Path(path.split("/", 1)[1]))
        return llms.gen1_5_flash.generate_content([img_file, query]).text
    else:
        paths = path
        img_files = []
        for path in paths:
            img_files.append(PILI.open(__ai_dir__ / Path(path.split("/", 1)[1])))
        return llms.gen1_5_flash.generate_content([*img_files, query]).text


@tool_decorator
def query_audio(query: str, path: str | list[str]):
    """\
    Use this tool to query an audio from the web and save it to the specified path.
    Args:
        query: query about the audio e.g. 'what is in the audio?', 'give me the emotion which is in this audio'
        path: path of the audio e.g. 'user_upload/audio_id.png' pass as a string for querying only 1 audio for querying multiple audios pass the list of string.
    Returns:
        The answer to the query about the audio.
    """
    if isinstance(path, str):
        audio_file = {"mime_type": "audio/mp3", "data": Path(path).read_bytes()}
        return llms.gen1_5_flash.generate_content([audio_file, query]).text
    else:
        paths = path
        audio_files = []
        for path in paths:
            audio_files.append(
                {"mime_type": "audio/mp3", "data": Path(path).read_bytes()}
            )
        return llms.gen1_5_flash.generate_content([*audio_files, query]).text


@tool_decorator
def query_video(query: str, path: str):
    """\
    Use this tool to query a video from the web and get the generated response.
    
    Args:
        query: query about the video e.g. 'summarize the video', 'transcribe the audio'.
        path: path of the video file e.g. 'user_upload/video_id.mp4'.
    
    Returns:
        The generated content based on the video and query.
    """
    # Upload the video file
    video_file = genai.upload_file(path=__ai_dir__ / Path(path.split("/", 1)[1]))

    while video_file.state.name == "PROCESSING":
        time.sleep(0.5)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed")

    # Generate content with the video and the prompt
    response = llms.gen1_5_flash.generate_content(
        [video_file, query], request_options={"timeout": 600}
    )

    # Return the response text
    return response.text


# DuckDuckGo Search
ddg_runner = DuckDuckGoSearchRun()


@tool_decorator
def search_ddg(query: str) -> str:
    """
    A wrapper around DuckDuckGo Search.
    Useful for when you need to answer questions about current events.
    """

    async def fetch_results() -> str:
        coroutines = [ddg_runner.ainvoke(query) for _ in range(3)]
        results = await asyncio.gather(*coroutines)
        return str(
            llms.llama_3_1_8b_instant.invoke(
                [
                    messages.HumanMessage(
                        "Combine the Below Search Results into 1 in short"
                        + str([result for result in results])
                    )
                ]
            ).content
        )

    return asyncio.run(fetch_results())


wikipedia_runner = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(doc_content_chars_max=8000))  # type: ignore


@tool_decorator
def search_wikipedia(query: str) -> str:
    """
    A wrapper around Wikipedia.
    Useful for when you need to answer general questions about people, places, companies, facts, historical events, or other subjects.
    Input should be a search query.
    """
    return str(
        llms.llama_3_1_8b_instant.invoke(
            f"write the very short summarize of the Wikipedia Search Result's Without Loosing Detail, Result:{str(wikipedia_runner.invoke(query))}"
        ).content
    )


arxiv_retriever = ArxivRetriever(
    load_max_docs=4,
    get_full_documents=True,
)  # type: ignore


@tool_decorator
def search_arxiv(query: str):
    """
    A wrapper around ArXiv.
    Useful for when you need to answer questions about scientific papers.
    Input should be a search query.
    """
    doc = arxiv_retriever.run(query)
    return str(
        llms.llama_3_1_8b_instant.invoke(
            f"write the detail structured notes Include the Metadata of the Arxiv Search Result's, Result:\n{doc}"
        ).content
    )


pubmed_runner = PubmedQueryRun()


@tool_decorator
def search_pubmed(query: str) -> str:
    """
    A wrapper around PubMed.
    Useful for when you need to answer questions about medicine, health, and biomedical topics from biomedical literature, MEDLINE, life science journals, and online books.
    Input should be a search query.
    """
    return str(
        llms.llama_3_1_8b_instant.invoke(
            f"write the very short summarize of the PubMed Search Result's Without Loosing Detail, Result:{str(pubmed_runner.invoke(query))}"
        ).content
    )


@tool_decorator
def gui_updater(what_to_update: str):
    """\
    Use this tool to update the GUI, Pass whatever you want to update the GUI with.
    Args:
        what_to_update: The content you want to update the GUI with.
    """
    global_shares["call_routine"]("ai_called_by_user", what_to_update=what_to_update)  # type: ignore


if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    reminder_thread = threading.Thread(target=run_reminders, daemon=True)
    reminder_thread.start()

tools: list[Callable] = [
    search_ddg,
    search_wikipedia,
    search_arxiv,
    search_pubmed,
    current_time,
    current_date,
    randint,
    random,
    send_email,
    search_emails,
    draft_email,
    mark_spam,
    reply_email,
    mark_read,
    star_email,
    unstar_email,
    permanently_delete_email,
    trash_email,
    query_image,
    query_video,
    query_audio,
    create_reminder,
    cancel_reminder,
    gui_updater,
]
tools.extend(load_tools(["stackexchange"]))


__all__ = ["tools"]
