import os
from pathlib import Path


def load_config() -> tuple[str, str]:
    GROQ_API_KEY = ""
    GOOGLE_GEN_API_KEY = ""
    with open("./.env", "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            if key == "GROQ_API_KEY":
                GROQ_API_KEY = value
            elif key == "GOOGLE_GEN_API_KEY":
                GOOGLE_GEN_API_KEY = value
            else:
                raise ValueError(
                    "Invalid key in .env file. Please check the file and try again."
                )

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found in .env file. Please add the key and try again."
        )
    if not GOOGLE_GEN_API_KEY:
        raise ValueError(
            "GOOGLE_GEN_API_KEY not found in .env file. Please add the key and try again."
        )
    return GROQ_API_KEY, GOOGLE_GEN_API_KEY  # type: ignore


__ai_dir__ = Path(os.path.split(__file__)[0], "AI_DIR/")
