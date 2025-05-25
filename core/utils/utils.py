from google import genai
from dotenv import load_dotenv
import os
from google.genai.types import GenerateContentConfig
from typing import List

load_dotenv()


def get_google_gemini_key():
    """Get the Google Gemini API key from environment variables."""
    return os.environ.get("GOOGLE_API_KEY")


def get_groq_key():
    """Get the Groq API key from environment variables."""
    return os.environ.get("GROQ_API_KEY")


def get_gemini_client():
    key = get_google_gemini_key()
    client = genai.Client(api_key=key)
    return client


def get_single_call_gemini_response(
    client,
    system_instruction: str = None,
    model_name="gemini-1.5-flash",
    contents: List[str] = ["what can you do?"],
):
    response = client.models.generate_content(
        model=model_name,
        config=GenerateContentConfig(
            system_instruction=system_instruction,
        ),
        contents=contents,
    )
    return response


def get_chat_gemini_response(
    client, model_name="gemini-2.0-flash", question="what can you do?"
):
    chat = client.chats.create(model=model_name)
    response = chat.send_message(message=question)
    return response


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
