from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from fastapi import HTTPException
import httpx

from app.core.config import settings



BREVO_API_KEY = settings.BREVO_API_KEY

# -------------------------------------------------
# with custom email template
# -------------------------------------------------

class EmailRecipient(BaseModel):
    email: EmailStr
    name: str = ""

class EmailRawHTMLContent(BaseModel):
    subject: str
    html_content: str
    sender_name: str = "Mimipoint"
    sender_email: EmailStr = "accounts@mimipoint.com"

base_url = "https://api.brevo.com/v3/smtp/email"
base_headers = {
    "Content-Type": "application/json",
    "api-key": BREVO_API_KEY,
}

async def send_html_email(
    recipients: List[EmailRecipient],
    content: EmailRawHTMLContent
) -> bool:
    url = base_url
    headers = base_headers
    payload = {
        "sender": {
            "name": content.sender_name,
            "email": content.sender_email
        },
        "to": [{"email": r.email, "name": r.name or r.email.split('@')[0]} for r in recipients],
        "subject": content.subject,
        "htmlContent": content.html_content  # Your raw HTML here
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return True
        else:
            raise HTTPException(status_code=response.status_code, detail=response.json())


# -------------------------------------------------
# with Brevo email template
# -------------------------------------------------

class EmailTemplateContent(BaseModel):
    template_id: int  # Brevo template ID
    subject: Optional[str] = None  # Optional override
    sender_name: str = "Mimipoint"
    sender_email: EmailStr = "accounts@mimipoint.com"
    params: Dict[str, Any]  # Dynamic parameters for the template

async def send_template_email(
    recipients: List[EmailRecipient],
    content: EmailTemplateContent
) -> bool:
    url = base_url
    headers = base_headers
    payload = {
        "sender": {
            "name": content.sender_name,
            "email": content.sender_email
        },
        "to": [{"email": r.email, "name": r.name or r.email.split('@')[0]} for r in recipients],
        "templateId": content.template_id,
        "params": content.params,
    }

    if content.subject:
        payload["subject"] = content.subject  # Optional: override subject from template

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            return True
        else:
            raise HTTPException(status_code=response.status_code, detail=response.json())