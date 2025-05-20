from typing import List
from .states import SequenceState
from src.core.gmail.status import GmailToolKitRunningStatus
from src.core.json.reader import JSONEmailReader


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
        print("yes")
        state.gmail_tool.start()

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
    return {"gmail_toolkit_status": GmailToolKitRunningStatus.RUNNING}


def read_emails_json(state: SequenceState):
    """
    Read emails from the email reader and update the state with the email data.
    Asynch method (blocking), so that start on next node execution is awaited till the emails are read.
    """
    state.gmail_tool.wait_for_data(file_path="emails.json")

    email_reader = JSONEmailReader()
    emails: List[dict] = email_reader.get_all_email_content()

    if not isinstance(emails, list) or not emails:
        print("No emails found.")
        print(emails)
        return None

    return {
        "email": emails,
    }  # Return the first valid email data found


def analyze_importance(state: SequenceState):
    """
    Analyze the importance of the email using the AI toolkit.
    """
    if not state.email:
        return None

    email_data = state.email
    # print(asyncio.iscoroutinefunction(state.ai_toolkit.analyze_importance))
    important_response = state.ai_toolkit.analyze_importance(
        email_data=email_data, json_output=True
    )
    decision1 = important_response.get("output", "").lower().strip()

    return {
        "is_mail_important": decision1 == "yes",
    }


async def summarize_email(state: SequenceState):
    """
    Summarize the email using the AI toolkit.
    """
    if not state.email:
        return None
    if state.is_mail_important:
        email_data = state.email
        summary = await state.ai_toolkit.summarize_email(
            email_data=email_data, json_output=True
        )
        return {"email_summary": summary.get("output")}


async def is_response_needed(state: SequenceState):
    """
    Check if a response is needed for the email using the AI toolkit.
    """
    if not state.email:
        return None
    if state.is_mail_important:
        email_data = state.email
        response_needed = await state.ai_toolkit.is_response_needed(
            email_data=email_data, json_output=True
        )
        decision2 = response_needed.get("output", "").lower().strip()
        return {"is_response_needed": decision2 == "yes"}


async def mail_response_format(state: SequenceState):
    """
    Get the response format for the email using the AI toolkit.
    """
    if not state.email:
        return None
    if state.is_mail_important and state.is_response_needed:
        email_data = state.email
        format_response = await state.ai_toolkit.mail_response_format(
            email_data=email_data, json_output=True
        )
        response_format = format_response.get("output", "").lower().strip()
        return {"response_format": response_format}


async def generate_draft_response(state: SequenceState):
    """
    Generate a response for the email using the AI toolkit.
    """
    if not state.email:
        return None
    if state.is_mail_important and state.is_response_needed:
        email_data = state.email
        response_suggestion = await state.ai_toolkit.generate_response(
            email_data=email_data,
            json_output=True,
            style=state.response_format,
        )
        response_text = response_suggestion.get("output")
        return {"response_email_draft": response_text}


async def get_response_approval(state: SequenceState):
    """
    Get the response approval from the user.
    """
    # Simulate user approval for the response
    input_text = (
        await input("Do you approve the draft response to be sent? (yes/no): ")
        .strip()
        .lower()
    )
    if input_text == "yes":
        user_approval = True
    elif input_text == "no":
        user_approval = False
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
        return None
    return {"response_approved": user_approval}


async def get_draft_edit_mode(state: SequenceState):
    """
    Get the draft edit mode from the user.
    This is a function which lets users choose the edit mode of draft (manual/auto).
    """
    # Simulate user selecting the draft edit mode
    input_text = (
        await input(
            "How do you want to edit the draft? (manual: 0/auto: 1/ skip response: 2): "
        )
        .strip()
        .lower()
    )
    if input_text == "0":
        return {"draft_manual_edit_mode": 0}
    elif input_text == "1":
        return {"draft_manual_edit_mode": 1}
    elif input_text == "2":
        return {"draft_manual_edit_mode": 2}
    else:
        print("Invalid input. Please enter '0' or '1' or '2'.")
        return None


async def get_edited_response(state: SequenceState):
    """
    Get the edited response from the user.
    """
    # Simulate user editing the response
    print("Current response draft:")
    print(state.response_email_draft)
    input_text = await input("Please edit the response: ").strip()
    if input_text:
        return {"response_email_draft": input_text}
    return None


async def auto_edit_response(state: SequenceState):
    """
    Auto edit the response for the email using the AI toolkit (LLM) by giving customization instruction.
    """
    if not state.email:
        return None
    if (
        state.is_mail_important
        and state.is_response_needed
        and state.response_email_draft != None
        and state.draft_manual_edit_mode == 1
    ):
        email_data = state.email
        edited_response = await state.ai_toolkit.edit_response(
            email_data=email_data,
            draft_mail=state.response_email_draft,
            json_output=True,
            style=state.response_format,
        )
        edited_response_text = edited_response.get("output")
        return {"response_edited": edited_response_text}


async def send_email_response(state: SequenceState):
    """
    Send the response for the email using the Gmail toolkit.
    """
    if not state.email:
        return None
    if (
        state.is_mail_important
        and state.response_approved
        and state.is_response_needed
        and state.response_email_draft != None
    ):
        email_data = state.email
        response_text = state.response_email_draft
        state.gmail_tool.send_mail(
            to=email_data["sender"],
            subject=email_data["subject"],
            body=response_text,
        )
        return {"response_sent": True}
