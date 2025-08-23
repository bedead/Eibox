import json
import os
import time
import base64
import threading
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.logging import logger
from app.schemas.gmail_account import GmailAccount
from app.utils.common import get_gcp_client_id, get_gcp_client_secret
from app.core.config import settings


class GmailToolKit:
    def __init__(
        self,
        gmail_account: GmailAccount,
        run_as_thread: bool = False,
        save_json: bool = False,
        json_file: Optional[str] = None,
        interval: int = 5,
        max_results: int = 1,
        username: str = None,
        token_refresh_callback: Optional[Callable[[GmailAccount, str], None]] = None,
    ):
        """
        Initializes the GmailToolKit with the provided parameters and sets up the Gmail API service.

        Parameters:
            gmail_account: GmailAccount - The Gmail account data containing access token
            run_as_thread: bool = False - If True, runs the email monitoring in a separate thread.
            save_json: bool = True - If True, saves the fetched emails to a JSON file.
            json_file: Optional[str] = None - Path to the JSON file where emails will be saved.
            interval: int = 5 - Time interval in seconds for checking new emails.
            max_results: int = 1 - Maximum number of emails to fetch in each check.
            token_refresh_callback: Optional[Callable] - Callback function to save refreshed tokens
        """
        self.gmail_account = gmail_account
        self.run_as_thread = run_as_thread
        self.save_json = save_json
        self.recent_emails: List = []
        self.max_results = max_results
        self.json_file = (
            json_file or f"emails_{gmail_account.email.replace('@', '_at_')}.json"
        )
        self.interval = interval
        self.service = None
        self.monitoring_active: bool = False
        self.monitor_thread = None
        self.paused: bool = False
        self.last_check_time = None
        self.logger = logger
        self.token_refresh_callback = token_refresh_callback
        self.token_expires_at = None
        self._calculate_token_expiry()
        self.authenticate()
        self.username = username
        self.logger.debug(f"GmailToolKit initialized for {self.gmail_account.email}.")

    def _calculate_token_expiry(self):
        """Calculate when the current token expires."""
        if self.gmail_account.expires_in:
            self.token_expires_at = datetime.now() + timedelta(
                seconds=self.gmail_account.expires_in
            )
        else:
            # Default to 1 hour if expires_in is not provided
            self.token_expires_at = datetime.now() + timedelta(hours=1)

    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or will expire soon (within 5 minutes)."""
        if not self.token_expires_at:
            return True
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))

    def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        Returns True if successful, False otherwise.
        """
        if not self.gmail_account.refresh_token:
            self.logger.error("No refresh token available for token refresh")
            return False

        if not self.gmail_account.client_id or not self.gmail_account.client_secret:
            self.logger.error(
                "Client ID and Client Secret are required for token refresh"
            )
            return False

        try:
            # Google OAuth2 token refresh endpoint
            token_url = "https://oauth2.googleapis.com/token"

            data = {
                "client_id": get_gcp_client_id(),
                "client_secret": get_gcp_client_secret(),
                "refresh_token": self.gmail_account.refresh_token,
                "grant_type": "refresh_token",
            }

            response = requests.post(token_url, data=data)
            response.raise_for_status()

            token_data = response.json()

            # Update the account with new tokens
            self.gmail_account.access_token = token_data["access_token"]
            self.gmail_account.expires_in = token_data.get("expires_in", 3600)
            self.gmail_account.token_last_refresh_time = datetime.now()

            # Update refresh token if a new one is provided
            if "refresh_token" in token_data:
                self.gmail_account.refresh_token = token_data["refresh_token"]

            # Recalculate expiry time
            self._calculate_token_expiry()

            # Call callback to save updated tokens
            if self.token_refresh_callback:
                self.token_refresh_callback(self.gmail_account, username=self.username)

            self.logger.debug(
                f"Token refreshed successfully for {self.gmail_account.email}"
            )
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP error during token refresh: {str(e)}")
            return False
        except KeyError as e:
            self.logger.error(f"Missing key in token refresh response: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(
                f"Unexpected error during token refresh: {str(e)}", exc_info=True
            )
            return False

    def _ensure_valid_token(self):
        """Ensure we have a valid access token, refreshing if necessary."""
        if self._is_token_expired():
            self.logger.debug(
                "Token is expired or will expire soon, attempting refresh..."
            )
            if not self._refresh_access_token():
                raise RuntimeError(
                    "Failed to refresh access token and current token is expired"
                )

            # Re-authenticate with the new token
            self.authenticate()

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
                client_id=None,
                client_secret=None,
                scopes=self.gmail_account.scope or settings.GOOGLE_GMAIL_SCOPE,
            )

            # Build the service
            self.service = build("gmail", "v1", credentials=creds)
            self.logger.debug(
                f"Authenticated successfully with Gmail API for {self.gmail_account.email}."
            )

            # Verify the service works by making a test call
            profile = self.service.users().getProfile(userId="me").execute()
            self.logger.debug(
                f"Gmail API connection verified. Email: {profile.get('emailAddress')}"
            )

        except Exception as e:
            self.logger.error(
                f"Error authenticating with Gmail API: {str(e)}", exc_info=True
            )
            raise RuntimeError(f"Failed to authenticate with Gmail API: {str(e)}")

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

    def load_existing_emails(self):
        """Load existing emails from JSON file to avoid duplicates."""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                self.logger.debug(
                    "JSON Decoder Error occurred while loading existing emails from JSON."
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
            self.logger.debug(
                f"Saved {len(new_emails)} new email(s) to {self.json_file}"
            )

    def get_email_content_based_on_gmail_id(self, message_id):
        """Retrieve email content given the email ID."""
        try:
            # Ensure we have a valid token before making API calls
            self._ensure_valid_token()

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
            # Ensure we have a valid token before making API calls
            self._ensure_valid_token()

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
            # Ensure we have a valid token before making API calls
            self._ensure_valid_token()

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
