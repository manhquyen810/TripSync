from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os
import logging
from app.services import email_templates

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL")
        self.client = SendGridAPIClient(self.api_key) if self.api_key else None
    
    def send_notification_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> bool:
        """Send notification email with plain text body"""
        if not self.client:
            logger.warning("SendGrid not configured. Skipping email.")
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=self._get_simple_template(subject, body)
            )
            
            response = self.client.send(message)
            logger.info(f"✅ Email sent to {to_email}: {response.status_code}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        """Send OTP verification email"""
        if not self.client:
            logger.warning("SendGrid not configured. Skipping email.")
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject="Password Reset - TripSync",
                html_content=email_templates.get_otp_email(otp_code)
            )
            response = self.client.send(message)
            logger.info(f"✅ OTP email sent to {to_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Failed to send OTP email: {e}")
            return False
    
    def send_trip_invite_email(self, to_email: str, trip_name: str, inviter_name: str, invite_code: str) -> bool:
        """Send trip invitation email"""
        if not self.client:
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f"You're invited to {trip_name}!",
                html_content=email_templates.get_trip_invite_email(trip_name, inviter_name, invite_code)
            )
            response = self.client.send(message)
            logger.info(f"✅ Invite email sent to {to_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Failed to send invite email: {e}")
            return False
    
    def send_expense_email(self, to_email: str, trip_name: str, payer_name: str, amount: float, currency: str, description: str) -> bool:
        """Send new expense notification email"""
        if not self.client:
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f"New expense in {trip_name}",
                html_content=email_templates.get_expense_added_email(trip_name, payer_name, amount, currency, description)
            )
            response = self.client.send(message)
            logger.info(f"✅ Expense email sent to {to_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Failed to send expense email: {e}")
            return False
    
    def send_payment_email(self, to_email: str, trip_name: str, payer_name: str, amount: float, currency: str) -> bool:
        """Send payment received notification email"""
        if not self.client:
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f"Payment received in {trip_name}",
                html_content=email_templates.get_payment_received_email(trip_name, payer_name, amount, currency)
            )
            response = self.client.send(message)
            logger.info(f"✅ Payment email sent to {to_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Failed to send payment email: {e}")
            return False
    
    def send_member_joined_email(self, to_email: str, trip_name: str, member_name: str) -> bool:
        """Send member joined notification email"""
        if not self.client:
            return False
        
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=f"{member_name} joined {trip_name}",
                html_content=email_templates.get_trip_joined_email(trip_name, member_name)
            )
            response = self.client.send(message)
            logger.info(f"✅ Member joined email sent to {to_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"❌ Failed to send member joined email: {e}")
            return False
    
    def _get_simple_template(self, subject: str, body: str) -> str:
        """Simple email template for generic messages"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                .header {{ color: #4F46E5; font-size: 24px; margin-bottom: 20px; }}
                .content {{ color: #333; line-height: 1.6; }}
                .footer {{ margin-top: 30px; color: #666; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">🌍 TripSync</div>
                <div class="content">
                    <h2>{subject}</h2>
                    <p>{body}</p>
                </div>
                <div class="footer">
                    © 2026 TripSync. All rights reserved.
                </div>
            </div>
        </body>
        </html>
        """

email_service = EmailService()
