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
    
    # HTML version - Modern, responsive design
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
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);">
                    <!-- Header with Brand -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%); padding: 40px 30px; text-align: center;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <div style="background-color: rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 15px 25px; display: inline-block; backdrop-filter: blur(10px);">
                                            <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">CredBuzzPay</h1>
                                        </div>
                                        <p style="color: #E0E7FF; margin: 15px 0 0 0; font-size: 15px; font-weight: 500;">🔐 Secure Payment Solutions</p>
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
                                        <h2 style="color: #1F2937; margin: 0 0 12px 0; font-size: 26px; font-weight: 700; line-height: 1.3;">Hello{f' {user_name}' if user_name else ''}! 👋</h2>
                                        <p style="color: #6B7280; font-size: 16px; line-height: 1.6; margin: 0;">Welcome to CredBuzzPay! To complete your verification, please use the code below:</p>
                                    </td>
                                </tr>
                                
                                <!-- OTP Code Box -->
                                <tr>
                                    <td align="center" style="padding: 0 0 35px 0;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td align="center" style="background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); border-radius: 12px; padding: 35px 20px; box-shadow: 0 8px 20px rgba(79, 70, 229, 0.3);">
                                                    <p style="color: #E0E7FF; margin: 0 0 12px 0; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Your Verification Code</p>
                                                    <div style="background-color: rgba(255, 255, 255, 0.15); border-radius: 8px; padding: 20px; backdrop-filter: blur(10px);">
                                                        <span style="color: #ffffff; font-size: 42px; font-weight: 800; letter-spacing: 12px; font-family: 'Courier New', Courier, monospace; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">{otp_code}</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Timer Info -->
                                <tr>
                                    <td align="center" style="padding-bottom: 35px;">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="background-color: #FEF3C7; border-radius: 8px; padding: 16px 24px; border-left: 4px solid #F59E0B;">
                                            <tr>
                                                <td>
                                                    <p style="color: #92400E; margin: 0; font-size: 14px; font-weight: 600; line-height: 1.5;">
                                                        ⏰ <strong>Expires in {settings.OTP_EXPIRY_MINUTES} minutes</strong> - Please use it quickly!
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                
                                <!-- Security Tips -->
                                <tr>
                                    <td style="background-color: #F3F4F6; border-radius: 10px; padding: 25px;">
                                        <h3 style="color: #1F2937; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">🔒 Security Tips</h3>
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
                                        <p style="color: #6B7280; margin: 0; font-size: 14px; font-weight: 600;">
                                            <a href="mailto:support@credbuzzpay.com" style="color: #4F46E5; text-decoration: none;">Contact Support</a>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(to bottom, #F9FAFB, #F3F4F6); padding: 30px 40px; border-top: 1px solid #E5E7EB;">
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="color: #6B7280; margin: 0 0 8px 0; font-size: 13px; font-weight: 600;">CredBuzzPay</p>
                                        <p style="color: #9CA3AF; margin: 0 0 15px 0; font-size: 12px; line-height: 1.5;">Your Trusted Payment Partner</p>
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
