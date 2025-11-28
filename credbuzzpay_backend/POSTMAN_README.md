# CredBuzz Users Auth API - Postman Collection

## Collection Details
- **Workspace**: CredBuzz Backend
- **Collection**: CredBuzz Users Auth API
- **Environment**: CredBuzz Local

## How to Access
1. Open Postman (Desktop App or Web)
2. Go to Workspaces and find "CredBuzz Backend"
3. The collection "CredBuzz Users Auth API" with 15 requests is available

## ⚠️ Important: Testing Locally
The Postman Cloud Collection Runner **cannot** reach `localhost` or `127.0.0.1`. To test the API:

### Option 1: Use Postman Desktop App
1. Open Postman Desktop App
2. Navigate to the collection
3. Select the "CredBuzz Local" environment
4. Run requests individually or use the Collection Runner

### Option 2: Use a Public URL (for Cloud Testing)
If you want to use Postman's cloud runner, you need to:
1. Deploy the API to a public server, OR
2. Use a tunneling service like ngrok:
   ```bash
   ngrok http 8000
   ```
3. Update the `base_url` in the environment to the ngrok URL

## API Endpoints

### Authentication
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 1 | Register User | POST | `/api/auth/register/` |
| 2 | Login User | POST | `/api/auth/login/` |
| 11 | Refresh Token | POST | `/api/auth/refresh-token/` |
| 15 | Logout | POST | `/api/auth/logout/` |

### User Profile
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 3 | Get Profile | GET | `/api/auth/profile/` |
| 4 | Update Profile | PUT | `/api/auth/profile/` |

### Password Management
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 8 | Forgot Password | POST | `/api/auth/forgot-password/` |
| 9 | Reset Password | POST | `/api/auth/reset-password/` |
| 10 | Change Password | POST | `/api/auth/change-password/` |

### User Management
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 5 | List Users | GET | `/api/auth/users/` |
| 6 | Get User by ID | GET | `/api/auth/users/{id}/` |
| 7 | Update User by ID | PUT | `/api/auth/users/{id}/` |
| 12 | Delete User | DELETE | `/api/auth/users/{id}/` |
| 13 | Activate User | POST | `/api/auth/users/{id}/activate/` |
| 14 | Deactivate User | POST | `/api/auth/users/{id}/deactivate/` |

## Environment Variables
The "CredBuzz Local" environment contains:
- `base_url`: `http://127.0.0.1:8000`
- `access_token`: Auto-populated after login/register
- `refresh_token`: Auto-populated after login/register
- `reset_token`: Auto-populated after forgot password
- `user_id`: Auto-populated after login/register

## Test Scripts
Each request has test scripts that:
1. Validate response status codes
2. Automatically save tokens to environment variables
3. Verify response structure

## Testing Order (Recommended)
1. **Register User** or **Login User** first (to get tokens)
2. **Get Profile** - verify authentication works
3. **Update Profile** - test profile update
4. **List Users** - get all users
5. **Get User by ID** - get specific user
6. **Update User by ID** - update specific user
7. **Forgot Password** - request reset token
8. **Reset Password** - reset with token
9. **Change Password** - change authenticated user password
10. **Refresh Token** - get new access token
11. **Delete/Activate/Deactivate User** - user management
12. **Logout** - end session

## Running Tests Locally via Command Line
All 24 Django unit tests pass:
```bash
python manage.py test users_auth
```

## Manual cURL Tests
```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test@1234","confirm_password":"Test@1234","first_name":"Test","last_name":"User"}'

# Login
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@1234"}'

# Get Profile (with token)
curl -X GET http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```
