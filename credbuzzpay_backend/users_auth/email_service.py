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
    Send OTP verification email to user with modern, professional design.
    
    Args:
        email: Recipient email address
        otp_code: The OTP code to send
        user_name: Optional user's name for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "🔐 CredBuzzPay - Your Verification Code"
    
    # Plain text version
    plain_message = f"""
Hello{f' {user_name}' if user_name else ''}!

Welcome to CredBuzzPay - Your Trusted Payment Partner

Your verification code is: {otp_code}

Please enter this code to complete your verification and secure your account.

IMPORTANT:
• This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes
• Do not share this code with anyone
• CredBuzzPay will never ask for your OTP via phone or SMS

If you didn't request this code, please ignore this email and ensure your account is secure.

Need help? Contact our support team.

Best regards,
The CredBuzzPay Team

---
© 2025 CredBuzzPay. All rights reserved.
This is an automated message. Please do not reply to this email.
    """.strip()
    
    # HTML version - Modern, responsive design with brand colors
    # Brand Colors:
    # Teal Primary: #00A38D
    # Teal Secondary: #00D2B8
    # Orange Accent: #FF8C00
    # Navy: #1A233A
    # Security Dark: #0F172A
    # Security Blue: #1E40AF
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>CredBuzzPay - Verification Code</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, sans-serif !important;}}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0f2f5; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <!-- Main Container -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header with Brand - Teal Gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 50%, #FF8C00 100%); padding: 40px 30px; text-align: center;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <div style="background-color: rgba(255, 255, 255, 0.15); border-radius: 12px; padding: 15px 25px; display: inline-block; backdrop-filter: blur(10px);">
                                            <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">CredBuzzPay</h1>
                                        </div>
                                        <p style="color: #ffffff; margin: 15px 0 0 0; font-size: 15px; font-weight: 500;">🔐 Secure Payment Solutions</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 50px 40px;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <!-- Greeting -->
                                <tr>
                                    <td style="padding-bottom: 30px;">
                                        <h2 style="color: #1A233A; margin: 0 0 12px 0; font-size: 26px; font-weight: 700; line-height: 1.3;">Hello{f' {user_name}' if user_name else ''}! 👋</h2>
                                        <p style="color: #4B5563; font-size: 16px; line-height: 1.6; margin: 0;">Welcome to CredBuzzPay! To complete your verification, please use the code below:</p>
                                    </td>
                                </tr>
                                
                                <!-- OTP Code Box - Teal Primary -->
                                <tr>
                                    <td align="center" style="padding: 0 0 35px 0;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td align="center" style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 100%); border-radius: 12px; padding: 35px 20px; box-shadow: 0 8px 20px rgba(0, 163, 141, 0.25);">
                                                    <p style="color: #ffffff; margin: 0 0 12px 0; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Your Verification Code</p>
                                                    <div style="background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 20px; backdrop-filter: blur(10px);">
                                                        <span style="color: #ffffff; font-size: 42px; font-weight: 800; letter-spacing: 12px; font-family: 'Courier New', Courier, monospace; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);">{otp_code}</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Timer Info - Orange Accent -->
                                <tr>
                                    <td align="center" style="padding-bottom: 35px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="background-color: #FFF3E0; border-radius: 8px; padding: 16px 24px; border-left: 4px solid #FF8C00;">
                                            <tr>
                                                <td>
                                                    <p style="color: #7A3D00; margin: 0; font-size: 14px; font-weight: 600; line-height: 1.5;">
                                                        ⏰ <strong>Expires in {settings.OTP_EXPIRY_MINUTES} minutes</strong> - Please use it quickly!
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Security Tips - Navy Background -->
                                <tr>
                                    <td style="background-color: #F5F5F7; border-left: 4px solid #00A38D; border-radius: 10px; padding: 25px;">
                                        <h3 style="color: #1A233A; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">🔒 Security Tips</h3>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Never share your OTP with anyone</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ CredBuzzPay will never ask for your code via phone</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ If you didn't request this, ignore this email</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Divider -->
                                <tr>
                                    <td style="padding: 35px 0;">
                                        <div style="border-top: 2px solid #E5E7EB;"></div>
                                    </td>
                                </tr>
                                
                                <!-- Help Section -->
                                <tr>
                                    <td align="center">
                                        <p style="color: #9CA3AF; margin: 0 0 10px 0; font-size: 13px; line-height: 1.5;">Need help? We're here for you!</p>
                                        <p style="color: #4B5563; margin: 0; font-size: 14px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer - Navy with Teal Accent -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay</p>
                                        <p style="color: #4B5563; margin: 0 0 15px 0; font-size: 12px; line-height: 1.5;">Your Trusted Payment Partner</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.<br>
                                            This is an automated message. Please do not reply.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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


def send_password_reset_otp_email(email: str, otp_code: str, user_name: str = None) -> bool:
    """
    Send Password Reset OTP email with modern design matching brand theme.
    Uses same color scheme but different content for password reset context.
    
    Args:
        email: Recipient email address
        otp_code: The 6-digit OTP code
        user_name: Optional user's name for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "🔒 CredBuzzPay - Password Reset Code"
    
    # Plain text version
    plain_message = f"""
Hello{f' {user_name}' if user_name else ''}!

Password Reset Request for Your CredBuzzPay Account

We received a request to reset your password. Use the code below to reset your password:

Reset Code: {otp_code}

IMPORTANT INFORMATION:
• This code will expire in 10 minutes
• Do not share this code with anyone
• If you didn't request this reset, please ignore this email
• Your password will remain unchanged if you don't use this code

Security Tips:
- Never share your reset code with anyone
- CredBuzzPay will never ask for your password via email
- If you're concerned about your account security, contact us immediately

Need Help?
Contact our support team: support@credbuzzpay.com

Best regards,
The CredBuzzPay Security Team

---
© 2026 CredBuzzPay. All rights reserved.
This is an automated message. Please do not reply to this email.
    """.strip()
    
    # HTML version - Following same brand theme as registration but with password reset context
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>CredBuzzPay - Password Reset Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f0f2f5; -webkit-font-smoothing: antialiased;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <!-- Main Container -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header with Brand - Teal Gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 50%, #FF8C00 100%); padding: 40px 30px; text-align: center;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <div style="background-color: rgba(255, 255, 255, 0.15); border-radius: 12px; padding: 15px 25px; display: inline-block; backdrop-filter: blur(10px);">
                                            <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">CredBuzzPay</h1>
                                        </div>
                                        <p style="color: #ffffff; margin: 15px 0 0 0; font-size: 15px; font-weight: 500;">🔒 Secure Password Reset</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 50px 40px;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <!-- Greeting -->
                                <tr>
                                    <td style="padding-bottom: 30px;">
                                        <h2 style="color: #1A233A; margin: 0 0 12px 0; font-size: 26px; font-weight: 700; line-height: 1.3;">Hello{f' {user_name}' if user_name else ''}! 👋</h2>
                                        <p style="color: #4B5563; font-size: 16px; line-height: 1.6; margin: 0;">We received a request to reset your password. Use the code below to proceed:</p>
                                    </td>
                                </tr>
                                
                                <!-- OTP Code Box - Teal Primary -->
                                <tr>
                                    <td align="center" style="padding: 0 0 35px 0;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td align="center" style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 100%); border-radius: 12px; padding: 35px 20px; box-shadow: 0 8px 20px rgba(0, 163, 141, 0.25);">
                                                    <p style="color: #ffffff; margin: 0 0 12px 0; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Your Password Reset Code</p>
                                                    <div style="background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 20px; backdrop-filter: blur(10px);">
                                                        <span style="color: #ffffff; font-size: 42px; font-weight: 800; letter-spacing: 12px; font-family: 'Courier New', Courier, monospace; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);">{otp_code}</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Timer Info - Orange Accent -->
                                <tr>
                                    <td align="center" style="padding-bottom: 35px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="background-color: #FFF3E0; border-radius: 8px; padding: 16px 24px; border-left: 4px solid #FF8C00;">
                                            <tr>
                                                <td>
                                                    <p style="color: #7A3D00; margin: 0; font-size: 14px; font-weight: 600; line-height: 1.5;">
                                                        ⏰ <strong>Expires in 10 minutes</strong> - Please use it quickly!
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Security Warning - Navy Background -->
                                <tr>
                                    <td style="background-color: #FEF2F2; border-left: 4px solid #EF4444; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                        <h3 style="color: #991B1B; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">⚠️ Didn't Request This?</h3>
                                        <p style="color: #7F1D1D; margin: 0; font-size: 14px; line-height: 1.6;">
                                            If you didn't request a password reset, please ignore this email. Your password will remain unchanged. If you're concerned about your account security, contact us immediately.
                                        </p>
                                    </td>
                                </tr>
                                
                                <!-- Security Tips - Navy Background -->
                                <tr>
                                    <td style="background-color: #F5F5F7; border-left: 4px solid #00A38D; border-radius: 10px; padding: 25px;">
                                        <h3 style="color: #1A233A; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">🔒 Security Tips</h3>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Never share your reset code with anyone</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ CredBuzzPay will never ask for your password via email</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Use a strong, unique password for your account</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Support Section -->
                    <tr>
                        <td style="background-color: #F9FAFB; padding: 25px 40px; border-top: 1px solid #E5E7EB;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 8px 0; font-size: 13px; line-height: 1.5;">Need assistance?</p>
                                        <p style="color: #00A38D; margin: 0; font-size: 14px; font-weight: 600;">📧 support@credbuzzpay.com</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer - Navy with Teal Accent -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay Security Team</p>
                                        <p style="color: #4B5563; margin: 0 0 15px 0; font-size: 12px; line-height: 1.5;">Protecting Your Payment Journey</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.<br>
                                            This is an automated message. Please do not reply.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
        
        logger.info(f"Password reset OTP email sent successfully to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset OTP email to {email}: {str(e)}")
        return False


def send_welcome_email(email: str, user_name: str) -> bool:
    """
    Send welcome email after registration with modern, engaging design.
    """
    subject = "🎉 Welcome to CredBuzzPay - Let's Get Started!"
    
    plain_message = f"""
Hello {user_name}!

Welcome to CredBuzzPay! 🎉

We're thrilled to have you join our community of smart payment users.

Your account has been created successfully, and you're all set to start using CredBuzzPay!

What you can do with CredBuzzPay:
✓ Pay bills instantly - Electricity, water, mobile recharge & more
✓ Transfer money securely - Send money to friends and family
✓ Manage your finances - Track expenses and payments in one place
✓ Quick & Easy - Simple interface for hassle-free payments
✓ Secure & Reliable - Bank-grade security for your transactions

Get Started:
1. Log in to your account
2. Complete your KYC verification for higher limits
3. Add your payment methods
4. Start making payments!

Need Help?
Our support team is always ready to assist you.
Email: support@credbuzzpay.com

Thank you for choosing CredBuzzPay!

Best regards,
The CredBuzzPay Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version - Modern, engaging welcome email
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to CredBuzzPay</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">
                    <!-- Celebration Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%); padding: 50px 30px; text-align: center; position: relative;">
                            <div style="font-size: 48px; margin-bottom: 15px;">🎉</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 32px; font-weight: 700;">Welcome to CredBuzzPay!</h1>
                            <p style="color: #E0E7FF; margin: 0; font-size: 16px; font-weight: 500;">Your journey to seamless payments starts here</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <!-- Greeting -->
                            <h2 style="color: #1F2937; margin: 0 0 15px 0; font-size: 24px; font-weight: 700;">Hi {user_name}! 👋</h2>
                            <p style="color: #4B5563; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                We're absolutely thrilled to have you join our community! Your account is all set up and ready to go.
                            </p>
                            
                            <!-- Features Grid -->
                            <h3 style="color: #1F2937; margin: 0 0 20px 0; font-size: 18px; font-weight: 700;">What You Can Do 🚀</h3>
                            
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 30px;">
                                <!-- Feature 1 -->
                                <tr>
                                    <td style="padding: 15px; background-color: #EEF2FF; border-radius: 10px; margin-bottom: 12px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="40" style="vertical-align: top;">
                                                    <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #4F46E5, #7C3AED); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; text-align: center; line-height: 36px;">💳</div>
                                                </td>
                                                <td style="padding-left: 15px; vertical-align: top;">
                                                    <p style="color: #1F2937; margin: 0 0 4px 0; font-size: 15px; font-weight: 700;">Pay Bills Instantly</p>
                                                    <p style="color: #6B7280; margin: 0; font-size: 13px; line-height: 1.5;">Electricity, water, mobile recharge & more</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <tr><td style="height: 12px;"></td></tr>
                                
                                <!-- Feature 2 -->
                                <tr>
                                    <td style="padding: 15px; background-color: #F3E8FF; border-radius: 10px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="40" style="vertical-align: top;">
                                                    <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #7C3AED, #EC4899); border-radius: 8px; font-size: 20px; text-align: center; line-height: 36px;">💸</div>
                                                </td>
                                                <td style="padding-left: 15px; vertical-align: top;">
                                                    <p style="color: #1F2937; margin: 0 0 4px 0; font-size: 15px; font-weight: 700;">Transfer Money Securely</p>
                                                    <p style="color: #6B7280; margin: 0; font-size: 13px; line-height: 1.5;">Send money to friends and family instantly</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <tr><td style="height: 12px;"></td></tr>
                                
                                <!-- Feature 3 -->
                                <tr>
                                    <td style="padding: 15px; background-color: #FCE7F3; border-radius: 10px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="40" style="vertical-align: top;">
                                                    <div style="width: 36px; height: 36px; background: linear-gradient(135deg, #EC4899, #F59E0B); border-radius: 8px; font-size: 20px; text-align: center; line-height: 36px;">📊</div>
                                                </td>
                                                <td style="padding-left: 15px; vertical-align: top;">
                                                    <p style="color: #1F2937; margin: 0 0 4px 0; font-size: 15px; font-weight: 700;">Manage Your Finances</p>
                                                    <p style="color: #6B7280; margin: 0; font-size: 13px; line-height: 1.5;">Track all your expenses in one place</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Quick Start Guide -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #F0FDF4, #DBEAFE); border-radius: 12px; padding: 25px; margin-bottom: 30px;">
                                <tr>
                                    <td>
                                        <h3 style="color: #1F2937; margin: 0 0 15px 0; font-size: 18px; font-weight: 700;">🚀 Quick Start Guide</h3>
                                        <ol style="color: #374151; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                                            <li style="margin-bottom: 8px;"><strong>Log in</strong> to your account</li>
                                            <li style="margin-bottom: 8px;"><strong>Complete KYC</strong> verification for higher limits</li>
                                            <li style="margin-bottom: 8px;"><strong>Add payment methods</strong></li>
                                            <li style="margin-bottom: 0;"><strong>Start making payments!</strong></li>
                                        </ol>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 30px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 10px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3); transition: all 0.3s;">Get Started Now →</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Security Note -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
                                <tr>
                                    <td>
                                        <p style="color: #92400E; margin: 0 0 8px 0; font-size: 14px; font-weight: 700;">🔐 Your Security Matters</p>
                                        <p style="color: #92400E; margin: 0; font-size: 13px; line-height: 1.5;">
                                            We use bank-grade security to protect your data and transactions. Your information is always safe with us.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Support Section -->
                            <div style="text-align: center; padding: 20px; background-color: #F9FAFB; border-radius: 10px;">
                                <p style="color: #6B7280; margin: 0 0 12px 0; font-size: 14px;">Need help getting started?</p>
                                <p style="color: #1F2937; margin: 0; font-size: 15px; font-weight: 600;">
                                    <a href="mailto:support@credbuzzpay.com" style="color: #4F46E5; text-decoration: none;">Contact our Support Team →</a>
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 1px solid #E5E7EB;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 12px 0; font-size: 14px; font-weight: 600;">Thank you for choosing CredBuzzPay!</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 12px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.<br>
                                            This email was sent to {email}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """
    
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
    Send password reset email with reset token and modern design.
    """
    subject = "🔑 CredBuzzPay - Password Reset Request"
    
    plain_message = f"""
Hello{f' {user_name}' if user_name else ''},

Password Reset Request for Your CredBuzzPay Account

We received a request to reset your password. Use the code below to reset your password:

Reset Code: {reset_token}

IMPORTANT INFORMATION:
• This code will expire in 24 hours
• Do not share this code with anyone
• If you didn't request this reset, please ignore this email
• Your password will remain unchanged if you don't use this code

Security Tips:
- Never share your reset code with anyone
- CredBuzzPay will never ask for your password via email
- If you're concerned about your account security, contact us immediately

Need Help?
Contact our support team: support@credbuzzpay.com

Best regards,
The CredBuzzPay Security Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version - Modern password reset email
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset - CredBuzzPay</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">
                    <!-- Security Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #DC2626 0%, #EF4444 50%, #F59E0B 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">🔐</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">Password Reset Request</h1>
                            <p style="color: #FEE2E2; margin: 0; font-size: 15px; font-weight: 500;">Secure your CredBuzzPay account</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <!-- Greeting -->
                            <h2 style="color: #1F2937; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">Hello{f' {user_name}' if user_name else ''}!</h2>
                            <p style="color: #4B5563; font-size: 15px; line-height: 1.6; margin: 0 0 25px 0;">
                                We received a request to reset the password for your CredBuzzPay account. Use the code below to proceed:
                            </p>
                            
                            <!-- Reset Code Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 30px;">
                                <tr>
                                    <td align="center" style="background: linear-gradient(135deg, #DC2626, #EF4444); border-radius: 12px; padding: 30px 20px; box-shadow: 0 8px 20px rgba(220, 38, 38, 0.25);">
                                        <p style="color: #FEE2E2; margin: 0 0 10px 0; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Password Reset Code</p>
                                        <div style="background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 18px; backdrop-filter: blur(10px); margin-bottom: 15px;">
                                            <span style="color: #ffffff; font-size: 28px; font-weight: 800; letter-spacing: 4px; font-family: 'Courier New', Courier, monospace;">{reset_token}</span>
                                        </div>
                                        <p style="color: #FECACA; margin: 0; font-size: 12px;">⏰ Valid for 24 hours</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Instructions -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #1E40AF; margin: 0 0 10px 0; font-size: 14px; font-weight: 700;">📝 How to Reset Your Password:</p>
                                        <ol style="color: #1E40AF; margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8;">
                                            <li style="margin-bottom: 6px;">Go to the password reset page</li>
                                            <li style="margin-bottom: 6px;">Enter the code shown above</li>
                                            <li style="margin-bottom: 6px;">Create your new secure password</li>
                                            <li style="margin-bottom: 0;">Confirm and save your changes</li>
                                        </ol>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Security Warning -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #FEF2F2; border: 2px solid #FCA5A5; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #991B1B; margin: 0 0 12px 0; font-size: 15px; font-weight: 700;">⚠️ Important Security Notice</p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #B91C1C; margin: 0; font-size: 13px; line-height: 1.5;">• Never share your reset code with anyone</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #B91C1C; margin: 0; font-size: 13px; line-height: 1.5;">• CredBuzzPay will NEVER ask for your code via phone or SMS</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #B91C1C; margin: 0; font-size: 13px; line-height: 1.5;">• If you didn't request this, someone may be trying to access your account</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #DC2626, #EF4444); color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 10px; font-size: 15px; font-weight: 700; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);">Reset My Password →</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Didn't Request Info -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F3F4F6; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td>
                                        <p style="color: #374151; margin: 0 0 8px 0; font-size: 14px; font-weight: 700;">Didn't request a password reset?</p>
                                        <p style="color: #6B7280; margin: 0 0 12px 0; font-size: 13px; line-height: 1.5;">
                                            If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.
                                        </p>
                                        <p style="color: #6B7280; margin: 0; font-size: 13px;">
                                            Concerned about your account security? <a href="mailto:security@credbuzzpay.com" style="color: #DC2626; text-decoration: none; font-weight: 600;">Contact our security team</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Divider -->
                            <div style="border-top: 2px solid #E5E7EB; margin: 30px 0;"></div>
                            
                            <!-- Support -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #9CA3AF; margin: 0 0 8px 0; font-size: 13px;">Need help?</p>
                                        <p style="color: #4B5563; margin: 0; font-size: 14px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #DC2626; text-decoration: none;">Contact Support</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 25px 40px; border-top: 1px solid #E5E7EB;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 8px 0; font-size: 13px; font-weight: 600;">CredBuzzPay Security Team</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.<br>
                                            This email was sent to {email}<br>
                                            This is an automated security message. Please do not reply.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """
    
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


def send_password_reset_confirmation_email(email: str, user_name: str = None) -> bool:
    """
    Send password reset confirmation email after successful password change.
    """
    subject = "✅ CredBuzzPay - Password Successfully Reset"
    
    plain_message = f"""
Hello{f' {user_name}' if user_name else ''},

Password Reset Confirmation

Your CredBuzzPay account password has been successfully reset.

IMPORTANT SECURITY NOTICE:
• Your account is now secured with your new password
• If you didn't make this change, contact us immediately
• We recommend enabling two-factor authentication

Security Tips:
- Use a strong, unique password
- Never share your password with anyone
- Change your password regularly
- Enable additional security features in your account settings

If you did not authorize this password change:
1. Contact our security team immediately
2. Email: security@credbuzzpay.com
3. We will investigate and secure your account

Thank you for keeping your account secure.

Best regards,
The CredBuzzPay Security Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset Confirmation</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">✅</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">Password Reset Successful</h1>
                            <p style="color: #ffffff; margin: 0; font-size: 15px; font-weight: 500;">Your account is now secured</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">Hello{f' {user_name}' if user_name else ''}!</h2>
                            <p style="color: #4B5563; font-size: 15px; line-height: 1.6; margin: 0 0 25px 0;">
                                Your CredBuzzPay account password has been successfully reset. Your account is now secured with your new password.
                            </p>
                            
                            <!-- Success Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #ECFDF5, #D1FAE5); border-left: 4px solid #00A38D; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #065F46; margin: 0 0 10px 0; font-size: 15px; font-weight: 700;">✅ What This Means:</p>
                                        <ul style="color: #047857; margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8;">
                                            <li style="margin-bottom: 6px;">Your old password no longer works</li>
                                            <li style="margin-bottom: 6px;">Your account is secured with the new password</li>
                                            <li style="margin-bottom: 0;">You can now log in using your new credentials</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Security Warning -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #FEF2F2; border: 2px solid #FCA5A5; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #991B1B; margin: 0 0 12px 0; font-size: 15px; font-weight: 700;">⚠️ Didn't Make This Change?</p>
                                        <p style="color: #B91C1C; margin: 0 0 15px 0; font-size: 13px; line-height: 1.6;">
                                            If you did NOT authorize this password reset, your account may be compromised. Contact our security team immediately.
                                        </p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                                            <tr>
                                                <td align="center">
                                                    <a href="mailto:security@credbuzzpay.com" style="display: inline-block; background: #DC2626; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 8px; font-size: 14px; font-weight: 700;">Contact Security Team</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Security Tips -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-left: 4px solid #00A38D; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <h3 style="color: #1A233A; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">🔒 Security Best Practices</h3>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Use a strong, unique password</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Enable two-factor authentication</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Change your password regularly</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">✓ Never share your password</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #00A38D, #00D2B8); color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 10px; font-size: 15px; font-weight: 700;">Log In to Your Account →</a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay Security Team</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.<br>
                                            This email was sent to {email}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
        
        logger.info(f"Password reset confirmation email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset confirmation email to {email}: {str(e)}")
        return False


def send_kyc_pending_reminder_email(email: str, user_name: str, current_step: int, total_steps: int = 7) -> bool:
    """
    Send KYC pending reminder email to users who haven't completed KYC.
    """
    subject = "⏰ CredBuzzPay - Complete Your KYC Verification"
    
    progress_percentage = int((current_step / total_steps) * 100)
    
    plain_message = f"""
Hello {user_name}!

Complete Your KYC Verification

We noticed you're in the process of completing your KYC verification.

Your Current Progress:
• Step {current_step} of {total_steps} ({progress_percentage}% complete)

Why complete KYC?
✓ Access all CredBuzzPay features
✓ Higher transaction limits
✓ Enhanced security
✓ Full account access

Complete your KYC now to enjoy seamless payment experiences!

What's Remaining:
Complete the verification steps to activate your full account.

Need help? Our support team is here to assist you.
Email: support@credbuzzpay.com

Best regards,
The CredBuzzPay Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Your KYC</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 50%, #FF8C00 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">⏰</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">Complete Your KYC</h1>
                            <p style="color: #ffffff; margin: 0; font-size: 15px; font-weight: 500;">You're almost there!</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">Hi {user_name}! 👋</h2>
                            <p style="color: #4B5563; font-size: 15px; line-height: 1.6; margin: 0 0 25px 0;">
                                We noticed you started your KYC verification but haven't completed it yet. Let's finish it together!
                            </p>
                            
                            <!-- Progress Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #00A38D, #00D2B8); border-radius: 12px; padding: 30px 20px; margin-bottom: 25px; box-shadow: 0 8px 20px rgba(0, 163, 141, 0.25);">
                                <tr>
                                    <td align="center">
                                        <p style="color: #ffffff; margin: 0 0 15px 0; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Your Progress</p>
                                        <div style="background-color: rgba(255, 255, 255, 0.2); border-radius: 50px; height: 12px; width: 100%; margin-bottom: 15px;">
                                            <div style="background-color: #ffffff; border-radius: 50px; height: 12px; width: {progress_percentage}%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);"></div>
                                        </div>
                                        <p style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800;">{progress_percentage}% Complete</p>
                                        <p style="color: rgba(255, 255, 255, 0.9); margin: 8px 0 0 0; font-size: 14px;">Step {current_step} of {total_steps}</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Benefits -->
                            <h3 style="color: #1A233A; margin: 0 0 20px 0; font-size: 18px; font-weight: 700;">Why Complete KYC? 🚀</h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 12px 0;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="30" style="vertical-align: top;">
                                                    <span style="color: #00A38D; font-size: 18px;">✓</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">Access All Features</p>
                                                    <p style="color: #6B7280; margin: 2px 0 0 0; font-size: 13px;">Unlock complete platform access</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="30" style="vertical-align: top;">
                                                    <span style="color: #00A38D; font-size: 18px;">✓</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">Higher Transaction Limits</p>
                                                    <p style="color: #6B7280; margin: 2px 0 0 0; font-size: 13px;">Increase your spending power</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 12px 0;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="30" style="vertical-align: top;">
                                                    <span style="color: #00A38D; font-size: 18px;">✓</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">Enhanced Security</p>
                                                    <p style="color: #6B7280; margin: 2px 0 0 0; font-size: 13px;">Protect your account better</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #00A38D, #00D2B8); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 10px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 12px rgba(0, 163, 141, 0.3);">Complete KYC Now →</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Support -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">Need help with verification?</p>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support Team →</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
        
        logger.info(f"KYC reminder email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send KYC reminder email to {email}: {str(e)}")
        return False


def send_kyc_rejection_email(email: str, user_name: str, rejection_reason: str, rejected_by: str = None) -> bool:
    """
    Send KYC rejection email when admin rejects user's KYC application.
    """
    subject = "❌ CredBuzzPay - KYC Application Rejected"
    
    plain_message = f"""
Hello {user_name},

KYC Application Status: REJECTED

We regret to inform you that your KYC application has been rejected by our verification team.

Rejection Reason:
{rejection_reason}

What to do next:
1. Review the rejection reason carefully
2. Make necessary corrections to your documents
3. Resubmit your KYC application
4. Our team will review it again

Important Notes:
• Ensure all documents are clear and legible
• Information must match across all documents
• Use recent photographs
• Follow all guidelines provided

Need Help?
If you have questions about the rejection or need assistance:
• Email: support@credbuzzpay.com
• Our support team is ready to help you

Best regards,
The CredBuzzPay Verification Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KYC Application Rejected</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">❌</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">KYC Application Rejected</h1>
                            <p style="color: #FEE2E2; margin: 0; font-size: 15px; font-weight: 500;">We need your attention</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">Hi {user_name},</h2>
                            <p style="color: #4B5563; font-size: 15px; line-height: 1.6; margin: 0 0 25px 0;">
                                Unfortunately, your KYC application has been reviewed and rejected by our verification team.
                            </p>
                            
                            <!-- Rejection Reason Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #FEF2F2; border-left: 4px solid #DC2626; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #991B1B; margin: 0 0 12px 0; font-size: 15px; font-weight: 700;">📋 Rejection Reason:</p>
                                        <p style="color: #B91C1C; margin: 0; font-size: 14px; line-height: 1.6;">
                                            {rejection_reason}
                                        </p>
                                        {f'<p style="color: #DC2626; margin: 12px 0 0 0; font-size: 12px; font-style: italic;">Reviewed by: {rejected_by}</p>' if rejected_by else ''}
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Next Steps -->
                            <h3 style="color: #1A233A; margin: 0 0 20px 0; font-size: 18px; font-weight: 700;">What to Do Next 📝</h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <ol style="color: #4B5563; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                                            <li style="margin-bottom: 10px;"><strong>Review</strong> the rejection reason carefully</li>
                                            <li style="margin-bottom: 10px;"><strong>Correct</strong> the issues mentioned</li>
                                            <li style="margin-bottom: 10px;"><strong>Prepare</strong> updated documents if needed</li>
                                            <li style="margin-bottom: 0;"><strong>Resubmit</strong> your KYC application</li>
                                        </ol>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Important Tips -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #FFF7ED, #FED7AA); border-left: 4px solid #FF8C00; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #7A3D00; margin: 0 0 12px 0; font-size: 14px; font-weight: 700;">💡 Important Tips:</p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 13px;">✓ Ensure all documents are clear and legible</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 13px;">✓ Information must match across all documents</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 13px;">✓ Use recent photographs</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 13px;">✓ Follow all guidelines provided</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #00A38D, #00D2B8); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 10px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 12px rgba(0, 163, 141, 0.3);">Resubmit KYC →</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Support -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F9FAFB; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">Questions about the rejection?</p>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support Team →</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #DC2626;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay Verification Team</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
        
        logger.info(f"KYC rejection email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send KYC rejection email to {email}: {str(e)}")
        return False


def send_kyc_completion_welcome_email(email: str, user_name: str) -> bool:
    """
    Send welcome email after KYC is fully completed (all steps done).
    This is different from the registration welcome email.
    """
    subject = "🎉 CredBuzzPay - KYC Verified! Your Account is Fully Active"
    
    plain_message = f"""
Hello {user_name}!

Congratulations! Your KYC is Complete! 🎉

We're excited to inform you that your KYC verification has been successfully completed!

Your Account Status:
✅ KYC Verification: COMPLETED
✅ Account Status: FULLY ACTIVE
✅ Transaction Limits: MAXIMUM

What You Can Do Now:
• Pay bills without restrictions
• Transfer money with higher limits
• Access all premium features
• Enjoy seamless transactions
• Complete financial freedom

Start Exploring:
Log in to your account and explore all the amazing features CredBuzzPay has to offer!

Thank you for completing your verification and trusting CredBuzzPay!

Need help? Our support team is here for you.
Email: support@credbuzzpay.com

Best regards,
The CredBuzzPay Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version - Similar to original welcome but post-KYC themed
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KYC Completed - Welcome</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 50%, #FF8C00 100%); padding: 50px 30px; text-align: center;">
                            <div style="font-size: 64px; margin-bottom: 15px;">🎉</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 32px; font-weight: 700;">KYC Verified!</h1>
                            <p style="color: #ffffff; margin: 0; font-size: 16px; font-weight: 500;">Your account is now fully active</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 24px; font-weight: 700;">Congratulations {user_name}! 🎊</h2>
                            <p style="color: #4B5563; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Your KYC verification has been successfully completed! You now have full access to all CredBuzzPay features.
                            </p>
                            
                            <!-- Status Badges -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 15px; background: linear-gradient(135deg, #ECFDF5, #D1FAE5); border-radius: 10px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="40" style="vertical-align: top;">
                                                    <span style="font-size: 24px;">✅</span>
                                                </td>
                                                <td style="padding-left: 12px; vertical-align: top;">
                                                    <p style="color: #065F46; margin: 0 0 4px 0; font-size: 15px; font-weight: 700;">KYC Verification</p>
                                                    <p style="color: #047857; margin: 0; font-size: 13px;">COMPLETED</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr><td style="height: 12px;"></td></tr>
                                <tr>
                                    <td style="padding: 15px; background: linear-gradient(135deg, #EFF6FF, #DBEAFE); border-radius: 10px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="40" style="vertical-align: top;">
                                                    <span style="font-size: 24px;">✅</span>
                                                </td>
                                                <td style="padding-left: 12px; vertical-align: top;">
                                                    <p style="color: #1E40AF; margin: 0 0 4px 0; font-size: 15px; font-weight: 700;">Account Status</p>
                                                    <p style="color: #1D4ED8; margin: 0; font-size: 13px;">FULLY ACTIVE</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr><td style="height: 12px;"></td></tr>
                                <tr>
                                    <td style="padding: 15px; background: linear-gradient(135deg, #FFF7ED, #FED7AA); border-radius: 10px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td width="40" style="vertical-align: top;">
                                                    <span style="font-size: 24px;">✅</span>
                                                </td>
                                                <td style="padding-left: 12px; vertical-align: top;">
                                                    <p style="color: #7A3D00; margin: 0 0 4px 0; font-size: 15px; font-weight: 700;">Transaction Limits</p>
                                                    <p style="color: #92400E; margin: 0; font-size: 13px;">MAXIMUM</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- What's Next -->
                            <h3 style="color: #1A233A; margin: 0 0 20px 0; font-size: 18px; font-weight: 700;">What You Can Do Now 🚀</h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-left: 4px solid #00A38D; border-radius: 10px; padding: 25px; margin-bottom: 30px;">
                                <tr>
                                    <td>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 14px; line-height: 1.6;"><strong>💳</strong> Pay bills without restrictions</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 14px; line-height: 1.6;"><strong>💸</strong> Transfer money with higher limits</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 14px; line-height: 1.6;"><strong>⭐</strong> Access all premium features</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #1A233A; margin: 0; font-size: 14px; line-height: 1.6;"><strong>🔒</strong> Enjoy enhanced security</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #00A38D, #00D2B8); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 10px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 12px rgba(0, 163, 141, 0.3);">Start Using CredBuzzPay →</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Thank You -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #F0FDF4, #DBEAFE); border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 10px 0; font-size: 16px; font-weight: 700;">Thank You for Choosing CredBuzzPay!</p>
                                        <p style="color: #4B5563; margin: 0; font-size: 14px; line-height: 1.6;">
                                            We're committed to providing you with the best payment experience. If you need any assistance, we're here to help!
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Support -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F9FAFB; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">Need help getting started?</p>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support →</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay</p>
                                        <p style="color: #4B5563; margin: 0 0 15px 0; font-size: 12px; line-height: 1.5;">Your Trusted Payment Partner</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.<br>
                                            This email was sent to {email}
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
        
        logger.info(f"KYC completion welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send KYC completion welcome email to {email}: {str(e)}")
        return False


def send_support_ticket_auto_reply(email: str, user_name: str, ticket_id: str, ticket_subject: str) -> bool:
    """
    Send automatic reply when user raises a support ticket.
    """
    subject = f"🎫 CredBuzzPay - Support Ticket #{ticket_id} Received"
    
    plain_message = f"""
Hello {user_name}!

Support Ticket Received

We have received your support ticket and our team is reviewing it.

Ticket Details:
• Ticket ID: #{ticket_id}
• Subject: {ticket_subject}
• Status: Under Review

What Happens Next:
Our support team will review your request and get back to you as soon as possible. We typically respond within 24-48 hours.

Track Your Ticket:
You can check the status of your ticket anytime by logging into your account.

Need Urgent Help?
For urgent matters, you can also contact us at:
• Email: support@credbuzzpay.com
• Available: 24/7

Thank you for contacting CredBuzzPay!

Best regards,
The CredBuzzPay Support Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Support Ticket Received</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">🎫</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">Ticket Received</h1>
                            <p style="color: #ffffff; margin: 0; font-size: 15px; font-weight: 500;">We're on it!</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">Hi {user_name}! 👋</h2>
                            <p style="color: #4B5563; font-size: 15px; line-height: 1.6; margin: 0 0 25px 0;">
                                Thank you for reaching out! We've received your support ticket and our team is already on it.
                            </p>
                            
                            <!-- Ticket Details Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #EFF6FF, #DBEAFE); border-left: 4px solid #00A38D; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #1E40AF; margin: 0 0 15px 0; font-size: 15px; font-weight: 700;">📋 Ticket Details:</p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #1D4ED8; margin: 0; font-size: 14px;"><strong>Ticket ID:</strong> #{ticket_id}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #1D4ED8; margin: 0; font-size: 14px;"><strong>Subject:</strong> {ticket_subject}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #1D4ED8; margin: 0; font-size: 14px;"><strong>Status:</strong> Under Review</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- What's Next -->
                            <h3 style="color: #1A233A; margin: 0 0 20px 0; font-size: 18px; font-weight: 700;">What Happens Next? 🚀</h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <ol style="color: #4B5563; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                                            <li style="margin-bottom: 10px;">Our team reviews your ticket</li>
                                            <li style="margin-bottom: 10px;">We investigate the issue thoroughly</li>
                                            <li style="margin-bottom: 10px;">You'll receive a response within 24-48 hours</li>
                                            <li style="margin-bottom: 0;">We'll resolve your concern promptly</li>
                                        </ol>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Response Time -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #FFF7ED, #FED7AA); border-left: 4px solid #FF8C00; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #7A3D00; margin: 0; font-size: 14px; line-height: 1.6;">
                                            ⏱️ <strong>Expected Response Time:</strong> 24-48 hours<br>
                                            We'll do our best to respond even sooner!
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="#" style="display: inline-block; background: linear-gradient(135deg, #00A38D, #00D2B8); color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 10px; font-size: 15px; font-weight: 700; box-shadow: 0 4px 12px rgba(0, 163, 141, 0.3);">Track Ticket Status →</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Urgent Help -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F9FAFB; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">Need urgent assistance?</p>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support (24/7) →</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay Support Team</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
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
        
        logger.info(f"Support ticket auto-reply sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send support ticket auto-reply to {email}: {str(e)}")
        return False


def send_maintenance_email(
    recipient_emails: list,
    affected_service: str,
    maintenance_start: str,
    maintenance_end: str,
    description: str = None
) -> dict:
    """
    Send maintenance notification email to users.
    Admin/Developer only.
    
    Args:
        recipient_emails: List of email addresses
        affected_service: Name of affected service/module
        maintenance_start: Start time (formatted string)
        maintenance_end: End time (formatted string)
        description: Optional additional details
    
    Returns:
        dict: {'sent': [], 'failed': []}
    """
    subject = f"🛠️ CredBuzzPay - Scheduled Maintenance: {affected_service}"
    
    plain_message = f"""
Important System Maintenance Notification

Dear CredBuzzPay User,

We will be performing scheduled maintenance on our system.

Maintenance Details:
• Affected Service: {affected_service}
• Start Time: {maintenance_start}
• End Time: {maintenance_end}
• Expected Duration: Check times above

{f'Details: {description}' if description else ''}

What This Means:
During the maintenance window, the affected service may be temporarily unavailable or experience reduced performance.

We apologize for any inconvenience and appreciate your patience while we improve our services.

What You Can Do:
• Plan your transactions outside the maintenance window
• Contact support if you have urgent needs
• Check our status page for real-time updates

Thank you for your understanding!

Best regards,
The CredBuzzPay Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scheduled Maintenance</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #FF8C00 0%, #FFA500 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">🛠️</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">Scheduled Maintenance</h1>
                            <p style="color: #ffffff; margin: 0; font-size: 15px; font-weight: 500;">System Update Notification</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">Important System Maintenance</h2>
                            <p style="color: #4B5563; font-size: 15px; line-height: 1.6; margin: 0 0 25px 0;">
                                We will be performing scheduled maintenance to improve our services and enhance your experience.
                            </p>
                            
                            <!-- Maintenance Details Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #FFF7ED, #FED7AA); border-left: 4px solid #FF8C00; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #7A3D00; margin: 0 0 15px 0; font-size: 15px; font-weight: 700;">📋 Maintenance Details:</p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 14px;"><strong>Affected Service:</strong></p>
                                                    <p style="color: #92400E; margin: 4px 0 0 0; font-size: 15px; font-weight: 700;">{affected_service}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 14px;"><strong>Start Time:</strong></p>
                                                    <p style="color: #92400E; margin: 4px 0 0 0; font-size: 15px; font-weight: 700;">{maintenance_start}</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0;">
                                                    <p style="color: #92400E; margin: 0; font-size: 14px;"><strong>End Time:</strong></p>
                                                    <p style="color: #92400E; margin: 4px 0 0 0; font-size: 15px; font-weight: 700;">{maintenance_end}</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            {f'''<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #EFF6FF; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #1E40AF; margin: 0 0 10px 0; font-size: 14px; font-weight: 700;">ℹ️ Additional Information:</p>
                                        <p style="color: #1D4ED8; margin: 0; font-size: 13px; line-height: 1.6;">{description}</p>
                                    </td>
                                </tr>
                            </table>''' if description else ''}
                            
                            <!-- Impact -->
                            <h3 style="color: #1A233A; margin: 0 0 15px 0; font-size: 18px; font-weight: 700;">What This Means for You</h3>
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px;">• The affected service may be temporarily unavailable</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px;">• You may experience reduced performance</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 6px 0;">
                                                    <p style="color: #4B5563; margin: 0; font-size: 14px;">• Other services will remain fully operational</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Recommendations -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background: linear-gradient(135deg, #ECFDF5, #D1FAE5); border-left: 4px solid #00A38D; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #065F46; margin: 0 0 10px 0; font-size: 14px; font-weight: 700;">💡 Recommendations:</p>
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #047857; margin: 0; font-size: 13px;">✓ Plan your transactions outside the maintenance window</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #047857; margin: 0; font-size: 13px;">✓ Contact support if you have urgent needs</p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 4px 0;">
                                                    <p style="color: #047857; margin: 0; font-size: 13px;">✓ Check our status page for real-time updates</p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Support -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F9FAFB; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">Questions or urgent assistance needed?</p>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support →</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Thank You -->
                            <p style="color: #4B5563; font-size: 14px; line-height: 1.6; margin: 25px 0 0 0; text-align: center;">
                                Thank you for your understanding and patience!
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #FF8C00;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay Operations Team</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """
    
    results = {'sent': [], 'failed': []}
    
    for email in recipient_emails:
        try:
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send(fail_silently=False)
            
            results['sent'].append(email)
            logger.info(f"Maintenance email sent to {email}")
            
        except Exception as e:
            results['failed'].append({'email': email, 'error': str(e)})
            logger.error(f"Failed to send maintenance email to {email}: {str(e)}")
    
    return results


def send_important_notice_email(
    recipient_emails: list,
    notice_title: str,
    notice_message: str,
    action_required: bool = False,
    action_url: str = None
) -> dict:
    """
    Send important notice/announcement email to users.
    Admin/Developer only.
    
    Args:
        recipient_emails: List of email addresses
        notice_title: Title of the notice
        notice_message: Detailed message content
        action_required: Whether user action is needed
        action_url: Optional URL for action button
    
    Returns:
        dict: {'sent': [], 'failed': []}
    """
    subject = f"📢 CredBuzzPay - Important Notice: {notice_title}"
    
    plain_message = f"""
IMPORTANT NOTICE

Dear CredBuzzPay User,

{notice_title}

{notice_message}

{f'ACTION REQUIRED: Please review this notice and take necessary action.' if action_required else 'No action required on your part.'}

{f'Visit: {action_url}' if action_url else ''}

If you have any questions or concerns, please contact our support team.

Email: support@credbuzzpay.com

Thank you for your attention.

Best regards,
The CredBuzzPay Team

---
© 2026 CredBuzzPay. All rights reserved.
    """.strip()
    
    # HTML version
    html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Important Notice</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f0f2f5;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center" style="padding: 0 15px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 163, 141, 0.12);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #00A38D 0%, #00D2B8 100%); padding: 40px 30px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 15px;">📢</div>
                            <h1 style="color: #ffffff; margin: 0 0 10px 0; font-size: 28px; font-weight: 700;">Important Notice</h1>
                            <p style="color: #ffffff; margin: 0; font-size: 15px; font-weight: 500;">Please read carefully</p>
                        </td>
                    </tr>
                    
                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 45px 40px;">
                            {f'''<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #FEF2F2; border-left: 4px solid #DC2626; border-radius: 10px; padding: 20px; margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #991B1B; margin: 0; font-size: 14px; font-weight: 700;">⚠️ ACTION REQUIRED</p>
                                    </td>
                                </tr>
                            </table>''' if action_required else ''}
                            
                            <h2 style="color: #1A233A; margin: 0 0 15px 0; font-size: 22px; font-weight: 700;">{notice_title}</h2>
                            
                            <!-- Notice Content Box -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F5F5F7; border-left: 4px solid #00A38D; border-radius: 10px; padding: 25px; margin-bottom: 25px;">
                                <tr>
                                    <td>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; line-height: 1.7; white-space: pre-line;">{notice_message}</p>
                                    </td>
                                </tr>
                            </table>
                            
                            {f'''<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin-bottom: 25px;">
                                <tr>
                                    <td align="center">
                                        <a href="{action_url}" style="display: inline-block; background: linear-gradient(135deg, #00A38D, #00D2B8); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 10px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 12px rgba(0, 163, 141, 0.3);">Take Action →</a>
                                    </td>
                                </tr>
                            </table>''' if action_url else ''}
                            
                            <!-- Support -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #F9FAFB; border-radius: 10px; padding: 20px;">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">Questions or concerns?</p>
                                        <p style="color: #1A233A; margin: 0; font-size: 15px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #00A38D; text-decoration: none; font-weight: 600;">Contact Support →</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 3px solid #00A38D;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #1A233A; margin: 0 0 8px 0; font-size: 13px; font-weight: 700;">CredBuzzPay Team</p>
                                        <p style="color: #9CA3AF; margin: 0; font-size: 11px; line-height: 1.5;">
                                            © 2026 CredBuzzPay. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """
    
    results = {'sent': [], 'failed': []}
    
    for email in recipient_emails:
        try:
            email_message = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_message.attach_alternative(html_message, "text/html")
            email_message.send(fail_silently=False)
            
            results['sent'].append(email)
            logger.info(f"Important notice email sent to {email}")
            
        except Exception as e:
            results['failed'].append({'email': email, 'error': str(e)})
            logger.error(f"Failed to send important notice email to {email}: {str(e)}")
    
    return results
