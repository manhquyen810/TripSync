import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.config import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL


def send_otp_email(to_email: str, otp_code: str) -> bool:
    """Send OTP code via email using SendGrid"""
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        
        from_email = Email(SENDGRID_FROM_EMAIL)
        to_email = To(to_email)
        subject = "TripSync - Mã OTP đặt lại mật khẩu"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #4CAF50;">TripSync - Đặt lại mật khẩu</h2>
                <p>Bạn đã yêu cầu đặt lại mật khẩu. Sử dụng mã OTP sau để tiếp tục:</p>
                <div style="background-color: #f5f5f5; padding: 15px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {otp_code}
                </div>
                <p style="color: #666;">Mã OTP này sẽ hết hạn sau 5 phút.</p>
                <p style="color: #999; font-size: 12px;">Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
            </body>
        </html>
        """
        
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content)
        
        response = sg.client.mail.send.post(request_body=mail.get())
        
        return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False
