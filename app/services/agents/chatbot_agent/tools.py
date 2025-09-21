from apscheduler.job import Job
from app.schemas.chat_session import ChatSession
from app.services.gmail.gmail_toolkit import GmailToolKit
from app.services.job_scheduler.jobs import (
    delete_email_scheduler_job,
    start_email_scheduler_job,
)
from langchain_core.runnables import RunnableConfig
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool

from app.services.session.get_session import get_session


# TODO: add more util tools
@tool
def get_userdetails_tool(config: RunnableConfig):
    """
    Retrieves the username and thread ID from the AI agent's runtime configuration.

    This tool is typically used to identify the current user and their associated chat thread

    Returns:
        dict: A dictionary containing:
            - "username" (str): The unique username.
            - "thread_id" (str): The ID representing the current conversation or chat instance.
    """
    configurable: Dict[str, Any] | None = config.get("configurable")

    if configurable is None:
        raise ValueError("Configurable data not found in config.")
    return {
        "username": configurable.get("username"),
        "thread_id": configurable.get("thread_id"),
    }


# @tool
# def start_email_scheduler_job_tool(username: str, thread_id: str, interval: int):
#     """
#     Starts a scheduled background job that periodically checks or processes emails
#     related to a specific user and thread.

#     Args:
#         username (str): The unique username.
#         thread_id (str): The unique identifier of the email thread to track.
#         interval (int): The frequency (in seconds) at which the job should run.

#     Returns:
#         Job: The background job instance that was started.
#     """
#     job: Job = start_email_scheduler_job(
#         username=username, thread_id=thread_id, interval=interval
#     )
#     return job


# @tool
# def delete_email_scheduler_job_tool(username: str, thread_id: str):
#     """
#     Deletes or stops an existing scheduled job that was set to process or monitor
#     emails for a specific user and thread.

#     Args:
#         username (str): The unique username.
#         thread_id (str): The unique identifier of the thread whose job should be deleted.

#     Returns:
#         Dict['status':]: status is "success" if job removed, and Exception e is returned in status.
#     """
#     result = delete_email_scheduler_job(username, thread_id)
#     return result


@tool
def search_gmails_tool(
    username: str,
    thread_id: str,
    max_results: int = 10,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    query: Optional[str] = None,
    subject: Optional[str] = None,
    sender: Optional[str] = None,
    recipient: Optional[str] = None,
    is_read: Optional[bool] = None,
    is_starred: Optional[bool] = None,
    is_important: Optional[bool] = None,
    has_attachment: Optional[bool] = None,
    filename: Optional[str] = None,
    larger_than: Optional[str] = None,
    categories: Optional[List[str]] = None,  # ["promotions", "primary"]
    labels: Optional[List[str]] = None,  # ["INBOX", "UNREAD", "CATEGORY_UPDATES"]
    locations: Optional[List[str]] = None,  # ["in:spam", "in:trash", "in:inbox"]
    extra_filters: Optional[List[str]] = None,  # ["has:drive", "is:snoozed"]
    page_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Fetches Gmail messages using advanced, fine-grained search filters.

    This method provides the smallest possible control over Gmail search queries,
    allowing the caller to combine multiple Gmail search operators to precisely
    target messages. It supports filtering by date range, status flags (read, starred,
    important), sender/recipient, subject, attachments, labels, categories,
    mailbox locations (inbox, spam, trash, etc.), size, and advanced Gmail operators.

    Internally, it constructs a Gmail-compatible query string (`q`) and uses the
    Gmail API to fetch matching messages. By default, spam and trash are excluded
    unless explicitly included via the `locations` argument.

    Args:
        from_date (Optional[str]): Start date in "d/m/yyyy" format to filter emails from.
        to_date (Optional[str]): End date in "d/m/yyyy" format to filter emails up to.
        max_results (int): Maximum number of email results to fetch. Defaults to 10.
        query (Optional[str]): Free-text Gmail search string (e.g., "invoice OR receipt").
        subject (Optional[str]): Filter emails containing this string in the subject.
        sender (Optional[str]): Filter emails sent from this email address.
        recipient (Optional[str]): Filter emails sent to this email address.
        is_read (Optional[bool]): True to filter read emails, False for unread.
        is_starred (Optional[bool]): True to include only starred emails.
        is_important (Optional[bool]): True to include only important emails.
        has_attachment (Optional[bool]): If True, fetch only emails with attachments.
        filename (Optional[str]): Filter emails with attachments matching this filename or extension.
        larger_than (Optional[str]): Filter emails larger than the given size (e.g., "1M", "500K").
        categories (Optional[List[str]]): Restrict search to Gmail categories
            (e.g., ["promotions", "social", "updates", "primary", "forums"]).
        labels (Optional[List[str]]): Restrict search to specific Gmail labels
            (system or custom, e.g., ["INBOX", "CATEGORY_PROMOTIONS"]).
        locations (Optional[List[str]]): Mailbox locations to search in
            (e.g., ["in:spam"], ["in:trash", "in:inbox"]). Can be combined with OR.
        extra_filters (Optional[List[str]]): Advanced Gmail filters such as
            ["has:drive", "is:snoozed", "has:link"]. These are appended directly to the query.
        page_token (Optional[str]): Gmail API pagination token to fetch the next page of results.

    Returns:
        dict: A dictionary containing the status and result data of the search operation.
              Example:
                {"status": "success", "result": List[dict]}
                {"status": "error", "error": "Error message"}

    Raises:
        Logs the exception and returns {"status": "error"} if any error occurs during execution.

    Example:
        # Fetch unread PDF invoices from spam and trash
        emails = search_gmails(
            from_date="01/07/2025",
            to_date="15/07/2025",
            sender="billing@example.com",
            is_read=False,
            has_attachment=True,
            filename="pdf",
            locations=["in:spam", "in:trash"],
            max_results=5
        )
    """
    session: ChatSession = get_session(username=username, thread_id=thread_id)
    if session.gmail_toolkit:
        gmail_toolkit: GmailToolKit = session.gmail_toolkit
        try:
            data: List[Dict[str, Any]] = gmail_toolkit.check_emails(
                from_date=from_date,
                max_results=max_results,
                to_date=to_date,
                query=query,
                subject=subject,
                sender=sender,
                recipient=recipient,
                is_read=is_read,
                is_starred=is_starred,
                is_important=is_important,
                has_attachment=has_attachment,
                filename=filename,
                larger_than=larger_than,
                categories=categories,
                labels=labels,
                locations=locations,
                extra_filters=extra_filters,
                page_token=page_token,
            )
            return {
                "status": "success",
                "result": data,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return {
            "status": "info",
            "info": f"User: {session.username} has not connected Any Gmail account yet.",
        }


@tool
def delete_email_tool(username: str, thread_id: str, message_id: str) -> Dict[str, Any]:
    """
    Deletes a specific email from the user's Gmail account.

    Args:
        username (str): The unique username.
        thread_id (str): The unique identifier of the email thread.
        message_id (str): The unique identifier of the email message to be deleted.

    Returns:
        dict: A dictionary containing the status of the deletion operation.
              Example: {"status": "success"} or {"status": "error", "error": "Error message"}
    """
    session: ChatSession = get_session(username=username, thread_id=thread_id)
    if session.gmail_toolkit:
        gmail_toolkit: GmailToolKit = session.gmail_toolkit
        try:
            gmail_toolkit.delete_email(message_id=message_id)
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return {
            "status": "info",
            "info": f"User: {session.username} has not connected Any Gmail account yet.",
        }


# @tool
# def get_day_of_week() -> str:
#     """
#     Returns the current day of the week (e.g., Monday, Tuesday).

#     Useful for scheduling tasks or contextualizing events based on the weekday.

#     Returns:
#         str: The current day of the week.
#     """
#     from datetime import datetime

#     return datetime.now().strftime("%A")


# @tool
# def get_day_of_month() -> int:
#     """
#     Returns the current day of the month as an integer.

#     Useful for monthly routines, bill reminders, or date-based triggers.

#     Returns:
#         int: The current day of the month (1-31).
#     """
#     from datetime import datetime

#     return datetime.now().day


# @tool
# def get_day_of_year() -> int:
#     """
#     Returns the current day of the year as an integer (1-366).

#     Useful for progress tracking or seasonal calculations.

#     Returns:
#         int: The current day of the year.
#     """
#     from datetime import datetime

#     return int(datetime.now().strftime("%j"))


# @tool
# def get_week_number() -> int:
#     """
#     Returns the ISO week number of the current year (1-53).

#     Useful for weekly planning and organization.

#     Returns:
#         int: The current ISO week number.
#     """
#     from datetime import datetime

#     return datetime.now().isocalendar().week


# @tool
# def is_weekend() -> bool:
#     """
#     Checks whether today is a weekend (Saturday or Sunday).

#     Useful for determining off-days or adjusting behavior based on work schedule.

#     Returns:
#         bool: True if today is Saturday or Sunday, False otherwise.
#     """
#     from datetime import datetime

#     return datetime.now().weekday() >= 5


all_tools = [
    # start_email_scheduler_job_tool,
    # delete_email_scheduler_job_tool,
    get_userdetails_tool,
    search_gmails_tool,
    delete_email_tool,
    # is_weekend,
]
