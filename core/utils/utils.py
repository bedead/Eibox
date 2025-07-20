from dotenv import load_dotenv
import os


load_dotenv()


def get_google_gemini_key() -> str | None:
    """Get the Google Gemini API key from environment variables."""
    return os.environ.get("GOOGLE_API_KEY")


def get_redis_store_host() -> str | None:
    """Get the redis store host endpoint with port."""
    return os.environ.get("REDIS_STORE_HOST")


def get_groq_key():
    """Get the Groq API key from environment variables."""
    return os.environ.get("GROQ_API_KEY")


from langchain_core.runnables.graph import MermaidDrawMethod


def display_graph(
    compiled_graph, use_mermaid: bool = False, use_api: bool = False, max_retry: int = 1
):
    """
    Display the image of the compiled graph.
    """
    if use_mermaid:
        compiled_graph.get_graph().draw_mermaid_png(
            output_file_path="graph.png",
            draw_method=(
                MermaidDrawMethod.PYPPETEER if not use_api else MermaidDrawMethod.API
            ),
            max_retries=max_retry,
        )
    else:
        compiled_graph.get_graph().draw_png()
