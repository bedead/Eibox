from datetime import datetime
from typing import Any, Dict


from langgraph.types import Command
from langgraph.graph import END
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model


from app.utils._text_helper import _to_text
from app.core.logging import logger
from app.db.repos.gmail.mails.add_draft_to_mail_object import add_draft_to_mail_object
from app.db.repos.gmail.mails.add_mail_to_object import add_mail_to_object
from app.schemas.unread_mails import MailDataSchema
from app.services.gmail_toolkit import GmailToolKit
from app.services.session.get_session import get_session
from app.utils._prompts import (
    IS_MAIL_IMPORTANT_PROMPT,
    IS_RESPONSE_NEEDED_PROMPT,
    MAIL_RESPONSE_FORMAT_PROMPT,
    GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT,
)
from app.services.agents.email_agent.states import EmailState


llm_model = init_chat_model(model="google_genai:gemini-2.0-flash-lite", temperature=0.5)
namespace_for_memory = ("auth", "user")


def get_gmail_toolkit(state: EmailState, config: RunnableConfig) -> Command:
    """
    Start the Gmail toolkit if it is not already running.
    This Node checks the current status of the Gmail toolkit and starts it if it is not running.
    """
    # getting username and thread_id for chat instance
    configurable: Dict[str, Any] | None = config.get("configurable", {})
    if configurable:
        username: str = configurable.get("username", "satyam")
        thread_id: str = configurable.get("thread_id", "test_thread")

        # get session data
        session = get_session(username=username, thread_id=thread_id)
        gmail_toolkit: GmailToolKit | None = session.gmail_toolkit
        if gmail_toolkit:
            today = datetime.today().strftime("%d/%m/%Y")
            # logger.debug(f"Today's date: {today}")
            data = gmail_toolkit.check_emails(
                from_date=today,
                to_date=today,
                max_results=1,
                is_read=False,
            )
            logger.debug(f"Email data: {data}")
            if len(data) > 0:
                mail_data = MailDataSchema(
                    mail_id=data[0]["id"],
                    subject=data[0]["subject"],
                    sender_email_address=data[0]["sender"],
                    date_time_received=data[0]["date"],
                    body=data[0]["body"],
                    unread=data[0]["unread"],
                    snippet=data[0]["snippet"],
                )
                result = add_mail_to_object(
                    username=username,
                    individual_mail_data=mail_data,
                    namespace_for_memory=namespace_for_memory,
                )
                if result and result["status"] == "success":
                    logger.debug(result["message"])

                    return Command(
                        update={
                            "email": data[0],
                            "current_mail_id": data[0]["id"],
                        }
                    )

    return Command()


def analyze_importance(state: EmailState) -> Command:
    """
    Analyze the importance of the email using the AI toolkit.
    """

    email_data = state["email"]

    messages = [
        SystemMessage(content=IS_MAIL_IMPORTANT_PROMPT),
        HumanMessage(content=f"{email_data}"),
    ]
    important_response = _to_text(llm_model.invoke(messages).content).lower().strip()

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
    response_needed = _to_text(llm_model.invoke(messages).content).lower().strip()

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
    response_format = _to_text(llm_model.invoke(messages).content).lower().strip()
    return {"response_format": response_format}


def generate_draft_response(state: EmailState, config: RunnableConfig):
    """
    Generate a draft response for the email using the AI toolkit.
    """
    email_data = state["email"]
    messages = [
        SystemMessage(content=GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT),
        HumanMessage(content=f"{email_data}"),
        HumanMessage(content=f"Mail style :{state['response_format']}"),
    ]
    draft_response = _to_text(llm_model.invoke(messages).content).lower().strip()

    current_mail_id: str = state["current_mail_id"]

    # get username and thread_id
    configurable: Dict[str, Any] | None = config.get("configurable", {})
    if configurable:
        username = configurable.get("username")

        if username:
            result = add_draft_to_mail_object(
                username, current_mail_id, draft_response, namespace_for_memory
            )
            if result and result["status"] == "success":
                logger.debug(result["message"])

                return {"response_email_draft": draft_response}
