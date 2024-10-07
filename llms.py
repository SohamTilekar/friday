from config import load_config
import google.generativeai as genai
from langchain_groq import ChatGroq
from langchain_core import rate_limiters

GROQ_API_KEY, GOOGLE_GEN_API_KEY = load_config()
genai.configure(api_key=GOOGLE_GEN_API_KEY)
llama_3_1_70b_versatile = ChatGroq(model="llama-3.1-70b-versatile", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=60 / 100, check_every_n_seconds=0.5))  # type: ignore
gemma_7b_it = ChatGroq(model="gemma-7b-it", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
gemma2_9b_it = ChatGroq(model="gemma2-9b-it", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
llama_3_1_8b_instant = ChatGroq(model="llama-3.1-8b-instant", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
llama_guard_3_8b = ChatGroq(model="llama-guard-3-8b", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
llama3_70b_8192 = ChatGroq(model="llama3-70b-8192", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
llama3_8b_8192 = ChatGroq(model="llama3-8b-8192", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
llama3_groq_70b_8192_tool_use_preview = ChatGroq(model="llama3-groq-70b-8192-tool-use-preview", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
emoji_selector = ChatGroq(model="llama3-groq-70b-8192-tool-use-preview", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0.5, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
llama3_groq_8b_8192_tool_use_preview = ChatGroq(model="llama3-groq-8b-8192-tool-use-preview", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore
mixtral_8x7b_32768 = ChatGroq(model="mixtral-8x7b-32768", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30 / 60, check_every_n_seconds=0.5))  # type: ignore

gen1_5_flash = genai.GenerativeModel("gemini-1.5-flash")
