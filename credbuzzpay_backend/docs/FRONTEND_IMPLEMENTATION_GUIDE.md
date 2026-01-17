# 🎨 Frontend Implementation Guide: Password Reset & Change Flows

**Target Audience**: Frontend Developers (Web, Mobile, Desktop)  
**Backend API Version**: 2.0 (OTP-First Security Model)  
**Date**: January 13, 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [FLOW A: Forgot Password (Unauthenticated)](#flow-a-forgot-password-unauthenticated)
3. [FLOW B: Profile Password Change (Authenticated)](#flow-b-profile-password-change-authenticated)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Error Handling](#error-handling)
6. [UI/UX Recommendations](#uiux-recommendations)
7. [Code Examples](#code-examples)
8. [Testing Checklist](#testing-checklist)

---

## 🎯 Overview

The CredBuzz backend now implements **two distinct password management flows**:

### FLOW A: Forgot Password (Unauthenticated Users)
**Use Case**: User forgot their password at login screen  
**Steps**: Email → OTP → reset_token → New Password  
**No authentication required** until password is reset

### FLOW B: Profile Password Change (Authenticated Users)
**Use Case**: Logged-in user wants to change password from profile  
**Steps**: Send OTP → Verify OTP → New Password  
**Requires Bearer token** throughout

---

## 🔐 FLOW A: Forgot Password (Unauthenticated)

### When to Use
- User clicks "Forgot Password?" on login screen
- User cannot log in
- User doesn't have access_token

### User Journey

```
Login Screen
    ↓
[Forgot Password Button]
    ↓
Email Input Screen
    ↓
OTP Input Screen
    ↓
New Password Screen
    ↓
Success → Redirect to Login
```

### Step-by-Step Implementation

#### Step 1: Request Password Reset OTP

**API Endpoint**: `POST /api/auth-user/forgot-password/`

**Request**:
```json
{
  "email": "user@example.com"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Password reset OTP has been sent to your email.",
  "data": {
    "email": "user@example.com",
    "expires_in_minutes": 10,
    "debug_otp": "123456"  // Only in DEBUG mode
  }
}
```

**Error Response** (404 NOT FOUND):
```json
{
  "success": false,
  "message": "Email not found. Please check your email address.",
  "error": "EMAIL_NOT_FOUND"
}
```

**UI Elements**:
- Email input field (with validation)
- "Send OTP" button
- Timer showing "OTP valid for 10 minutes"
- "Resend OTP" link (disabled for 60 seconds)

---

#### Step 2: Verify OTP and Get Reset Token

**API Endpoint**: `POST /api/auth-user/verify-forgot-password-otp/`

**Request**:
```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "OTP verified successfully.",
  "data": {
    "reset_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_in_minutes": 15
  }
}
```

**Error Responses**:

- **Invalid OTP** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "Invalid OTP code.",
  "error": "INVALID_OTP",
  "attempts_remaining": 3
}
```

- **OTP Expired** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "OTP has expired. Please request a new one.",
  "error": "OTP_EXPIRED"
}
```

- **Too Many Attempts** (429 TOO MANY REQUESTS):
```json
{
  "success": false,
  "message": "Too many failed attempts. Please request a new OTP.",
  "error": "MAX_ATTEMPTS_EXCEEDED"
}
```

**UI Elements**:
- 6-digit OTP input (numeric)
- "Verify OTP" button
- Countdown timer (10 minutes)
- "Resend OTP" link
- Show remaining attempts after failed attempt

**Important**:
⚠️ **Save the `reset_token` in memory** (not localStorage) - you'll need it for the next step!

---

#### Step 3: Reset Password with Token

**API Endpoint**: `POST /api/auth-user/reset-password-with-token/`

**Request**:
```json
{
  "reset_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "new_password": "NewSecurePass123",
  "confirm_password": "NewSecurePass123"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Password reset successful. Please login with your new password."
}
```

**Error Responses**:

- **Token Expired** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "Reset token has expired. Please start the password reset process again.",
  "error": "TOKEN_EXPIRED"
}
```

- **Weak Password** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "Password validation failed.",
  "errors": {
    "new_password": [
      "Password must be at least 8 characters long.",
      "Password must contain at least one uppercase letter.",
      "Password must contain at least one digit."
    ]
  }
}
```

**UI Elements**:
- New password input (with strength indicator)
- Confirm password input
- Password requirements checklist:
  - ✅ At least 8 characters
  - ✅ One uppercase letter
  - ✅ One lowercase letter
  - ✅ One number
- "Reset Password" button
- Show/hide password toggles

**After Success**:
- Show success message
- Redirect to login screen after 2 seconds
- Clear all stored tokens from memory

---

### Resending OTP (FLOW A)

**API Endpoint**: `POST /api/auth-user/resend-otp/`

**Request**:
```json
{
  "email": "user@example.com"
}
```

**Same response as Step 1** (forgot-password endpoint)

**Rate Limiting**:
- Show "Resend OTP" button disabled for 60 seconds after each request
- Implement client-side countdown timer

---

## 👤 FLOW B: Profile Password Change (Authenticated)

### When to Use
- User is logged in with valid access_token
- User wants to change password from profile/settings
- User clicks "Change Password" in their account settings

### User Journey

```
Profile/Settings Screen
    ↓
[Change Password Button]
    ↓
Send OTP Screen
    ↓
Verify OTP Screen
    ↓
New Password Screen
    ↓
Success → Stay in Profile
```

### Step-by-Step Implementation

#### Step 1: Send OTP to Authenticated User

**API Endpoint**: `POST /api/auth-user/profile/send-otp/`

**Headers**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request**:
```json
{
  "action_type": "PASSWORD_CHANGE"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "OTP sent to your registered email.",
  "data": {
    "email": "user@example.com",
    "expires_in_minutes": 5,
    "debug_otp": "123456"  // Only in DEBUG mode
  }
}
```

**Error Response** (401 UNAUTHORIZED):
```json
{
  "success": false,
  "message": "Authentication required.",
  "error": "AUTHENTICATION_REQUIRED"
}
```

**UI Elements**:
- "Send OTP to my email" button
- Display user's registered email (masked: u***r@example.com)
- Timer showing "OTP valid for 5 minutes" (shorter than FLOW A)
- "Resend OTP" link

**Notes**:
- OTP automatically sent to user's registered email
- No need to ask for email input
- Shorter expiry (5 minutes) for higher security

---

#### Step 2: Verify OTP (Authenticated)

**API Endpoint**: `POST /api/auth-user/profile/verify-otp/`

**Headers**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request**:
```json
{
  "otp_code": "123456"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "OTP verified successfully. You may now proceed."
}
```

**Error Responses**:

- **Invalid OTP** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "Invalid OTP code.",
  "error": "INVALID_OTP",
  "attempts_remaining": 2
}
```

- **OTP Expired** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "OTP has expired. Please request a new one.",
  "error": "OTP_EXPIRED"
}
```

- **Max Attempts** (429 TOO MANY REQUESTS):
```json
{
  "success": false,
  "message": "Too many failed attempts. Please request a new OTP.",
  "error": "MAX_ATTEMPTS_EXCEEDED"
}
```

**UI Elements**:
- 6-digit OTP input
- "Verify OTP" button
- Countdown timer (5 minutes)
- Show remaining attempts (max 3 for authenticated users)
- "Resend OTP" link

**Important**:
⚠️ **No reset_token is returned** - user is already authenticated with Bearer token!

---

#### Step 3: Change Password (After OTP Verification)

**API Endpoint**: `POST /api/auth-user/profile/change-password/`

**Headers**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Request**:
```json
{
  "new_password": "NewSecurePass123",
  "confirm_password": "NewSecurePass123"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Password changed successfully."
}
```

**Error Responses**:

- **OTP Not Verified** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "Please verify OTP before changing password.",
  "error": "OTP_NOT_VERIFIED"
}
```

- **Weak Password** (400 BAD REQUEST):
```json
{
  "success": false,
  "message": "Password validation failed.",
  "errors": {
    "new_password": [
      "Password must be at least 8 characters long."
    ]
  }
}
```

**UI Elements**:
- New password input (with strength meter)
- Confirm password input
- Password requirements checklist
- "Change Password" button
- Show/hide password toggles

**After Success**:
- Show success message
- Stay on profile page (don't redirect)
- Optionally show a confirmation badge

**Notes**:
- This endpoint verifies that OTP was recently verified
- Current access_token remains valid
- User doesn't get logged out

---

## 📡 API Endpoints Reference

### Base URL
```
http://127.0.0.1:8000/api/auth-user
```

### FLOW A Endpoints (Unauthenticated)

| Method | Endpoint | Auth Required | Description |
|--------|----------|--------------|-------------|
| POST | `/forgot-password/` | ❌ No | Send OTP to email |
| POST | `/verify-forgot-password-otp/` | ❌ No | Verify OTP and get reset_token |
| POST | `/reset-password-with-token/` | ❌ No | Reset password with token |
| POST | `/resend-otp/` | ❌ No | Resend OTP to email |

### FLOW B Endpoints (Authenticated)

| Method | Endpoint | Auth Required | Description |
|--------|----------|--------------|-------------|
| POST | `/profile/send-otp/` | ✅ Bearer Token | Send OTP to user's email |
| POST | `/profile/verify-otp/` | ✅ Bearer Token | Verify OTP |
| POST | `/profile/change-password/` | ✅ Bearer Token | Change password after OTP |

---

## ⚠️ Error Handling

### Common Error Codes

| HTTP Status | Error Code | Meaning | Action |
|------------|-----------|---------|--------|
| 400 | `INVALID_OTP` | Wrong OTP entered | Show remaining attempts, allow retry |
| 400 | `OTP_EXPIRED` | OTP > 10/5 min old | Show "Resend OTP" button |
| 400 | `OTP_NOT_VERIFIED` | Tried to skip OTP step | Go back to OTP verification |
| 400 | `TOKEN_EXPIRED` | reset_token > 15 min | Restart from Step 1 |
| 400 | `WEAK_PASSWORD` | Password doesn't meet requirements | Show specific validation errors |
| 404 | `EMAIL_NOT_FOUND` | Email doesn't exist | Suggest sign up or check typo |
| 429 | `MAX_ATTEMPTS_EXCEEDED` | Too many failed OTP attempts | Force resend OTP |
| 401 | `AUTHENTICATION_REQUIRED` | Bearer token missing/invalid | Redirect to login |

### Error Handling Best Practices

1. **Always display specific error messages** from API response
2. **Show remaining attempts** after failed OTP verification
3. **Disable submit buttons** during API calls (prevent double-submit)
4. **Clear sensitive data** (OTP, passwords) after errors
5. **Auto-redirect** to appropriate screen based on error code

---

## 🎨 UI/UX Recommendations

### OTP Input Best Practices

1. **6 Separate Input Boxes**:
   ```
   [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ] [ 6 ]
   ```
   - Auto-focus next box on input
   - Auto-focus previous box on backspace
   - Paste support (auto-distribute digits)

2. **Countdown Timer**:
   - FLOW A: "OTP expires in 09:45"
   - FLOW B: "OTP expires in 04:30"
   - Change color to red in last 2 minutes

3. **Resend OTP Logic**:
   ```javascript
   let resendDisabled = true;
   let countdown = 60; // seconds
   
   setInterval(() => {
     countdown--;
     if (countdown === 0) {
       resendDisabled = false;
     }
   }, 1000);
   ```

### Password Input Best Practices

1. **Real-time Password Strength Indicator**:
   - Weak (red) → Medium (yellow) → Strong (green)
   - Show which requirements are met/unmet

2. **Password Requirements Checklist**:
   ```
   ✅ At least 8 characters
   ❌ One uppercase letter
   ✅ One lowercase letter
   ❌ One number
   ```

3. **Show/Hide Password Toggle**:
   - Eye icon to toggle visibility
   - Default to hidden (type="password")

### Mobile-Specific Considerations

1. **OTP Auto-Fill**:
   ```html
   <input type="text" autocomplete="one-time-code" />
   ```
   - iOS/Android will auto-detect OTP from SMS

2. **Numeric Keyboard for OTP**:
   ```html
   <input type="tel" inputmode="numeric" pattern="[0-9]*" />
   ```

3. **Email Keyboard**:
   ```html
   <input type="email" inputmode="email" />
   ```

---

## 💻 Code Examples

### React Example (FLOW A: Forgot Password)

```jsx
import { useState } from 'react';
import axios from 'axios';

const ForgotPasswordFlow = () => {
  const [step, setStep] = useState(1); // 1: Email, 2: OTP, 3: Password
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const BASE_URL = 'http://127.0.0.1:8000/api/auth-user';

  // Step 1: Request OTP
  const handleRequestOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${BASE_URL}/forgot-password/`, {
        email: email
      });

      if (response.data.success) {
        setStep(2); // Move to OTP step
        // In DEBUG mode, auto-fill OTP
        if (response.data.data.debug_otp) {
          setOtp(response.data.data.debug_otp);
        }
      }
    } catch (err) {
      if (err.response?.status === 404) {
        setError('Email not found. Please check your email address.');
      } else {
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${BASE_URL}/verify-forgot-password-otp/`, {
        email: email,
        otp_code: otp
      });

      if (response.data.success) {
        setResetToken(response.data.data.reset_token);
        setStep(3); // Move to password step
      }
    } catch (err) {
      const errData = err.response?.data;
      if (errData?.error === 'INVALID_OTP') {
        setError(`Invalid OTP. ${errData.attempts_remaining} attempts remaining.`);
      } else if (errData?.error === 'OTP_EXPIRED') {
        setError('OTP has expired. Please request a new one.');
      } else if (errData?.error === 'MAX_ATTEMPTS_EXCEEDED') {
        setError('Too many failed attempts. Please request a new OTP.');
        setStep(1); // Go back to email step
      } else {
        setError('Failed to verify OTP. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Reset Password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${BASE_URL}/reset-password-with-token/`, {
        reset_token: resetToken,
        new_password: newPassword,
        confirm_password: confirmPassword
      });

      if (response.data.success) {
        alert('Password reset successful! Redirecting to login...');
        // Redirect to login page
        window.location.href = '/login';
      }
    } catch (err) {
      const errData = err.response?.data;
      if (errData?.error === 'TOKEN_EXPIRED') {
        setError('Reset token has expired. Please start again.');
        setStep(1);
      } else if (errData?.errors?.new_password) {
        setError(errData.errors.new_password.join(' '));
      } else {
        setError('Failed to reset password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="forgot-password-flow">
      {step === 1 && (
        <form onSubmit={handleRequestOTP}>
          <h2>Forgot Password</h2>
          <input
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
      )}

      {step === 2 && (
        <form onSubmit={handleVerifyOTP}>
          <h2>Enter OTP</h2>
          <p>OTP sent to {email}</p>
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            pattern="[0-9]{6}"
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
      )}

      {step === 3 && (
        <form onSubmit={handleResetPassword}>
          <h2>Reset Password</h2>
          <input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
      )}
    </div>
  );
};

export default ForgotPasswordFlow;
```

---

### React Example (FLOW B: Profile Password Change)

```jsx
import { useState } from 'react';
import axios from 'axios';

const ProfilePasswordChange = ({ accessToken }) => {
  const [step, setStep] = useState(1); // 1: Request OTP, 2: Verify OTP, 3: New Password
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const BASE_URL = 'http://127.0.0.1:8000/api/auth-user';

  const axiosConfig = {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  };

  // Step 1: Send OTP
  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${BASE_URL}/profile/send-otp/`,
        { action_type: 'PASSWORD_CHANGE' },
        axiosConfig
      );

      if (response.data.success) {
        setStep(2);
        // In DEBUG mode, auto-fill OTP
        if (response.data.data.debug_otp) {
          setOtp(response.data.data.debug_otp);
        }
      }
    } catch (err) {
      if (err.response?.status === 401) {
        setError('Session expired. Please login again.');
      } else {
        setError('Failed to send OTP. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify OTP
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${BASE_URL}/profile/verify-otp/`,
        { otp_code: otp },
        axiosConfig
      );

      if (response.data.success) {
        setStep(3);
      }
    } catch (err) {
      const errData = err.response?.data;
      if (errData?.error === 'INVALID_OTP') {
        setError(`Invalid OTP. ${errData.attempts_remaining} attempts remaining.`);
      } else if (errData?.error === 'OTP_EXPIRED') {
        setError('OTP has expired. Please request a new one.');
      } else {
        setError('Failed to verify OTP. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Change Password
  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axios.post(
        `${BASE_URL}/profile/change-password/`,
        {
          new_password: newPassword,
          confirm_password: confirmPassword
        },
        axiosConfig
      );

      if (response.data.success) {
        setSuccess(true);
        // Reset form after 3 seconds
        setTimeout(() => {
          setStep(1);
          setSuccess(false);
          setOtp('');
          setNewPassword('');
          setConfirmPassword('');
        }, 3000);
      }
    } catch (err) {
      const errData = err.response?.data;
      if (errData?.error === 'OTP_NOT_VERIFIED') {
        setError('Please verify OTP first.');
        setStep(2);
      } else if (errData?.errors?.new_password) {
        setError(errData.errors.new_password.join(' '));
      } else {
        setError('Failed to change password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="success-message">
        <h2>✅ Password Changed Successfully!</h2>
        <p>Your password has been updated.</p>
      </div>
    );
  }

  return (
    <div className="profile-password-change">
      {step === 1 && (
        <div>
          <h2>Change Password</h2>
          <p>We'll send an OTP to your registered email for verification.</p>
          <button onClick={handleSendOTP} disabled={loading}>
            {loading ? 'Sending...' : 'Send OTP to My Email'}
          </button>
          {error && <div className="error">{error}</div>}
        </div>
      )}

      {step === 2 && (
        <form onSubmit={handleVerifyOTP}>
          <h2>Verify OTP</h2>
          <input
            type="text"
            placeholder="Enter 6-digit OTP"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            maxLength={6}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
      )}

      {step === 3 && (
        <form onSubmit={handleChangePassword}>
          <h2>Enter New Password</h2>
          <input
            type="password"
            placeholder="New password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Changing...' : 'Change Password'}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
      )}
    </div>
  );
};

export default ProfilePasswordChange;
```

---

### Flutter/Dart Example (FLOW A)

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ForgotPasswordService {
  static const String baseUrl = 'http://127.0.0.1:8000/api/auth-user';
  
  // Step 1: Request OTP
  static Future<Map<String, dynamic>> requestOTP(String email) async {
    final response = await http.post(
      Uri.parse('$baseUrl/forgot-password/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );
    
    return jsonDecode(response.body);
  }
  
  // Step 2: Verify OTP
  static Future<Map<String, dynamic>> verifyOTP(String email, String otp) async {
    final response = await http.post(
      Uri.parse('$baseUrl/verify-forgot-password-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'otp_code': otp,
      }),
    );
    
    return jsonDecode(response.body);
  }
  
  // Step 3: Reset Password
  static Future<Map<String, dynamic>> resetPassword(
    String resetToken,
    String newPassword,
    String confirmPassword,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/reset-password-with-token/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'reset_token': resetToken,
        'new_password': newPassword,
        'confirm_password': confirmPassword,
      }),
    );
    
    return jsonDecode(response.body);
  }
}
```

---

## ✅ Testing Checklist

### FLOW A: Forgot Password

- [ ] Email input validates format
- [ ] "Email not found" error displays correctly
- [ ] OTP email arrives within 30 seconds
- [ ] OTP input accepts only 6 digits
- [ ] Invalid OTP shows remaining attempts
- [ ] OTP expires after 10 minutes
- [ ] "Resend OTP" works and generates new OTP
- [ ] reset_token expires after 15 minutes
- [ ] Weak password shows specific errors
- [ ] Password mismatch error displays
- [ ] Successful reset redirects to login
- [ ] All user sessions invalidated after reset

### FLOW B: Profile Password Change

- [ ] "Send OTP" requires Bearer token
- [ ] OTP sent to user's registered email
- [ ] OTP expires after 5 minutes (shorter!)
- [ ] Max 3 OTP attempts enforced
- [ ] Cannot change password without OTP verification
- [ ] Weak password validation works
- [ ] Success message displays in profile
- [ ] User stays logged in after change
- [ ] Confirmation email received

### Edge Cases

- [ ] Network timeout handling
- [ ] Multiple rapid OTP requests (rate limiting)
- [ ] Token expiry during multi-step flow
- [ ] Browser back button during flow
- [ ] Page refresh doesn't break flow state
- [ ] Mobile keyboard types (email, numeric, text)
- [ ] Copy-paste OTP from email works
- [ ] Screen reader accessibility

---

## 🔒 Security Best Practices

### For Frontend Developers

1. **Never Store Sensitive Data in localStorage**:
   - ❌ Bad: `localStorage.setItem('reset_token', token)`
   - ✅ Good: Store in React state or memory

2. **Always Use HTTPS in Production**:
   - Development: `http://127.0.0.1:8000`
   - Production: `https://api.credbuzz.com`

3. **Validate User Input**:
   ```javascript
   // Email validation
   const isValidEmail = (email) => {
     return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
   };
   
   // Password validation
   const isStrongPassword = (password) => {
     return password.length >= 8 &&
            /[A-Z]/.test(password) &&
            /[a-z]/.test(password) &&
            /[0-9]/.test(password);
   };
   ```

4. **Clear Sensitive Data After Use**:
   ```javascript
   // After successful password reset
   setOtp('');
   setResetToken('');
   setNewPassword('');
   setConfirmPassword('');
   ```

5. **Handle Token Expiry Gracefully**:
   ```javascript
   axios.interceptors.response.use(
     response => response,
     error => {
       if (error.response?.status === 401) {
         // Redirect to login
         window.location.href = '/login';
       }
       return Promise.reject(error);
     }
   );
   ```

---

## 📞 Support & Questions

### For Help

- **Backend API Docs**: See `docs/PASSWORD_RESET_FLOWS.md`
- **Postman Collection**: `docs/postman/CredBuzz_Password_Reset_Flows.postman_collection.json`
- **API Base URL**: `http://127.0.0.1:8000/api/auth-user`

### Common Questions

**Q: Can I use the old `/reset-password/` endpoint?**  
A: Yes, but it's deprecated. Migrate to new flows within 3-6 months.

**Q: What's the difference between FLOW A and FLOW B?**  
A: FLOW A is for unauthenticated users (uses reset_token), FLOW B is for authenticated users (uses access_token).

**Q: Why do OTP expiry times differ?**  
A: Authenticated users (5 min) have stricter security. Unauthenticated users (10 min) need more time to check email.

**Q: Can I skip OTP verification?**  
A: No, OTP is mandatory for all password changes (step-up authentication).

**Q: What happens to other sessions after password reset?**  
A: FLOW A invalidates all sessions. FLOW B keeps current session active.

---

## 🎓 Conclusion

You now have everything needed to implement secure password management in your frontend:

✅ **Two distinct flows** for different user contexts  
✅ **Step-by-step API integration** with examples  
✅ **Error handling** for all scenarios  
✅ **UI/UX best practices** for great user experience  
✅ **Security recommendations** to protect users  

**Ready to implement? Start with FLOW A (Forgot Password) on your login screen!**

---

**Version**: 2.0  
**Last Updated**: January 13, 2026  
**Maintained by**: CredBuzz Backend Team
