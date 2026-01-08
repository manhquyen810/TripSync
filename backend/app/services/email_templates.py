"""Email templates for different notification types"""

def get_base_template(title: str, content: str) -> str:
    """Base email template wrapper"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
            .container {{ background-color: white; padding: 40px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ color: #4F46E5; font-size: 28px; margin-bottom: 20px; text-align: center; }}
            .icon {{ font-size: 48px; text-align: center; margin-bottom: 20px; }}
            .content {{ color: #333; line-height: 1.8; font-size: 16px; }}
            .button {{ background-color: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
            .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; text-align: center; }}
            .highlight {{ background-color: #FEF3C7; padding: 15px; border-radius: 5px; margin: 15px 0; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">🌍 TripSync</div>
            {content}
            <div class="footer">
                © 2026 TripSync. All rights reserved.<br>
                This is an automated notification. Please do not reply to this email.
            </div>
        </div>
    </body>
    </html>
    """

def get_otp_email(otp_code: str) -> str:
    """OTP verification email"""
    content = f"""
        <div class="icon">🔐</div>
        <div class="content">
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Use the code below to continue:</p>
            <div class="highlight" style="text-align: center; font-size: 32px; letter-spacing: 5px;">
                {otp_code}
            </div>
            <p>This code will expire in <strong>5 minutes</strong>.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </div>
    """
    return get_base_template("Password Reset", content)

def get_trip_invite_email(trip_name: str, inviter_name: str, invite_code: str) -> str:
    """Trip invitation email"""
    content = f"""
        <div class="icon">✈️</div>
        <div class="content">
            <h2>You're Invited to a Trip!</h2>
            <p><strong>{inviter_name}</strong> has invited you to join the trip:</p>
            <div class="highlight" style="text-align: center; font-size: 24px;">
                📍 {trip_name}
            </div>
            <p>Use this invite code to join:</p>
            <div class="highlight" style="text-align: center; font-size: 28px; letter-spacing: 3px;">
                {invite_code}
            </div>
            <p style="text-align: center;">
                <a href="#" class="button">Open TripSync App</a>
            </p>
        </div>
    """
    return get_base_template("Trip Invitation", content)

def get_expense_added_email(trip_name: str, payer_name: str, amount: float, currency: str, description: str) -> str:
    """New expense notification email"""
    content = f"""
        <div class="icon">💰</div>
        <div class="content">
            <h2>New Expense Added</h2>
            <p>A new expense has been added to <strong>{trip_name}</strong>:</p>
            <div class="highlight">
                <p style="margin: 5px 0;"><strong>Amount:</strong> {amount:,.2f} {currency}</p>
                <p style="margin: 5px 0;"><strong>Paid by:</strong> {payer_name}</p>
                <p style="margin: 5px 0;"><strong>Description:</strong> {description}</p>
            </div>
            <p style="text-align: center;">
                <a href="#" class="button">View Details</a>
            </p>
        </div>
    """
    return get_base_template("New Expense", content)

def get_payment_received_email(trip_name: str, payer_name: str, amount: float, currency: str) -> str:
    """Payment received notification email"""
    content = f"""
        <div class="icon">✅</div>
        <div class="content">
            <h2>Payment Received!</h2>
            <p><strong>{payer_name}</strong> has settled a debt in <strong>{trip_name}</strong>:</p>
            <div class="highlight" style="text-align: center;">
                <p style="font-size: 36px; margin: 10px 0; color: #10B981;">
                    {amount:,.2f} {currency}
                </p>
            </div>
            <p>Your balance has been updated.</p>
            <p style="text-align: center;">
                <a href="#" class="button">View Balances</a>
            </p>
        </div>
    """
    return get_base_template("Payment Received", content)

def get_trip_joined_email(trip_name: str, member_name: str) -> str:
    """Member joined trip notification email"""
    content = f"""
        <div class="icon">👥</div>
        <div class="content">
            <h2>New Member Joined!</h2>
            <p><strong>{member_name}</strong> has joined <strong>{trip_name}</strong>!</p>
            <p>You can now collaborate on planning activities, sharing expenses, and more.</p>
            <p style="text-align: center;">
                <a href="#" class="button">View Trip</a>
            </p>
        </div>
    """
    return get_base_template("New Member", content)

def get_document_expiring_email(trip_name: str, document_name: str, expiry_date: str) -> str:
    """Document expiring notification email"""
    content = f"""
        <div class="icon">⚠️</div>
        <div class="content">
            <h2>Document Expiring Soon</h2>
            <p>A document in <strong>{trip_name}</strong> is expiring soon:</p>
            <div class="highlight" style="border-left: 4px solid #EF4444;">
                <p style="margin: 5px 0;"><strong>Document:</strong> {document_name}</p>
                <p style="margin: 5px 0;"><strong>Expiry Date:</strong> {expiry_date}</p>
            </div>
            <p>Please renew this document before your trip.</p>
            <p style="text-align: center;">
                <a href="#" class="button">View Document</a>
            </p>
        </div>
    """
    return get_base_template("Document Expiring", content)

def get_reminder_email(trip_name: str, reminder_text: str) -> str:
    """General reminder email"""
    content = f"""
        <div class="icon">🔔</div>
        <div class="content">
            <h2>Reminder</h2>
            <p>You have a reminder for <strong>{trip_name}</strong>:</p>
            <div class="highlight">
                {reminder_text}
            </div>
            <p style="text-align: center;">
                <a href="#" class="button">View Trip</a>
            </p>
        </div>
    """
    return get_base_template("Reminder", content)
