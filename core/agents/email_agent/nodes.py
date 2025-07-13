import random
from core.utils.prompts import (
    MAIL_SUMMARY_PROMPT,
    IS_MAIL_IMPORTANT_PROMPT,
    IS_RESPONSE_NEEDED_PROMPT,
    MAIL_RESPONSE_FORMAT_PROMPT,
    GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT,
)
from core.agents.email_agent.states import EmailState
from langgraph.graph import END
from langgraph.types import interrupt, Command
from core.gmail import GmailToolKit

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model
from langgraph.store.redis import RedisStore


llm_model = init_chat_model(model="ollama:qwen2.5:0.5b")
gmail_tool = GmailToolKit(run_as_thread=False, save_json=False)
with RedisStore.from_conn_string("redis://localhost:6379") as store:
    store.setup()


def get_gmail_toolkit(state: EmailState) -> Command:
    """
    Start the Gmail toolkit if it is not already running.
    This Node checks the current status of the Gmail toolkit and starts it if it is not running.
    """
    # data = gmail_tool.start()

    # time.sleep(5)
    gmail = {
        "id": "17f3a12b2e6c9a5e",
        "subject": "URGENT: Immediate Action Required on Your Internship Application",
        "sender": "hr@companycareers.com",
        "date": "2025-07-03T09:15:00Z",
        "body": "Dear Satyam,\n\nWe reviewed your internship application and require additional documents to process your candidacy. Please upload your updated resume and project portfolio by 6 PM IST today. Without these, your application will not be considered further.\n\nIf you've already submitted them, kindly ignore this message.\n\nRegards,\nHR Team\nCompanyCareers",
        "unread": True,
        "snippet": "We reviewed your internship application and require additional documents to process...",
    }

    user_id = state.get("user_id", "1")
    thread_id = state.get("thread_id", "test")

    namespace_for_memory = (user_id, thread_id)

    store.put(namespace_for_memory, "mail", gmail)

    # return Command(update={"email": gmail_tool.get_mails()[0]})
    return Command(
        update={"email": gmail, "namespace_for_memory": namespace_for_memory}
    )


def analyze_importance(state: EmailState) -> Command:
    """
    Analyze the importance of the email using the AI toolkit.
    """
    if not state["email"]:
        return

    email_data = state["email"]

    messages = [
        SystemMessage(content=IS_MAIL_IMPORTANT_PROMPT),
        HumanMessage(content=f"{email_data}"),
    ]
    important_response = llm_model.invoke(messages).content.lower().strip()

    return Command(
        update={
            "is_mail_important": important_response == "yes",
        }
    )


def summarize_email(state: EmailState):
    """
    Summarize the email using the AI toolkit.
    """
    if not state["email"]:
        return
    if state["is_mail_important"]:
        email_data = state["email"]
        messages = [
            SystemMessage(content=MAIL_SUMMARY_PROMPT),
            HumanMessage(content=f"{email_data}"),
        ]
        summary = llm_model.invoke(messages).content.lower().strip()
        store.put(state["namespace_for_memory"], "mail_summary", summary)

        return {"email_summary": summary}


def is_response_needed(state: EmailState):
    """
    Check if a response is needed for the email using the AI toolkit.
    """
    if not state["email"]:
        return
    if state["is_mail_important"]:
        email_data = state["email"]
        messages = [
            SystemMessage(content=IS_RESPONSE_NEEDED_PROMPT),
            HumanMessage(content=f"{email_data}"),
        ]
        response_needed = llm_model.invoke(messages).content.lower().strip()

        return {"is_response_needed": response_needed == "yes"}


def mail_response_format(state: EmailState):
    """
    Get the response format for the email using the AI toolkit.
    """
    if not state["email"]:
        return
    if state["is_mail_important"] and state["is_response_needed"]:
        email_data = state["email"]
        messages = [
            SystemMessage(content=MAIL_RESPONSE_FORMAT_PROMPT),
            HumanMessage(content=f"{email_data}"),
        ]
        response_format = llm_model.invoke(messages).content.lower().strip()
        return {"response_format": response_format}


def generate_draft_response(state: EmailState):
    """
    Generate a draft response for the email using the AI toolkit.
    """
    if not state["email"]:
        return
    if state["is_mail_important"] and state["is_response_needed"]:
        email_data = state["email"]
        messages = [
            SystemMessage(content=GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT),
            HumanMessage(content=f"{email_data}"),
            HumanMessage(content=f"Mail style :{state['response_format']}"),
        ]
        draft_response = llm_model.invoke(messages).content.lower().strip()

        store.put(state["namespace_for_memory"], "draft_response", draft_response)

        return {"response_email_draft": draft_response}
