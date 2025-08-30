from app.services.session.get_session import get_session
from app.utils._prompts import (
    IS_MAIL_IMPORTANT_PROMPT,
    IS_RESPONSE_NEEDED_PROMPT,
    MAIL_RESPONSE_FORMAT_PROMPT,
    GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT,
)
from app.services.agents.email_agent.states import EmailState
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore


from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model


llm_model = init_chat_model(model="ollama:qwen2.5:0.5b")
namespace_for_memory = ("auth", "user")


def get_gmail_toolkit(
    state: EmailState, config: RunnableConfig, store: BaseStore
) -> Command:
    """
    Start the Gmail toolkit if it is not already running.
    This Node checks the current status of the Gmail toolkit and starts it if it is not running.
    """
    # getting username and thread_id for chat instance
    username = config["configurable"].get("username")
    thread_id = config["configurable"].get("thread_id", "test_thread")

    # get session data
    session = get_session(username=username, thread_id=thread_id)
    gmail_toolkit = session.gmail_toolkit
    data = gmail_toolkit.start()

    data_key = f"user-data:{username}:{thread_id}"
    unread_key = f"user-unread_mails:{username}:{thread_id}"
    # dummy mail data
    # gmail = {
    #     "id": "17f3a12b2e6c9a5e",
    #     "subject": "URGENT: Immediate Action Required on Your Internship Application",
    #     "sender": "hr@companycareers.com",
    #     "date": "2025-07-03T09:15:00Z",
    #     "body": "Dear Satyam,\n\nWe reviewed your internship application and require additional documents to process your candidacy. Please upload your updated resume and project portfolio by 6 PM IST today. Without these, your application will not be considered further.\n\nIf you've already submitted them, kindly ignore this message.\n\nRegards,\nHR Team\nCompanyCareers",
    #     "unread": True,
    #     "snippet": "We reviewed your internship application and require additional documents to process...",
    # }

    # fetching data from storage if available
    data_list = store.get(namespace_for_memory, key=data_key)
    unread_mails = store.get(namespace_for_memory, key=unread_key)

    # Extract values or set defaults
    data_list: list = data_list.value if data_list else []
    unread_mails: int = unread_mails.value if unread_mails else 0

    # Debug: printing the data fetched from storage
    # print(f"Data list from store: {data_list}")
    # print(f"Unread mails from store: {unread_mails}")

    # Update in-memory, then write back once
    data_list.append(data[0])
    unread_mails += 1

    store.put(namespace_for_memory, key=data_key, value=data_list)
    store.put(namespace_for_memory, key=unread_key, value=unread_mails)

    # return Command(update={"email": gmail_tool.get_mails()[0]})
    return Command(
        update={
            "email": data[0],
            "current_mail_id": data[0]["id"],
        }
    )


def analyze_importance(state: EmailState) -> Command:
    """
    Analyze the importance of the email using the AI toolkit.
    """

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


def is_response_needed(state: EmailState):
    """
    Check if a response is needed for the email using the AI toolkit.
    """
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
    email_data = state["email"]
    messages = [
        SystemMessage(content=MAIL_RESPONSE_FORMAT_PROMPT),
        HumanMessage(content=f"{email_data}"),
    ]
    response_format = llm_model.invoke(messages).content.lower().strip()
    return {"response_format": response_format}


def generate_draft_response(
    state: EmailState, store: BaseStore, config: RunnableConfig
):
    """
    Generate a draft response for the email using the AI toolkit.
    """
    email_data = state["email"]
    messages = [
        SystemMessage(content=GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT),
        HumanMessage(content=f"{email_data}"),
        HumanMessage(content=f"Mail style :{state['response_format']}"),
    ]
    draft_response = llm_model.invoke(messages).content.lower().strip()

    mail_id: str = state["current_mail_id"]

    # get username and thread_id
    username = config["configurable"].get("username")
    thread_id = config["configurable"].get("thread_id")

    # create key for data
    data_key = f"user-data:{username}:{thread_id}"

    data_list = store.get(namespace_for_memory, key=data_key)
    data_list: list = data_list.value if data_list else []

    # Update draft_response for the correct mail
    for mail in data_list:
        if mail["id"] == mail_id:
            mail["draft_response"] = draft_response
            break

    store.put(
        namespace=namespace_for_memory,
        key=data_key,
        value=data_list,
    )

    return {"response_email_draft": draft_response}
