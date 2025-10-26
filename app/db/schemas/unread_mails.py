from typing import List, Optional
from pydantic import BaseModel


class MailDataSchema(BaseModel):
    mail_id: str
    subject: str
    sender_email_address: str
    date_time_received: str
    body: str
    unread: bool
    snippet: str
    draft_response: Optional[str] = None


class UnreadMailsSchema(BaseModel):
    unread_mails_count: int
    mails_data: List[MailDataSchema]
