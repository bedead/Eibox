import time

from core.utils.prompts import (
    MAIL_SUMMARY_PROMPT,
    IS_MAIL_IMPORTANT_PROMPT,
    IS_RESPONSE_NEEDED_PROMPT,
    MAIL_RESPONSE_FORMAT_PROMPT,
    GENERATE_MAIL_RESPONSE_SUGGESTION_PROMPT,
    EDIT_SUGGESTED_RESPONSE_PROMPT,
)
from ..shared_state import SharedState
from langgraph.types import interrupt, Command
from core.gmail import GmailToolKit

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model

llm_model = init_chat_model(model="ollama:qwen2.5:0.5b")
# gmail_tool = GmailToolKit(run_as_thread=False, save_json=False)


def get_gmail_toolkit(state: SharedState) -> Command:
    """
    Start the Gmail toolkit if it is not already running.
    This Node checks the current status of the Gmail toolkit and starts it if it is not running.
    """
    # gmail_tool.start()

    time.sleep(5)
    gmail = {
        "id": "17f3a12b2e6c9a5e",
        "subject": "URGENT: Immediate Action Required on Your Internship Application",
        "sender": "hr@companycareers.com",
        "date": "2025-07-03T09:15:00Z",
        "body": "Dear Satyam,\n\nWe reviewed your internship application and require additional documents to process your candidacy. Please upload your updated resume and project portfolio by 6 PM IST today. Without these, your application will not be considered further.\n\nIf you've already submitted them, kindly ignore this message.\n\nRegards,\nHR Team\nCompanyCareers",
        "unread": True,
        "snippet": "We reviewed your internship application and require additional documents to process...",
    }

    # return Command(update={"email": gmail_tool.get_mails()[0]})
    return Command(update={"email": gmail})


def analyze_importance(state: SharedState) -> Command:
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
    print(f"Analyzed 1 mail importance: {important_response}")

    return Command(update={"is_mail_important": important_response == "yes"})


def summarize_email(state: SharedState):
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

        print(f"Summarized mail: {summary}")
        return {"email_summary": summary}


def is_response_needed(state: SharedState):
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


def mail_response_format(state: SharedState):
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
        print(f"Chosen draft Response format: {response_format}")
        return {"response_format": response_format}


def generate_draft_response(state: SharedState):
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
        response_format = llm_model.invoke(messages).content.lower().strip()

        return {"response_email_draft": response_format}


def get_response_approval(state: SharedState):
    """
    Get the response approval from the user.
    """
    # Simulate user approval for the response
    print("Draft response:")
    print(state["response_email_draft"])
    is_approved = interrupt(
        {"question": "Do you approve the draft response to be sent? (y/n):"}
    )
    if is_approved == "y":
        user_approval = True
    elif is_approved == "n":
        user_approval = False
    else:
        print("Invalid input. Please enter 'y' or 'n'.")
        return
    return {"response_approved": user_approval}


def get_draft_edit_mode(state: SharedState):
    """
    Get the draft edit mode from the user.
    This is a function which lets users choose the edit mode of draft (manual/auto).
    """
    # Simulate user selecting the draft edit mode
    edit_mode = interrupt(
        {
            "question": "How do you want to edit the draft? (manual: 0/auto: 1/ no response: 2):"
        }
    )
    if edit_mode == 0:
        return {"draft_manual_edit_mode": 0}
    elif edit_mode == 1:
        return {"draft_manual_edit_mode": 1}
    elif edit_mode == 2:
        return {"draft_manual_edit_mode": 2}
    else:
        print("Invalid input. Please enter 0 or 1 or 2.")
        return


def get_edited_response(state: SharedState):
    """
    Get the edited response from the user.
    """
    # Simulate user editing the response
    manual_edited_draft = interrupt({"question": "Please edit the response:"})
    if manual_edited_draft:
        return {"response_email_draft": manual_edited_draft}
    return


def auto_edit_response(state: SharedState):
    """
    Auto edit the response for the email using the AI toolkit (LLM) by giving customization instruction.
    """
    if not state["email"]:
        return
    if (
        state["is_mail_important"]
        and state["is_response_needed"]
        and state["response_email_draft"] != None
        and state["draft_manual_edit_mode"] == 1
    ):
        customization_instruction = interrupt(
            {"question": "Please provide customization instruction for the response:"}
        )
        email_data = state["email"]
        messages = [
            SystemMessage(content=EDIT_SUGGESTED_RESPONSE_PROMPT),
            HumanMessage(content=f"Mail data :{email_data}"),
            HumanMessage(content=f"Draft mail :{state['response_email_draft']}"),
            HumanMessage(
                content=f"Customization instruction :{customization_instruction}"
            ),
            HumanMessage(content=f"Mail style :{state['response_format']}"),
        ]
        edited_response_text = llm_model.invoke(messages).content.lower().strip()
        return {"response_edited": edited_response_text}


def send_email_response(state: SharedState):
    """
    Send the response for the email using the Gmail toolkit.
    """
    if not state["email"]:
        return
    if (
        state["is_mail_important"]
        and state["response_approved"]
        and state["is_response_needed"]
        and state["response_email_draft"] != None
    ):
        email_data = state["email"]
        response_text = (
            state["response_edited"]
            if state["response_edited"]
            else state["response_email_draft"]
        )
        # status = gmail_tool.send_mail(
        #     to=email_data["sender"],
        #     subject=email_data["subject"],
        #     body=response_text,
        # )
        # dummy testing mechanism
        status = {"success": True}
        return {"response_sent": status["success"]}
