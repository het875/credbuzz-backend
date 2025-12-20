"""
Email Service
=============
Service for sending emails including OTP verification emails.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def send_otp_email(email: str, otp_code: str, user_name: str = None) -> bool:
    """
    Send OTP verification email to user.
    
    Args:
        email: Recipient email address
        otp_code: The OTP code to send
        user_name: Optional user's name for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "CredBuzzPay - Your Verification Code"
    
    # Plain text version
    plain_message = f"""
Welcome to CredBuzzPay!

Your verification code is: {otp_code}

Enter this code to complete your verification.

This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.

Thanks,
The CredBuzzPay Team
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">CredBuzzPay</h1>
            <p style="color: #e8e8e8; margin: 10px 0 0 0; font-size: 14px;">Secure Payment Solutions</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 30px;">
            <h2 style="color: #333333; margin: 0 0 20px 0;">Welcome{f' {user_name}' if user_name else ''}!</h2>
            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                Your verification code is:
            </p>
            
            <!-- OTP Box -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; padding: 25px; text-align: center; margin: 0 0 30px 0;">
                <span style="color: #ffffff; font-size: 36px; font-weight: bold; letter-spacing: 8px; font-family: monospace;">
                    {otp_code}
                </span>
            </div>
            
            <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0 0 15px 0;">
                Enter this code to complete your verification.
            </p>
            
            <p style="color: #999999; font-size: 13px; line-height: 1.6; margin: 0 0 30px 0;">
                ⏱️ This code will expire in <strong>{settings.OTP_EXPIRY_MINUTES} minutes</strong>.
            </p>
            
            <hr style="border: none; border-top: 1px solid #eeeeee; margin: 30px 0;">
            
            <p style="color: #999999; font-size: 12px; line-height: 1.6; margin: 0;">
                If you didn't request this code, please ignore this email. Your account is safe.
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
            <p style="color: #999999; font-size: 12px; margin: 0;">
                © 2025 CredBuzzPay. All rights reserved.
            </p>
            <p style="color: #999999; font-size: 11px; margin: 10px 0 0 0;">
                This is an automated message. Please do not reply to this email.
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    try:
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send(fail_silently=False)
        
        logger.info(f"OTP email sent successfully to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False


def send_welcome_email(email: str, user_name: str) -> bool:
    """
    Send welcome email after registration.
    """
    subject = "Welcome to CredBuzzPay!"
    
    plain_message = f"""
Hi {user_name},

Welcome to CredBuzzPay! We're excited to have you on board.

Your account has been created successfully. You can now:
- Pay bills conveniently
- Transfer money securely
- Manage your finances easily

If you have any questions, feel free to reach out to our support team.

Thanks,
The CredBuzzPay Team
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False


def send_password_reset_email(email: str, reset_token: str, user_name: str = None) -> bool:
    """
    Send password reset email with reset token.
    """
    subject = "CredBuzzPay - Password Reset Request"
    
    plain_message = f"""
Hi{f' {user_name}' if user_name else ''},

We received a request to reset your password.

Your password reset code is: {reset_token}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

Thanks,
The CredBuzzPay Team
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return False
