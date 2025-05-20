import os
import json
from typing import List
import logging
import markdown
from bs4 import BeautifulSoup


class JSONEmailReader:
    def __init__(self, json_file="emails.json"):
        self.json_file = json_file
        self.logger = logging.getLogger(__name__)

    def load_emails(self):
        """Load emails from the JSON file."""
        if not os.path.exists(self.json_file):
            self.logger.debug(f"Error: {self.json_file} not found.")
            return []

        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                emails = json.load(file)
                return emails if isinstance(emails, list) else []
        except json.JSONDecodeError:
            self.logger.debug("Error: Unable to decode JSON file.")
            return []

    def extract_text(self, content):
        """Convert HTML or Markdown to plain text and remove extra spaces/newlines."""
        if not content:
            return ""

        # Check if content is HTML
        if "<html" in content.lower() or "<body" in content.lower():
            soup = BeautifulSoup(content, "html.parser")
            text = soup.get_text(separator=" ").strip()
        else:
            # Assume Markdown
            try:
                html_content = markdown.markdown(content)
                soup = BeautifulSoup(html_content, "html.parser")
                text = soup.get_text(separator=" ").strip()
            except Exception as e:
                self.logger.error(
                    f"Exception {e} occured while extracting text from HTML or MD"
                )
                text = content.strip()

        # Remove extra spaces and newlines
        return " ".join(text.split())

    def get_all_email_content(self) -> List[dict]:
        """
        Return a list of emails with sender, subject, date, and body as plain text.
        Deletes the emails from the JSON file after reading them.
        """
        emails = self.load_emails()
        if not emails:
            return "No emails found."

        formatted_emails = []
        for email in emails:
            formatted_emails.append(
                {
                    "sender": email.get("sender", "Unknown"),
                    "subject": email.get("subject", "No Subject"),
                    "date": email.get("date", "Unknown Date"),
                    "body": self.extract_text(email.get("body", "")),
                }
            )

        self.delete_read_emails()

        return formatted_emails

    def delete_read_emails(self):
        """Deletes all emails from the JSON file after reading."""
        try:
            with open(self.json_file, "w", encoding="utf-8") as file:
                json.dump([], file, indent=4)  # Overwrite file with an empty list
            self.logger.debug("All read emails have been deleted from the JSON file.")
        except Exception as e:
            self.logger.debug(f"Error deleting emails: {e}")


# Example usage
if __name__ == "__main__":
    reader = JSONEmailReader()
    emails = reader.get_all_email_content()

    if isinstance(emails, list):
        for email in emails:
            print(
                f"From: {email['sender']}\nSubject: {email['subject']}\nDate: {email['date']}\nBody:\n{email['body']}\n"
            )
            print("=" * 80)  # Separator
    else:
        print(emails)
