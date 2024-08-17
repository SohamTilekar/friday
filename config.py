def load_config():
    GROQ_API_KEY = ""
    with open("./.env", "r") as f:
        for line in f:
            key, value = line.strip().split("=")
            if key == "GROQ_API_KEY":
                GROQ_API_KEY = value
            else:
                raise ValueError("Invalid key in .env file. Please check the file and try again.")
    
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in .env file. Please add the key and try again.")
    
    return GROQ_API_KEY
