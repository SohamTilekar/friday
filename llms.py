from config import load_config
import asyncio
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun, HumanInputRun, tool as tool_decorator
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.retrievers import ArxivRetriever
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_groq import ChatGroq
from langchain_core import messages, rate_limiters
from tools import tools
GROQ_API_KEY = load_config()
llama_3_1_70b_versatile = ChatGroq(model="llama-3.1-70b-versatile", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=100/60, check_every_n_seconds=0.5))  # type: ignore
helper_llm = ChatGroq(model="llama3-8b-8192", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=0.5))  # type: ignore
ltm_manager_llm = ChatGroq(model="llama-3.1-8b-instant", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=0.5))  # type: ignore
gemma_7b_it = ChatGroq(model="gemma-7b-it", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
gemma2_9b_it = ChatGroq(model="gemma2-9b-it", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
llama_3_1_8b_instant = ChatGroq(model="llama-3.1-8b-instant", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
llama_guard_3_8b = ChatGroq( model="llama-guard-3-8b", stop_sequences=None, api_key=GROQ_API_KEY, temperature=0, rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
llama3_70b_8192 = ChatGroq(model="llama3-70b-8192",stop_sequences=None,api_key=GROQ_API_KEY,temperature=0,rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
llama3_8b_8192 = ChatGroq(model="llama3-8b-8192",stop_sequences=None,api_key=GROQ_API_KEY,temperature=0,rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
llama3_groq_70b_8192_tool_use_preview = ChatGroq(model="llama3-groq-70b-8192-tool-use-preview",stop_sequences=None,api_key=GROQ_API_KEY,temperature=0,rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
llama3_groq_8b_8192_tool_use_preview = ChatGroq(model="llama3-groq-8b-8192-tool-use-preview",stop_sequences=None,api_key=GROQ_API_KEY,temperature=0,rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore
mixtral_8x7b_32768 = ChatGroq(model="mixtral-8x7b-32768",stop_sequences=None,api_key=GROQ_API_KEY,temperature=0,rate_limiter=rate_limiters.InMemoryRateLimiter(requests_per_second=30/60, check_every_n_seconds=0.5)) # type: ignore

# tools
ddg_runner = DuckDuckGoSearchRun()
@tool_decorator
def search_ddg(query: str) -> list[str]:
    """
    A wrapper around DuckDuckGo Search.
    Useful for when you need to answer questions about current events.
    """
    async def fetch_results() -> list[str]:
        coroutines = [ddg_runner.ainvoke(query) for _ in range(3)]
        results = await asyncio.gather(*coroutines)
        return [str(helper_llm.invoke(f"write the very short summarize & combine of the DuckDuckGo Search Result's Without Loosing Detail, Result:\n\n\n\n{result}").content) for result in results]
    return asyncio.run(fetch_results())
tools.append(search_ddg)

wikipedia_runner = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(doc_content_chars_max=8000)) # type: ignore
@tool_decorator
def search_wikipedia(query: str) -> str:
    """
    A wrapper around Wikipedia.
    Useful for when you need to answer general questions about people, places, companies, facts, historical events, or other subjects.
    Input should be a search query.
    """
    return str(helper_llm.invoke(f"write the very short summarize of the Wikipedia Search Result's Without Loosing Detail, Result:{str(wikipedia_runner.invoke(query))}").content)
tools.append(search_wikipedia)

arxiv_retriever = ArxivRetriever(
    load_max_docs=4,
    get_full_documents=True,
) # type: ignore

@tool_decorator
def search_arxiv(query: str):
    """
    A wrapper around ArXiv.
    Useful for when you need to answer questions about scientific papers.
    Input should be a search query.
    """
    doc = arxiv_retriever.run(query)
    return str(helper_llm.invoke(f"write the detail structured notes Include the Metadata of the Arxiv Search Result's, Result:\n{doc}").content)
tools.append(search_arxiv)

pubmed_runner = PubmedQueryRun()

@tool_decorator
def search_pubmed(query: str) -> str:
    """
    A wrapper around PubMed.
    Useful for when you need to answer questions about medicine, health, and biomedical topics from biomedical literature, MEDLINE, life science journals, and online books.
    Input should be a search query.
    """
    return str(helper_llm.invoke(f"write the very short summarize of the PubMed Search Result's Without Loosing Detail, Result:{str(pubmed_runner.invoke(query))}").content)
tools.append(search_pubmed)

def get_input() -> str:
    print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
    print("```")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "q":
            break
        contents.append(line)
    print("```")
    return "\n".join(contents)

human_runner = HumanInputRun(input_func=get_input)
@tool_decorator
def human_input(query: str) -> str:
    """
    You can ask a human for guidance when you think you got stuck or you are not sure what to do next. The input should be a question for the human.
    """
    return str(human_runner.invoke(query))
tools.append(human_input)
