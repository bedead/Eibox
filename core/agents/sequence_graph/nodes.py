import time
from typing import List
from .states import SequenceState
from core.gmail import GmailToolKitRunningStatus
from core.json import JSONEmailReader
from langgraph.types import interrupt, Command
from langgraph.graph import END


def start_gmail_toolkit(state: SequenceState):
    """
    Start the Gmail toolkit if it is not already running.
    This Node checks the current status of the Gmail toolkit and starts it if it is not running.
    """
    if (
        state.gmail_toolkit_status != GmailToolKitRunningStatus.RUNNING
        and state.gmail_toolkit_status == GmailToolKitRunningStatus.STOPED
        and state.gmail_toolkit_status != GmailToolKitRunningStatus.PAUSED
    ):
        state.gmail_tool.start()
        time.sleep(5)

        return {"gmail_toolkit_status": GmailToolKitRunningStatus.RUNNING}


def pasue_gmail_toolkit(state: SequenceState):
    """
    Pause the Gmail toolkit if it is not already paused.
    This Node checks the current status of the Gmail toolkit and pauses it if it is not paused.
    """
    if (
        state.gmail_toolkit_status != GmailToolKitRunningStatus.PAUSED
        and state.gmail_toolkit_status == GmailToolKitRunningStatus.RUNNING
        and state.gmail_toolkit_status != GmailToolKitRunningStatus.STOPED
    ):
        state.gmail_tool.pause()

    return {"gmail_toolkit_status": GmailToolKitRunningStatus.PAUSED}


def resume_gmail_toolkit(state: SequenceState):
    if (
        state.gmail_toolkit_status != GmailToolKitRunningStatus.RUNNING
        and state.gmail_toolkit_status == GmailToolKitRunningStatus.PAUSED
        and state.gmail_toolkit_status != GmailToolKitRunningStatus.STOPED
    ):
        state.gmail_tool.resume()
        time.sleep(5)

        return {"gmail_toolkit_status": GmailToolKitRunningStatus.RUNNING}


def stop_gmail_toolkit(state: SequenceState):
    if (
        state.gmail_toolkit_status != GmailToolKitRunningStatus.STOPED
        and state.gmail_toolkit_status == GmailToolKitRunningStatus.RUNNING
        and state.gmail_toolkit_status != GmailToolKitRunningStatus.PAUSED
    ):
        state.gmail_tool.stop()
    return {"gmail_toolkit_status": GmailToolKitRunningStatus.STOPED}


def restart_gmail_toolkit(state: SequenceState):
    if (
        state.gmail_toolkit_status == GmailToolKitRunningStatus.RUNNING
        and state.gmail_toolkit_status != GmailToolKitRunningStatus.STOPED
        and state.gmail_toolkit_status != GmailToolKitRunningStatus.PAUSED
    ):
        state.gmail_tool.restart()
        time.sleep(5)

    return {"gmail_toolkit_status": GmailToolKitRunningStatus.RUNNING}


def read_emails_json(state: SequenceState):
    """
    Read emails from the email reader and update the state with the email data.
    """
    email_reader = JSONEmailReader()
    emails: List[dict] = email_reader.get_all_email_content()

    if not isinstance(emails, list) or not emails:
        print("No emails found.")
        # print(emails)
        return

    ## interrupt debug code
    resp = interrupt(
        {
            "question": f"Found {len(emails)} emails. Do you want to process the first one? (y/n):"
        }
    )
    if resp.lower() != "y":
        print("Skipping email processing.")
        return {
            "email": emails[0],
        }
    else:
        Command(goto=END)

    return {
        "email": emails[0],
    }  # Return the first valid email data found


def analyze_importance(state: SequenceState):
    """
    Analyze the importance of the email using the AI toolkit.
    """
    if not state.email:
        return

    email_data = state.email
    # print(asyncio.iscoroutinefunction(state.ai_toolkit.analyze_importance))
    important_response = state.ai_toolkit.analyze_importance(
        email_data=email_data, json_output=True
    )
    decision1 = important_response.get("output", "").lower().strip()
    print(f"Analyzed 1 mail importance: {decision1}")

    return {
        "is_mail_important": decision1 == "yes",
    }


def summarize_email(state: SequenceState):
    """
    Summarize the email using the AI toolkit.
    """
    if not state.email:
        return
    if state.is_mail_important:
        email_data = state.email
        summary = state.ai_toolkit.summarize_email(
            email_data=email_data, json_output=True
        )

        print(f"Summarized mail: {summary.get('output')}")
        return {"email_summary": summary.get("output")}


def is_response_needed(state: SequenceState):
    """
    Check if a response is needed for the email using the AI toolkit.
    """
    if not state.email:
        return
    if state.is_mail_important:
        email_data = state.email
        response_needed = state.ai_toolkit.is_response_needed(
            email_data=email_data, json_output=True
        )
        decision2 = response_needed.get("output", "").lower().strip()
        return {"is_response_needed": decision2 == "yes"}


def mail_response_format(state: SequenceState):
    """
    Get the response format for the email using the AI toolkit.
    """
    if not state.email:
        return
    if state.is_mail_important and state.is_response_needed:
        email_data = state.email
        format_response = state.ai_toolkit.mail_response_format(
            email_data=email_data, json_output=True
        )
        response_format = format_response.get("output", "").lower().strip()
        print(f"Chosen draft Response format: {response_format}")
        return {"response_format": response_format}


def generate_draft_response(state: SequenceState):
    """
    Generate a draft response for the email using the AI toolkit.
    """
    if not state.email:
        return
    if state.is_mail_important and state.is_response_needed:
        email_data = state.email
        response_suggestion = state.ai_toolkit.generate_response(
            email_data=email_data,
            json_output=True,
            style=state.response_format,
        )
        response_text = response_suggestion.get("output")

        return {"response_email_draft": response_text}


def get_response_approval(state: SequenceState):
    """
    Get the response approval from the user.
    """
    # Simulate user approval for the response
    print("Draft response:")
    print(
        state.response_edited if state.response_edited else state.response_email_draft
    )
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


def get_draft_edit_mode(state: SequenceState):
    """
    Get the draft edit mode from the user.
    This is a function which lets users choose the edit mode of draft (manual/auto).
    """
    # Simulate user selecting the draft edit mode
    edit_mode = interrupt(
        {
            "question": "How do you want to edit the draft? (manual: 0/auto: 1/ skip response: 2):"
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


def get_edited_response(state: SequenceState):
    """
    Get the edited response from the user.
    """
    # Simulate user editing the response
    manual_edited_draft = interrupt({"question": "Please edit the response:"})
    if manual_edited_draft:
        return {"response_email_draft": manual_edited_draft}
    return


def auto_edit_response(state: SequenceState):
    """
    Auto edit the response for the email using the AI toolkit (LLM) by giving customization instruction.
    """
    if not state.email:
        return
    if (
        state.is_mail_important
        and state.is_response_needed
        and state.response_email_draft != None
        and state.draft_manual_edit_mode == 1
    ):
        customization_instruction = interrupt(
            {"question": "Please provide customization instruction for the response:"}
        )
        email_data = state.email
        edited_response = state.ai_toolkit.edit_response(
            email_data=email_data,
            draft_mail=state.response_email_draft,
            additional_context=customization_instruction,
            json_output=True,
            style=state.response_format,
        )
        edited_response_text = edited_response.get("output")
        return {"response_edited": edited_response_text}


def send_email_response(state: SequenceState):
    """
    Send the response for the email using the Gmail toolkit.
    """
    if not state.email:
        return
    if (
        state.is_mail_important
        and state.response_approved
        and state.is_response_needed
        and state.response_email_draft != None
    ):
        email_data = state.email
        response_text = (
            state.response_edited
            if state.response_edited
            else state.response_email_draft
        )
        status = state.gmail_tool.send_mail(
            to=email_data["sender"],
            subject=email_data["subject"],
            body=response_text,
        )
        return {"response_sent": status["status"]}
