import datetime
from langchain_core.tools import tool as tool_decorator
from typing import Any
import random as rand

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

@tool_decorator
def remember_knowledge(memory: str):
    """\
    Use this tool to remember New knowledge in long term memory.
    Args:
        memory: The knowledge to remember.
    """
    long_term_memory.add(memory)
    return f"Remembered: {memory}"

@tool_decorator
def forget_knowledge(memory: str):
    """\
    Use this tool to forget selected knowledge in long term memory.
    Args:
        memory: The knowledge to forget
    """
    long_term_memory.remove(memory)
    return f"Forgot: {memory}"

@tool_decorator
def update_knowledge_memory(old_memory: str, new_memory: str):
    """\
    Use this tool to update selected knowledge in long term memory.
    Args:
        old_memory: The knowledge to update.
        new_memory: The new knowledge.
    """
    long_term_memory.remove(old_memory)
    long_term_memory.add(new_memory)
    return f"Updated: {old_memory} -> {new_memory}"

tools: list[Any] = [
    current_time,
    current_date,
    randint,
    random,
    remember_knowledge,
    forget_knowledge,
    update_knowledge_memory
]

long_term_memory: set[str] = set()
