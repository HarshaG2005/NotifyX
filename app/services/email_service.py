import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email via Gmail SMTP"""
    
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = SMTP_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add body
        message.attach(MIMEText(body, "plain"))
        
        # Send via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure connection
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Email sent to {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False