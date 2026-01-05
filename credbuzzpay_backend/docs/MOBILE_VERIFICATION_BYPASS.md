# Mobile OTP Verification Control

## Overview

This feature allows you to temporarily bypass mobile OTP verification during user registration and authentication. When disabled, only email OTP verification is required, making it easier for development and testing.

## Configuration

### Settings.py

A new setting has been added to control mobile OTP verification:

```python
# MOBILE VERIFICATION CONTROL
# Set to False to temporarily bypass mobile OTP verification (only email OTP required)
# Set to True to require both email and mobile OTP verification
REQUIRE_MOBILE_VERIFICATION = os.getenv('REQUIRE_MOBILE_VERIFICATION', 'False').lower() in ('true', '1', 'yes')
```

### Environment Variables

Add this to your `.env` file:

```bash
# Mobile OTP Verification Control
# Set to True to require mobile OTP verification
# Set to False to bypass mobile OTP (only email OTP required)
REQUIRE_MOBILE_VERIFICATION=False
```

**Default:** `False` (mobile verification disabled)

## How It Works

### When `REQUIRE_MOBILE_VERIFICATION=False` (Default)

1. **During Registration:**
   - Email OTP is sent and required for verification
   - Mobile OTP is NOT sent
   - If a mobile number is provided, it's automatically marked as verified
   - User can complete registration with only email OTP

2. **Verify Mobile Endpoint (`/api/v1/auth/verify-mobile/`):**
   - Automatically verifies the mobile number without requiring OTP
   - Returns success message: "Mobile verification is disabled - automatically verified"

3. **Resend OTP Endpoint (`/api/v1/auth/resend-otp/`):**
   - For email: Works normally
   - For mobile: Auto-verifies and returns bypass message

### When `REQUIRE_MOBILE_VERIFICATION=True`

1. **During Registration:**
   - Both email and mobile OTPs are sent
   - User must verify both email and mobile

2. **Verify Mobile Endpoint:**
   - Requires valid OTP
   - Works as normal mobile verification

3. **Resend OTP Endpoint:**
   - Both email and mobile OTPs can be resent normally

## API Response Changes

### Registration Response (When Mobile Verification Disabled)

```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": "ABC12",
      "email": "user@example.com",
      "mobile": "+1234567890",
      "is_email_verified": false,
      "is_mobile_verified": true,  // Automatically set to true
      ...
    },
    "tokens": {...},
    "email_otp_sent": true,
    "email_message": "OTP sent successfully",
    "mobile_otp_sent": false,
    "mobile_message": "Mobile verification disabled - automatically verified"
  }
}
```

### Verify Mobile Response (When Disabled)

```json
{
  "status": "success",
  "message": "Mobile verification is disabled - automatically verified"
}
```

### Resend OTP - Mobile (When Disabled)

```json
{
  "status": "success",
  "message": "Mobile verification is disabled - automatically verified",
  "data": {
    "otp_sent": false,
    "message": "Mobile verification bypassed"
  }
}
```

## Use Cases

### Development & Testing
- **Recommended:** `REQUIRE_MOBILE_VERIFICATION=False`
- Speeds up testing by eliminating mobile OTP steps
- No need for SMS service integration during development

### Staging Environment
- **Recommended:** `REQUIRE_MOBILE_VERIFICATION=False` or `True` based on testing needs
- Test with email-only flow first
- Enable mobile verification when ready to test SMS integration

### Production Environment
- **Recommended:** `REQUIRE_MOBILE_VERIFICATION=True`
- Ensures full two-factor verification (email + mobile)
- Enhanced security with both channels verified

## Switching Between Modes

### To Disable Mobile Verification

1. Update `.env` file:
   ```bash
   REQUIRE_MOBILE_VERIFICATION=False
   ```

2. Restart your Django application:
   ```bash
   # If using gunicorn
   sudo systemctl restart credbuzz-backend
   
   # If using development server
   python manage.py runserver
   ```

3. No database changes needed - existing users remain unaffected

### To Enable Mobile Verification

1. Update `.env` file:
   ```bash
   REQUIRE_MOBILE_VERIFICATION=True
   ```

2. Ensure SMS service is configured (Twilio or equivalent)

3. Restart your Django application

## Code Changes Summary

### Files Modified

1. **`credbuzzpay_backend/settings.py`**
   - Added `REQUIRE_MOBILE_VERIFICATION` setting

2. **`authentication/views.py`**
   - Modified `register()` function to check the setting
   - Modified `verify_mobile()` to auto-verify when disabled
   - Modified `resend_otp()` to handle mobile bypass

3. **`.env.production`**
   - Added `REQUIRE_MOBILE_VERIFICATION=False` default

## Testing

### Test Registration with Mobile Verification Disabled

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "mobile": "+1234567890"
  }'
```

**Expected:**
- `is_mobile_verified: true` in response
- No mobile OTP sent
- Only email OTP required

### Test Verify Mobile (When Disabled)

```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-mobile/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"otp": "123456"}'
```

**Expected:**
- Success without checking OTP
- Message: "Mobile verification is disabled - automatically verified"

## Security Considerations

⚠️ **Important:**

1. **Production Use:** 
   - It's recommended to enable mobile verification in production (`REQUIRE_MOBILE_VERIFICATION=True`)
   - Disabling it reduces security by relying only on email verification

2. **Temporary Bypass:** 
   - This feature is designed for temporary use during development/testing
   - Enable full verification before launching to production

3. **User Experience:**
   - Disabling mobile verification provides better UX during development
   - But production users benefit from two-factor verification

## Troubleshooting

### Issue: Mobile verification still required after setting to False

**Solution:**
1. Verify `.env` file has correct value
2. Restart Django application
3. Check logs for setting value:
   ```python
   from django.conf import settings
   print(settings.REQUIRE_MOBILE_VERIFICATION)
   ```

### Issue: Old users not auto-verified

**Solution:**
This setting only affects new registrations and verification attempts. To auto-verify existing users:

```python
# Run in Django shell
from authentication.models import User

# Auto-verify all users with mobile numbers
User.objects.filter(mobile__isnull=False, is_mobile_verified=False).update(is_mobile_verified=True)
```

## Future Enhancements

Potential improvements:
1. Admin panel toggle for this setting
2. Per-user mobile verification requirements
3. Audit log for when bypass is used
4. Temporary bypass with expiration date

---

**Last Updated:** January 5, 2026  
**Version:** 1.0  
**Status:** ✅ Implemented and Ready to Use
