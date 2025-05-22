import json
import os
import time
import base64
import threading
import pickle
from datetime import datetime
from typing import List, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
import logging
from google.oauth2.credentials import Credentials
from pydantic import FilePath

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


import os
from dotenv import load_dotenv

load_dotenv()


class GmailToolKit:
    def __init__(
        self,
        creds_file: FilePath = os.getenv("GCP_CREDS_FILE"),
        token_file: FilePath = os.getenv("GCP_TOKEN_FILE"),
        json_file: FilePath = os.getenv("GMAIL_DATA_SAVE_FILE"),
        interval: int = 5,
        max_results: int = 1,
        date=None,
    ):
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
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.authenticate()
        self.logger.debug("GmailToolKit initialized.")

    def authenticate(self):
        """
        Authenticate with Gmail API and initialize service.
        Initially uses creds.json file to initiate OAuth2 flow.
        If token.pickle exists, it loads the credentials from there.
        If the token.pickle file does not exist, it creates a new one after successful authentication.
        If the token.pickle file is invalid or expired, it refreshes them or prompts for re-authentication. ## yet to be implemented
        """
        creds: Credentials = None
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "rb") as token:
                    creds: Credentials = pickle.load(token)
        except Exception as e:
            self.logger.error(f"Error loading token file: {str(e)}")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.debug("Refreshing expired token...")
                creds.refresh(Request())
                self.logger.debug("Token refreshed successfully.")
            else:
                flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_file, SCOPES
                )
                creds: Credentials = self.get_available_port(flow=flow)
                self.logger.debug("New token generated successfully.")

            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)
                self.logger.debug("Token saved to pickle file.")

        self.service = build("gmail", "v1", credentials=creds)
        self.logger.debug("Authenticated successfully with Gmail API.")

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

            print(f"Saved {len(new_emails)} new email(s) to {self.json_file}")

    def get_email_content(self, message_id):
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
        self, date: Optional[str], query: str = "is:unread", max_results: int = 1
    ) -> list:
        """Check for emails matching the given query and optional date filter in (d, m, y) format."""
        try:
            # If a date is provided, convert it from (d, m, y) to YYYY/MM/DD format
            if date:
                try:
                    day, month, year = map(
                        int, date.split("/")
                    )  # Expecting "10/3/2024"
                    date_obj = datetime(year, month, day)
                    next_day = date_obj + timedelta(days=1)

                    # Modify the query to fetch emails from that specific date
                    query += f" after:{date_obj.strftime('%Y/%m/%d')} before:{next_day.strftime('%Y/%m/%d')}"
                except ValueError:
                    self.logger.debug(
                        "Invalid date format! Use d,m,y (e.g., 10,3,2024)."
                    )
                    return []

            results = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])

            emails = []
            for message in messages:
                email = self.get_email_content(message["id"])
                if email:
                    emails.append(email)
                    # self.log(
                    #     f"New Email - From: {email['sender']}, Subject: {email['subject']}"
                    # )

            return emails
        except Exception as e:
            self.logger.error(f"Error fetching emails: {str(e)}")
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
                if self.recent_emails:
                    self.save_emails_to_json(self.recent_emails)

                self.last_check_time = datetime.now()
                self.logger.debug(f"Going to sleep for {self.interval} seconds...")
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Error in background monitoring: {str(e)}")

    def start(self):
        """Start monitoring emails in a background thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.paused = False
            self.monitor_thread = threading.Thread(
                target=self.background_monitor,
                daemon=True,
                args=(self.max_results, self.date),
            )
            self.monitor_thread.start()
            self.logger.debug("Started monitoring emails...")
        else:
            self.logger.debug("Monitoring is already active.")

    def wait_for_data(self, file_path: str, timeout: int = 10):
        start_time = time.time()
        while not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            if time.time() - start_time > timeout:
                raise TimeoutError("Data not ready within timeout.")
            time.sleep(0.5)

    def stop(self):
        """Stop the background monitoring thread."""
        self.monitoring_active = False
        self.logger.debug("Stopped monitoring emails.")
        if self.monitor_thread:
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
        return self.recent_emails

    def send_mail(self, to, subject, body):
        """Send an email using the Gmail API."""
        try:
            message = {
                "raw": base64.urlsafe_b64encode(
                    f"From: me\nTo: {to}\nSubject: {subject}\n\n{body}".encode("utf-8")
                ).decode("utf-8")
            }
            self.service.users().messages().send(userId="me", body=message).execute()
            self.logger.debug(f"Email sent to {to} with subject '{subject}'")
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")


# Example usage
if __name__ == "__main__":
    tool = GmailToolKit()
    tool.start()
    # print(tool.check_emails())
    time.sleep(10)
    tool.pause()
    time.sleep(5)
    tool.resume()
    time.sleep(5)
    tool.restart()
    time.sleep(10)
    tool.stop()
