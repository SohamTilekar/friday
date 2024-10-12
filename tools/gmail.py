import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
from langchain_core.tools import tool as tool_decorator
from langchain_core.pydantic_v1 import BaseModel, Field
import os
from googleapiclient.errors import HttpError
from sqlalchemy import desc


SCOPES = ["https://mail.google.com/"]

creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
with open("token.json", "w") as token:
    token.write(creds.to_json())

# Initialize and store the Gmail API client
gmail_service = build("gmail", "v1", credentials=creds)

class ReplyEmail(BaseModel):
    message_id: str = Field(..., description="The ID of the email thread to reply to.")
    reply_text: str = Field(..., description="The text content of the reply.")

@tool_decorator("reply_email", args_schema=ReplyEmail)
def reply_email(message_id: str, reply_text: str) -> str:
    """
    Use this tool to reply to an email thread.
    """
    try:
        message = (
            gmail_service.users().messages().get(userId="me", id=message_id).execute()
        )
        thread_id = message["threadId"]

        reply = {
            "raw": base64.urlsafe_b64encode(
                f"To: {message['payload']['headers'][0]['value']}\r\n"
                f"Subject: Re: {message['payload']['headers'][1]['value']}\r\n\r\n"
                + reply_text
            ).decode("utf-8"),
            "threadId": thread_id,
        }

        gmail_service.users().messages().send(userId="me", body=reply).execute()
        return f"Successfully reply {message_id}"
    except Exception as e:
        return f"An Error Occurred Error: {e}"

class MarkSpam(BaseModel):
    message_id: str = Field(..., description="The ID of the email message to mark as spam.")

@tool_decorator("mark_spam", args_schema=MarkSpam)
def mark_spam(message_id: str) -> str:
    """
    Use this tool to mark an email as spam.
    """
    try:
        global gmail_service
        gmail_service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["INBOX"], "addLabelIds": ["SPAM"]},
        ).execute()
        return f"Email with ID: {message_id} marked as spam."
    except Exception as e:
        return f"An error occurred: {e}"

class DraftEmail(BaseModel):
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")
    to: str = Field(..., description="The recipient email address.")

@tool_decorator("draft_email", args_schema=DraftEmail)
def draft_email(subject: str, body: str, to: str) -> str:
    """
    Use this tool to draft an email with the given subject and body content.
    """
    try:
        global gmail_service

        # Create a MIMEText object to represent the email
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        # Encode the message in base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Create the payload for the Gmail API
        payload = {"message": {"raw": raw_message}}

        # Draft the email
        gmail_service.users().drafts().create(userId="me", body=payload).execute()

        return "Email drafted successfully!"
    except HttpError as e:
        return f"An error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

class SendEmail(BaseModel):
    to: str = Field(..., description="The recipient's email address.")
    subject: str = Field(..., description="The subject of the email.")
    body: str = Field(..., description="The body content of the email.")

@tool_decorator("send_email", args_schema=SendEmail)
def send_email(to: str, subject: str, body: str) -> str:
    """
    Use this tool to send an email with the given subject and body content.
    """
    try:
        global gmail_service

        # Create a MIMEText object to represent the email
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject

        # Encode the message in base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Create the payload for the Gmail API
        payload = {"raw": raw_message}

        # Send the email
        gmail_service.users().messages().send(userId="me", body=payload).execute()

        return "Email sent successfully!"
    except HttpError as e:
        return f"An error occurred: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

class MarkRead(BaseModel):
    message_id: str = Field(..., description="The ID of the email message to mark as read.")

@tool_decorator("mark_read", args_schema=MarkRead)
def mark_read(message_id: str) -> str:
    """
    Use this tool to mark an email as read.
    """
    try:
        global gmail_service
        gmail_service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        return f"Email with ID: {message_id} marked as read."
    except Exception as e:
        return f"An error occurred: {e}"

class SearchEmails(BaseModel):
    query: str = Field(..., description="Email search query string, a query to search for emails.")

@tool_decorator("search_emails", args_schema=SearchEmails)
def search_emails(query: str) -> list[dict]:
    """
    Use this tool to search for emails based on a query string.
    """
    global gmail_service
    results = gmail_service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    email_data = []

    for msg in messages:
        message = (
            gmail_service.users().messages().get(userId="me", id=msg["id"]).execute()
        )
        email_data.append({"id": msg["id"], "snippet": message["snippet"]})

    return email_data

class StarEmail(BaseModel):
    message_id: str = Field(..., description="The ID of the email message to star.")

@tool_decorator("star_email", args_schema=StarEmail)
def star_email(message_id: str) -> str:
    """
    Use this tool to star an email.
    """
    global gmail_service
    gmail_service.users().messages().modify(
        userId="me", id=message_id, body={"addLabelIds": ["STARRED"]}
    ).execute()

class UnstarEmail(BaseModel):
    message_id: str = Field(..., description="The ID of the email message to unstar.")

@tool_decorator("unstar_email", args_schema=UnstarEmail)
def unstar_email(message_id: str) -> str:
    """
    Use this tool to unstar an email.
    """
    global gmail_service
    gmail_service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["STARRED"]}
    ).execute()

class PermanentlyDeleteEmail(BaseModel):
    message_id: str = Field(..., description="The ID of the email message to delete.")

@tool_decorator("permanently_delete_email", args_schema=PermanentlyDeleteEmail)
def permanently_delete_email(message_id: str):
    """\
    Use this tool to permanently delete an email.
    """
    try:
        gmail_service.users().messages().delete(userId="me", id=message_id).execute()
        return f"Message with id: {message_id} deleted successfully."
    except Exception as error:
        return f"An error occurred: {error}"

class TrashEmail(BaseModel):
    message_id: str = Field(..., description="The ID of the email message to delete.")

@tool_decorator("trash_email", args_schema=TrashEmail)
def trash_email(message_id: str):
    """\
    Use this tool to put emails in trash.
    """
    try:
        gmail_service.users().messages().trash(userId="me", id=message_id).execute()
        return f"Message with id: {message_id} has puted in trash successfully."
    except Exception as error:
        return f"An error occurred: {error}"


def get_full_thread(thread_id):
    thread = gmail_service.users().threads().get(userId="me", id=thread_id).execute()
    messages = thread.get("messages", [])
    conversation = []

    for msg in messages:
        message_data = {}
        payload = msg["payload"]
        headers = payload["headers"]

        # Extracting subject and sender from headers
        for header in headers:
            if header["name"] == "Subject":
                message_data["subject"] = header["value"]
            if header["name"] == "From":
                message_data["from"] = header["value"]
            if header["name"] == "Date":
                message_data["date"] = header["value"]

        # Extracting message snippet (preview)
        message_data["snippet"] = msg.get("snippet", "")

        # Handling multipart emails
        parts = payload.get("parts", [])
        message_body = ""

        for part in parts:
            if part.get("mimeType") == "text/plain":
                message_body = part.get("body", {}).get("data", "")
                message_body = base64.urlsafe_b64decode(message_body).decode("utf-8")

        if message_body:
            message_data["body"] = message_body
        else:
            # Fallback to snippet if body not found
            message_data["body"] = msg.get("snippet", "")

        conversation.append(message_data)

    return conversation


def get_email_body(msg: dict) -> str:
    """
    Extracts the email body/content from the message payload.

    Args:
        msg (dict): The Gmail message object.

    Returns:
        str: The extracted email content.
    """
    payload = msg["payload"]
    parts = payload.get("parts", [])
    body = ""

    if "data" in payload["body"]:
        # If the message body is plain text or HTML encoded
        body = payload["body"]["data"]
    else:
        # Handle multipart emails
        for part in parts:
            if part["mimeType"] == "text/plain":
                body = part["body"][
                    "data"
                ]  # You may need to decode the base64-encoded body here

    return body


__all__ = [
    "reply_email",
    "mark_spam",
    "draft_email",
    "send_email",
    "search_emails",
    "mark_read",
    "star_email",
    "unstar_email",
    "reply_email",
    "permanently_delete_email",
    "trash_email",
]
