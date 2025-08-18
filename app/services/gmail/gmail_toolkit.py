import json
import os
import time
import base64
import threading
import pickle
from datetime import datetime
from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
from app.core.logging import logger
from google.oauth2.credentials import Credentials
from pydantic import FilePath

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


import os
from dotenv import load_dotenv

load_dotenv()


# TODO: #10 Remove auto GmailToolKit class trigger to generate token.pickle file, as the token is retrived from db and before starting the agent the tokens are saved in backend session
class GmailToolKit:
    def __init__(
        self,
        run_as_thread: bool = False,
        save_json: bool = True,
        creds_file: FilePath = os.getenv("GCP_CREDS_FILE"),
        token_file: FilePath = os.getenv("GCP_TOKEN_FILE"),
        json_file: FilePath = os.getenv("GMAIL_DATA_SAVE_FILE"),
        interval: int = 5,
        max_results: int = 1,
        date=None,
    ):
        """
        Initializes the GmailToolKit with the provided parameters and sets up the Gmail API service.
        Parameters:
            run_as_thread: bool = False - If True, runs the email monitoring in a separate thread.
            save_json: bool = True - If True, saves the fetched emails to a JSON file.
            creds_file: FilePath = os.getenv("GCP_CREDS_FILE") - Path to the Google API credentials file.
            token_file: FilePath = os.getenv("GCP_TOKEN_FILE") - Path to the token file for storing OAuth tokens.
            json_file: FilePath = os.getenv("GMAIL_DATA_SAVE_FILE") - Path to the JSON file where emails will be saved.
            interval: int = 5 - Time interval in seconds for checking new emails.
            max_results: int = 1 - Maximum number of emails to fetch in each check.
            date: Optional[str] = None - Date filter for fetching emails in (d, m, y) format.
        """
        self.run_as_thread = run_as_thread
        self.save_json = save_json
        self.recent_emails: List = []
        self.max_results = max_results
        self.date = date
        self.json_file = json_file
        self.creds_file = creds_file
        self.token_file = token_file
        self.interval = interval
        self.service = None
        self.monitoring_active: bool = False
        self.monitor_thread = None
        self.paused: bool = False
        self.last_check_time = None
        self.logger = logger
        self.authenticate()
        self.logger.debug("GmailToolKit initialized.")

    def authenticate(self):
        """
        Authenticate with Gmail API and initialize service.
        Initially uses creds.json file to initiate OAuth2 flow.
        If token.pickle exists, it loads the credentials from there.
        If the token.pickle file does not exist, it creates a new one after successful authentication.
        If the token.pickle file is invalid or expired, it refreshes them or prompts for re-authentication.
        """
        creds = None

        # Load existing token if it exists
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "rb") as token:
                    creds = pickle.load(token)
                self.logger.debug("Token file loaded successfully.")
            except (pickle.PickleError, EOFError, FileNotFoundError) as e:
                self.logger.error(f"Error loading token file: {str(e)}", exc_info=True)
                # Remove corrupted token file
                try:
                    os.remove(self.token_file)
                    self.logger.debug("Corrupted token file removed.")
                except OSError:
                    pass
                creds = None
            except Exception as e:
                self.logger.error(
                    f"Unexpected error loading token file: {str(e)}", exc_info=True
                )
                creds = None

        # Check if credentials are valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    self.logger.debug("Refreshing expired token...")
                    creds.refresh(Request())
                    self.logger.debug("Token refreshed successfully.")
                except Exception as e:
                    self.logger.error(
                        f"Error refreshing token: {str(e)}", exc_info=True
                    )
                    self.logger.debug(
                        "Failed to refresh token, initiating new OAuth flow..."
                    )
                    creds = None

            # If no valid credentials, start OAuth flow
            if not creds or not creds.valid:
                try:
                    if not os.path.exists(self.creds_file):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.creds_file}"
                        )

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.creds_file, SCOPES
                    )
                    creds = self.get_available_port(flow=flow)
                    self.logger.debug("New token generated successfully.")
                except Exception as e:
                    self.logger.error(
                        f"Error during OAuth flow: {str(e)}", exc_info=True
                    )
                    raise RuntimeError(
                        f"Failed to authenticate with Gmail API: {str(e)}"
                    )

            # Save the credentials
            try:
                with open(self.token_file, "wb") as token:
                    pickle.dump(creds, token)
                self.logger.debug("Token saved to pickle file.")
            except Exception as e:
                self.logger.error(f"Error saving token file: {str(e)}", exc_info=True)
                # Continue execution even if saving fails

        # Build the service
        try:
            self.service = build("gmail", "v1", credentials=creds)
            self.logger.debug("Authenticated successfully with Gmail API.")
        except Exception as e:
            self.logger.error(f"Error building Gmail service: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to build Gmail service: {str(e)}")

        # Verify the service works by making a test call
        try:
            # Test the connection with a simple API call
            self.service.users().getProfile(userId="me").execute()
            self.logger.debug("Gmail API connection verified.")
        except Exception as e:
            self.logger.error(
                f"Gmail API connection test failed: {str(e)}", exc_info=True
            )
            raise RuntimeError(f"Gmail API connection failed: {str(e)}")

    def get_available_port(
        self, flow: InstalledAppFlow, start_port=8080, max_attempts=2
    ):
        for port in range(start_port, start_port + max_attempts):
            try:
                creds = flow.run_local_server(port=port)
                return creds
            except PermissionError:
                start_port += 1
                continue
        raise RuntimeError("Could not find an available port")

    def mark_email_as_read(self, service, message_id):
        """Marks an email as read by removing the UNREAD label."""
        try:
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
        except Exception as e:
            self.logger.debug(f"Error marking email {message_id} as read: {str(e)}")

    def load_existing_emails(self):
        """Load existing emails from JSON file to avoid duplicates."""
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    self.logger.debug(
                        "JSON Decoder Error occured while loading existing emails from JSON."
                    )
                    return []
        return []

    def save_emails_to_json(self, emails):
        """Append new emails to JSON file without overwriting old emails."""
        existing_emails = self.load_existing_emails()
        existing_ids = {email["id"] for email in existing_emails}

        new_emails = [email for email in emails if email["id"] not in existing_ids]

        if new_emails:
            existing_emails.extend(new_emails)
            with open(self.json_file, "w") as file:
                json.dump(existing_emails, file, indent=4)

            # print(f"Saved {len(new_emails)} new email(s) to {self.json_file}")

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
            self.mark_email_as_read(self.service, message_id)
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
                        Each email is obtained using `self.get_email_content(message_id)`.

        Raises:
            Logs the exception and returns an empty list if any error occurs during execution.

        Example:
            emails = self.check_emails(
                from_date="01/07/2025",
                to_date="15/07/2025",
                sender="billing@example.com",
                is_read=False,
                has_attachment=True,
                filename="pdf",
                max_results=5
            )
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
                search_query += (
                    f" larger:{larger_than.upper()}"  # Gmail uses 1M, 1K, etc.
                )

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

    def background_monitor(self, max_results, date):
        """Background function to monitor emails periodically."""
        while self.monitoring_active:
            if self.paused:
                time.sleep(1)
                continue

            try:
                self.recent_emails: List = self.check_emails(
                    max_results=max_results, date=date
                )
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
                args=(self.max_results, self.date),
            )
            self.monitor_thread.start()
            self.logger.debug("Started monitoring emails in background thread...")
        else:
            # Run directly in the current thread
            try:
                self.recent_emails = self.check_emails(
                    max_results=self.max_results, date=self.date
                )
                if self.recent_emails and self.save_json:
                    self.save_emails_to_json(self.recent_emails)
                self.last_check_time = datetime.now()

                return self.recent_emails
            except Exception as e:
                self.logger.error(f"Error in monitoring: {str(e)}", exc_info=True)
            self.logger.debug("Completed single email check...")

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
        """Retrieve the most recent emails.
        Returns:
            List of recent emails.
        If no emails are found, returns an empty list.
        """
        return self.recent_emails

    def send_mail(self, to, subject, body) -> Dict[str, Any]:
        """
        Send an email using the Gmail API.
        Args:
            to (str): Recipient email address.
            subject (str): Subject of the email.
            body (str): Body content of the email.
        Returns:
            status (Dict[str, Any]): A dictionary containing the success status and message.
            {"success": bool, "message": str}
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


# Example usage
if __name__ == "__main__":
    tool = GmailToolKit(run_as_thread=False, max_results=5, save_json=False)
    tool.start()
    print(tool.get_mails())
