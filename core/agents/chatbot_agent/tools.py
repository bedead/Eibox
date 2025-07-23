import uuid
from apscheduler.job import Job
from core.gmail.gmail_toolkit import GmailToolKit
from core.job_scheduler.jobs import (
    delete_email_scheduler_job,
    start_email_scheduler_job,
)
from langchain_core.runnables import RunnableConfig
from typing import List, Optional
from langchain_core.tools import tool


@tool
def get_userdetails_tool(config: RunnableConfig):
    """
    Retrieves the user ID and thread ID from the AI agent's runtime configuration.

    This tool is typically used to identify the current user and their associated chat thread

    Returns:
        dict: A dictionary containing:
            - "user_id" (str): The ID or username of the user.
            - "thread_id" (str): The ID representing the current conversation or chat instance.
    """

    return {
        "user_id": config["configurable"].get("user_id"),
        "thread_id": config["configurable"].get("thread_id"),
    }


@tool
def start_email_scheduler_job_tool(user_id: str, thread_id: str, interval: int):
    """
    Starts a scheduled background job that periodically checks or processes emails
    related to a specific user and thread.

    Args:
        user_id (str): The unique identifier for the user.
        thread_id (str): The unique identifier of the email thread to track.
        interval (int): The frequency (in seconds) at which the job should run.

    Returns:
        Job: The background job instance that was started.
    """
    job: Job = start_email_scheduler_job(
        user_id=user_id, thread_id=thread_id, interval=interval
    )
    return job


@tool
def delete_email_scheduler_job_tool(user_id: str, thread_id: str):
    """
    Deletes or stops an existing scheduled job that was set to process or monitor
    emails for a specific user and thread.

    Args:
        user_id (str): The unique identifier for the user.
        thread_id (str): The unique identifier of the thread whose job should be deleted.

    Returns:
        Dict['status':]: status is "success" if job removed, and Exception e is returned in status.
    """
    result = delete_email_scheduler_job(user_id, thread_id)
    return result


@tool
def search_gmails_tool(
    from_date: Optional[str] = None,  # Format: "d/m/yyyy"
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
    larger_than: Optional[str] = None,  # e.g., "5M", "100K"
    category: Optional[str] = None,  # e.g., "promotions", "primary"
    label_ids: Optional[List[str]] = None,  # e.g., ["INBOX", "UNREAD"]
    include_spam: bool = False,
    include_trash: bool = False,
    max_results: int = 10,
    page_token: Optional[str] = None,
) -> List[dict]:
    """
    Fetches gmails from the user's Gmail inbox using advanced search filters based on users request.

    This method provides fine-grained control over Gmail search queries, allowing
    filtering by date range, read/unread status, sender, recipient, subject,
    attachments, labels, categories, size, and more. Internally, it constructs a
    Gmail-compatible query string and uses the Gmail API to fetch matching messages.

    Args:
        from_date (Optional[str]): Start date in "d/m/yyyy" format to filter emails from.
        to_date (Optional[str]): End date in "d/m/yyyy" format to filter emails up to.
        query (Optional[str]): Custom free-text search string (e.g., "invoice OR receipt").
        subject (Optional[str]): Filter emails that have this string in the subject.
        sender (Optional[str]): Filter emails sent from this email address.
        recipient (Optional[str]): Filter emails sent to this email address.
        is_read (Optional[bool]): Set to True to filter read emails, False for unread.
        is_starred (Optional[bool]): Set to True to only include starred emails.
        is_important (Optional[bool]): Set to True to include only important emails.
        has_attachment (Optional[bool]): If True, fetch only emails with attachments.
        filename (Optional[str]): Filter emails with attachments matching this filename or extension.
        larger_than (Optional[str]): Filter emails larger than the given size (e.g., "1M", "500K").
        category (Optional[str]): Gmail tab category (e.g., "primary", "promotions", "social").
        label_ids (Optional[List[str]]): List of Gmail label IDs to restrict results (e.g., ["INBOX", "UNREAD"]).
        include_spam (bool): Whether to include emails from the spam folder.
        include_trash (bool): Whether to include emails from the trash folder.
        max_results (int): Maximum number of email results to fetch. Defaults to 10.
        page_token (Optional[str]): Gmail API pagination token to fetch the next page of results.

    Returns:
        List[dict]: A list of email dictionaries containing parsed metadata and content.
                    Each email is obtained using `self.get_email_content_based_on_gmail_id(message_id)`.

    Raises:
        Logs the exception and returns an empty list if any error occurs during execution.

    Example:
        emails = search_gmails(
            from_date="01/07/2025",
            to_date="15/07/2025",
            sender="billing@example.com",
            is_read=False,
            has_attachment=True,
            filename="pdf",
            max_results=5
        )
    """
    toolkit = GmailToolKit()
    return toolkit.check_emails(
        from_date=from_date,
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
        category=category,
        label_ids=label_ids,
        include_spam=include_spam,
        include_trash=include_trash,
        max_results=max_results,
        page_token=page_token,
    )


all_tools = [
    start_email_scheduler_job_tool,
    delete_email_scheduler_job_tool,
    get_userdetails_tool,
    search_gmails_tool,
]

# Store metadata for each tool
# for tool_id, tool in tool_registry.items():
#     store.put(
#         ("tools",),  # Namespace
#         tool_id,  # Key
#         {
#             "description": f"{tool.name}: {tool.description}",
#         },
#     )
