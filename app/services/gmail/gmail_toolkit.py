import os
import time
import base64
import threading
import requests
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Callable
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.logging import logger
from app.db.repos.gmail.add_gmail_accounts import add_gmail_account
from app.schemas.gmail_account import GmailAccount
from app.utils.common import get_gcp_client_id, get_gcp_client_secret
from app.core.config import settings


class GmailToolKit:
    def __init__(
        self,
        gmail_account: GmailAccount,
        run_as_thread: bool = False,
        interval: int = 5,
        max_results: int = 1,
    ):
        """
        Initializes the GmailToolKit with the provided parameters and sets up the Gmail API service.

        Parameters:
            gmail_account: GmailAccount - The Gmail account data containing access token
            run_as_thread: bool = False - If True, runs the email monitoring in a separate thread.
            interval: int = 5 - Time interval in seconds for checking new emails.
            max_results: int = 1 - Maximum number of emails to fetch in each check.
        """
        self.gmail_account = gmail_account
        self.run_as_thread = run_as_thread
        self.max_results = max_results
        self.interval = interval
        self.logger = logger
        self.recent_emails: List = []
        self.service = None
        self.monitoring_active: bool = False
        self.monitor_thread = None
        self.paused: bool = False
        self.last_check_time = None
        self.creds = None
        self.authenticate()
        self.logger.debug(f"GmailToolKit initialized for {self.gmail_account.email}.")

    def authenticate(self):
        """
        Authenticate with Gmail API using the provided access token.
        """
        try:
            # Create credentials object from the access token
            creds = Credentials(
                token=self.gmail_account.access_token,
                refresh_token=self.gmail_account.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=get_gcp_client_id(),
                client_secret=get_gcp_client_secret(),
                scopes=self.gmail_account.scope or settings.GOOGLE_GMAIL_SCOPE,
            )

            # Build the service
            self.service = build(serviceName="gmail", version="v1", credentials=creds)

            # Verify the service works by making a test call
            profile = self.service.users().getProfile(userId="me").execute()
            self.logger.debug(
                f"Gmail API connection verified. Email: {profile.get('emailAddress')}"
            )
            self.creds = creds
            self._maybe_persist_tokens()

        except Exception as e:
            self.logger.error(
                f"Error authenticating with Gmail API: {str(e)}", exc_info=True
            )
            raise RuntimeError(f"Failed to authenticate with Gmail API: {str(e)}")

    def _maybe_persist_tokens(self):
        """Update refresh tokens if refresh successful."""
        if self.creds:
            self.gmail_account.access_token = self.creds.token
            self.gmail_account.refresh_token = self.creds.refresh_token
            expiry = self.creds.expiry
            if expiry is None:
                self.gmail_account.expires_in = 3600
            else:
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
                self.gmail_account.expires_in = max(0, int((expiry.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()))

            self.gmail_account.token_last_refresh_time = str(datetime.now())
            add_gmail_account(
                new_account=self.gmail_account, namespace_for_memory=("auth", "user")
            )

    def mark_email_as_read(self, message_id):
        """Marks an email as read by removing the UNREAD label."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
        except Exception as e:
            self.logger.debug(f"Error marking email {message_id} as read: {str(e)}")

    def get_email_content_based_on_gmail_id(self, message_id):
        """Retrieve email content given the email ID."""
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = message.get("payload", {}).get("headers", [])
            subject = sender = date = ""
            for header in headers:
                if header["name"] == "Subject":
                    subject = header["value"]
                elif header["name"] == "From":
                    sender = header["value"]
                elif header["name"] == "Date":
                    date = header["value"]

            body = ""
            payload = message.get("payload", {})
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain" and "body" in part:
                        body_data = part["body"].get("data", "")
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode("utf-8")
                            break
            elif "body" in payload and "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

            # Mark email as read
            self.mark_email_as_read(message_id)

            return {
                "id": message_id,
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body,
                "unread": "UNREAD" in message.get("labelIds", []),
                "snippet": message.get("snippet", ""),
            }
        except Exception as e:
            self.logger.debug(f"Error retrieving email {message_id}: {str(e)}")
            return None

    def check_emails(
        self,
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
        Fetches emails from the user's Gmail inbox using advanced search filters.
        """
        try:

            def parse_date(date_str: str) -> str:
                day, month, year = map(int, date_str.split("/"))
                return datetime(year, month, day).strftime("%Y/%m/%d")

            # === Construct Gmail search query ===
            search_query = ""

            if from_date:
                search_query += f" after:{parse_date(from_date)}"
            if to_date:
                to_dt = datetime.strptime(parse_date(to_date), "%Y/%m/%d") + timedelta(
                    days=1
                )
                search_query += f" before:{to_dt.strftime('%Y/%m/%d')}"

            if subject:
                search_query += f' subject:"{subject}"'
            if sender:
                search_query += f" from:{sender}"
            if recipient:
                search_query += f" to:{recipient}"
            if query:
                search_query += f" {query}"
            if is_read is True:
                search_query += " is:read"
            elif is_read is False:
                search_query += " is:unread"
            if is_starred is True:
                search_query += " is:starred"
            if is_important is True:
                search_query += " is:important"
            if category:
                search_query += f" category:{category}"
            if has_attachment:
                search_query += " has:attachment"
            if filename:
                search_query += f" filename:{filename}"
            if larger_than:
                search_query += f" larger:{larger_than.upper()}"

            # Include spam/trash if needed
            if include_spam or include_trash:
                search_query += " in:anywhere"
            else:
                search_query += " -in:spam -in:trash"

            # === Build request ===
            kwargs = {
                "userId": "me",
                "q": search_query.strip(),
                "maxResults": max_results,
            }

            if label_ids:
                kwargs["labelIds"] = label_ids
            if page_token:
                kwargs["pageToken"] = page_token

            # === Execute search ===
            results = self.service.users().messages().list(**kwargs).execute()
            messages = results.get("messages", [])
            emails = []

            for message in messages:
                email = self.get_email_content_based_on_gmail_id(message["id"])
                if email:
                    emails.append(email)

            return emails

        except Exception as e:
            self.logger.error(f"Error fetching emails: {str(e)}", exc_info=True)
            return []

    def background_monitor(self):
        """Background function to monitor emails periodically."""
        while self.monitoring_active:
            if self.paused:
                time.sleep(1)
                continue

            try:
                self.recent_emails = self.check_emails(max_results=self.max_results)
                if self.recent_emails and self.save_json:
                    self.save_emails_to_json(self.recent_emails)

                self.last_check_time = datetime.now()
                self.logger.debug(f"Going to sleep for {self.interval} seconds...")
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(
                    f"Error in background monitoring: {str(e)}", exc_info=True
                )

    def start(self):
        """Start monitoring emails either in background thread or directly."""
        if self.monitoring_active:
            self.logger.debug("Monitoring is already active.")
            return

        self.monitoring_active = True
        self.paused = False

        if self.run_as_thread:
            self.monitor_thread = threading.Thread(
                target=self.background_monitor,
                daemon=True,
            )
            self.monitor_thread.start()
            self.logger.debug("Started monitoring emails in background thread...")
        else:
            # Run directly in the current thread
            try:
                self.recent_emails = self.check_emails(max_results=self.max_results)
                if self.recent_emails and self.save_json:
                    self.save_emails_to_json(self.recent_emails)
                self.last_check_time = datetime.now()
                return self.recent_emails
            except Exception as e:
                self.logger.error(f"Error in monitoring: {str(e)}", exc_info=True)
                return []
            finally:
                self.monitoring_active = False

    def stop(self):
        """Stop the monitoring process."""
        self.monitoring_active = False
        self.logger.debug("Stopped monitoring emails.")
        if self.run_as_thread and self.monitor_thread:
            self.monitor_thread.join()

    def pause(self):
        """Pause the email monitoring process."""
        if self.monitoring_active and not self.paused:
            self.paused = True
            self.logger.debug("Paused email monitoring.")

    def resume(self):
        """Resume the paused monitoring process."""
        if self.monitoring_active and self.paused:
            self.paused = False
            self.logger.debug("Resumed email monitoring.")

    def restart(self):
        """Restart the email monitoring process."""
        self.stop()
        self.start()
        self.logger.debug("Restarted email monitoring.")

    def get_mails(self):
        """Retrieve the most recent emails."""
        return self.recent_emails

    def send_mail(self, to, subject, body) -> Dict[str, Any]:
        """
        Send an email using the Gmail API.

        Args:
            to (str): Recipient email address.
            subject (str): Subject of the email.
            body (str): Body content of the email.

        Returns:
            Dict[str, Any]: Status dictionary with success and message.
        """
        status = {}
        try:
            message = {
                "raw": base64.urlsafe_b64encode(
                    f"From: me\nTo: {to}\nSubject: {subject}\n\n{body}".encode("utf-8")
                ).decode("utf-8")
            }
            self.service.users().messages().send(userId="me", body=message).execute()
            self.logger.debug(f"Email sent to {to} with subject '{subject}'")
            status["success"] = True
            status["message"] = f"Email sent to {to} with subject '{subject}'"
            return status
        except Exception as e:
            status["success"] = False
            status["message"] = f"Error sending email: {str(e)}"
            self.logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return status

    def delete_email(self, message_id: str):
        """
        Deletes an email by its message ID.

        Args:
            message_id (str): The unique identifier of the email message to be deleted.
        """
        try:
            self.service.users().messages().delete(userId="me", id=message_id).execute()
            self.logger.debug(f"Email with ID {message_id} deleted successfully.")
        except Exception as e:
            self.logger.error(
                f"Error deleting email {message_id}: {str(e)}", exc_info=True
            )
            raise RuntimeError(f"Failed to delete email {message_id}: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Example GmailAccount data
    gmail_account = GmailAccount(
        email="example@gmail.com",
        access_token="your_access_token_here",
        refresh_token="your_refresh_token_here",
        expires_in=3600,
        token_type="Bearer",
        scope=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
        ],
    )

    tool = GmailToolKit(
        gmail_account=gmail_account, run_as_thread=False, max_results=5, save_json=False
    )
    emails = tool.start()
    print(tool.get_mails())
