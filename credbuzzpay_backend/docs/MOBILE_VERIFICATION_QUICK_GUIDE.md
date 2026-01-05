# 🔧 Quick Guide: Bypass Mobile OTP Verification

## ✅ What's Been Done

Mobile OTP verification can now be temporarily bypassed. When disabled, users only need to verify their email (not mobile).

## 🎯 Quick Setup

### 1. Update Your Environment File

Add to your `.env` file (or create it if it doesn't exist):

```bash
# Set to False to bypass mobile OTP (RECOMMENDED FOR NOW)
REQUIRE_MOBILE_VERIFICATION=False

# Set to True to require mobile OTP (for production later)
# REQUIRE_MOBILE_VERIFICATION=True
```

### 2. That's It!

No code changes needed. Just restart your Django server:

```bash
# Development
python manage.py runserver

# Production
sudo systemctl restart credbuzz-backend
```

## 📝 What Happens Now

### With `REQUIRE_MOBILE_VERIFICATION=False` (Current Default)

✅ **Registration:**
- Email OTP: ✉️ REQUIRED (user must verify)
- Mobile OTP: ❌ NOT SENT (automatically verified)

✅ **User Experience:**
- Users only verify email
- Mobile numbers are auto-verified
- Faster registration process

✅ **API Endpoints:**
- `/api/v1/auth/register/` - Only sends email OTP
- `/api/v1/auth/verify-mobile/` - Auto-verifies without OTP
- `/api/v1/auth/resend-otp/` - For mobile, auto-verifies

### With `REQUIRE_MOBILE_VERIFICATION=True` (For Later)

- Both email and mobile OTP required
- Full two-factor verification
- Production-ready security

## 🔄 Switch Anytime

Just change the value in `.env` and restart:

```bash
# Disable mobile verification
REQUIRE_MOBILE_VERIFICATION=False

# Enable mobile verification  
REQUIRE_MOBILE_VERIFICATION=True
```

## 📊 Testing

### Test Registration (Mobile Verification Disabled)

```bash
POST /api/v1/auth/register/
{
  "email": "test@example.com",
  "password": "Password123!",
  "mobile": "+1234567890"
}
```

**Response:**
```json
{
  "data": {
    "user": {
      "is_mobile_verified": true,  // ← Auto-verified!
      ...
    },
    "mobile_otp_sent": false,
    "mobile_message": "Mobile verification disabled - automatically verified"
  }
}
```

### Test Verify Mobile (Disabled)

```bash
POST /api/v1/auth/verify-mobile/
Authorization: Bearer YOUR_TOKEN
{
  "otp": "any_value"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Mobile verification is disabled - automatically verified"
}
```

## 💡 Recommendations

### For Development (Now)
```bash
REQUIRE_MOBILE_VERIFICATION=False
```
- ✅ Faster testing
- ✅ No SMS service needed
- ✅ Focus on other features

### For Production (Later)
```bash
REQUIRE_MOBILE_VERIFICATION=True
```
- ✅ Better security
- ✅ Two-factor verification
- ✅ Multiple contact channels

## 📂 Files Changed

1. ✅ `settings.py` - Added REQUIRE_MOBILE_VERIFICATION setting
2. ✅ `authentication/views.py` - Updated register, verify_mobile, resend_otp
3. ✅ `.env.production` - Added default setting
4. ✅ Documentation created

## 🚀 Status

**✅ READY TO USE**

The mobile OTP bypass is now active with the default setting of `False` (disabled).

---

**Need help?** Check [MOBILE_VERIFICATION_BYPASS.md](MOBILE_VERIFICATION_BYPASS.md) for detailed documentation.
