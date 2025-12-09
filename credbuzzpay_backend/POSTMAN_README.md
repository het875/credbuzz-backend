# CredBuzz Backend API - Postman Collection

## 📁 Collection Location
The Postman collection and environment files are located in:
```
docs/postman/
├── CredBuzz_Backend_API.postman_collection.json
└── CredBuzz_Backend_Local.postman_environment.json
```

## Collection Details
- **Workspace**: CredBuzz Backend
- **Collection**: CredBuzz Backend API
- **Environment**: CredBuzz Backend - Local

## 🔐 Security Features
- **Dynamic Login**: Single `identifier` field supports email, username, user_code, or phone
- **Progressive Lockout**: 2min → 5min → 10min → 30min → 60min → blocked
- **JWT with Enhanced Payload**: Includes user_code, user_role, app_access, feature_access
- **30-minute Inactivity Timeout**: Token invalidates after inactivity

## ⚠️ Important: Testing Locally
The Postman Cloud Collection Runner **cannot** reach `localhost` or `127.0.0.1`. To test the API:

### Option 1: Use Postman Desktop App
1. Open Postman Desktop App
2. Import the collection from `docs/postman/CredBuzz_Backend_API.postman_collection.json`
3. Import the environment from `docs/postman/CredBuzz_Backend_Local.postman_environment.json`
4. Select the "CredBuzz Backend - Local" environment
5. Run requests individually or use the Collection Runner

### Option 2: Use a Public URL (for Cloud Testing)
If you want to use Postman's cloud runner, you need to:
1. Deploy the API to a public server, OR
2. Use a tunneling service like ngrok:
   ```bash
   ngrok http 8000
   ```
3. Update the `base_url` in the environment to the ngrok URL

## 🚀 Quick Start Credentials
| Role | Identifier | Password |
|------|------------|----------|
| Developer | `dev@credbuzz.com` or `developer` or `CGX0R0` | `Developer@123` |
| Super Admin | `superadmin@credbuzz.com` or `superadmin` or `VYO541` | `SuperAdmin@123` |

## API Endpoints

### Authentication
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 1 | Register User | POST | `/api/auth/register/` |
| 2 | Login User | POST | `/api/auth/login/` |
| 3 | Refresh Token | POST | `/api/auth/refresh-token/` |
| 4 | Logout | POST | `/api/auth/logout/` |

### User Profile
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 5 | Get Profile | GET | `/api/auth/profile/` |
| 6 | Update Profile | PUT | `/api/auth/profile/` |

### Password Management
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 7 | Forgot Password | POST | `/api/auth/forgot-password/` |
| 8 | Reset Password | POST | `/api/auth/reset-password/` |
| 9 | Change Password | POST | `/api/auth/change-password/` |

### User Management
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 10 | List Users | GET | `/api/auth/users/` |
| 11 | Get User by ID | GET | `/api/auth/users/{id}/` |
| 12 | Update User by ID | PUT | `/api/auth/users/{id}/` |
| 13 | Delete User | DELETE | `/api/auth/users/{id}/` |
| 14 | Activate User | POST | `/api/auth/users/{id}/activate/` |
| 15 | Deactivate User | POST | `/api/auth/users/{id}/deactivate/` |

### RBAC (Role-Based Access Control)
| # | Request | Method | Endpoint |
|---|---------|--------|----------|
| 16 | List Roles | GET | `/api/rbac/roles/` |
| 17 | Create Role | POST | `/api/rbac/roles/` |
| 18 | List Apps | GET | `/api/rbac/apps/` |
| 19 | Create App | POST | `/api/rbac/apps/` |
| 20 | List Features | GET | `/api/rbac/features/` |
| 21 | Create Feature | POST | `/api/rbac/features/` |

## Dynamic Login Format
The login endpoint accepts a single `identifier` field that auto-detects the type:

```json
{
    "identifier": "dev@credbuzz.com",
    "password": "Developer@123"
}
```

### Auto-Detection Rules
| Input Pattern | Detected As | Example |
|---------------|-------------|---------|
| Contains `@` | Email | `user@example.com` |
| Starts with `+` or 10+ digits | Phone | `+1234567890` |
| Exactly 6 alphanumeric | User Code | `CGX0R0` |
| Default | Username | `developer` |

## Login Response Structure
```json
{
    "access": "eyJhbG...",
    "refresh": "eyJhbG...",
    "user": {
        "id": 1,
        "email": "dev@credbuzz.com",
        "username": "developer",
        "user_code": "CGX0R0",
        "user_role": "DEVELOPER",
        "first_name": "Dev",
        "last_name": "User"
    },
    "app_access": ["Mobile App", "Web App"],
    "feature_access": ["Dashboard", "Reports"]
}
```

## Environment Variables
The "CredBuzz Backend - Local" environment contains:
- `base_url`: `http://127.0.0.1:8000/api`
- `access_token`: Auto-populated after login/register
- `refresh_token`: Auto-populated after login/register
- `user_id`: Auto-populated after login
- `user_code`: Auto-populated after login
- `user_role`: Auto-populated after login
- `role_id`: For RBAC testing
- `app_id`: For RBAC testing
- `feature_id`: For RBAC testing

## Test Scripts
Each request has test scripts that:
1. Validate response status codes
2. Automatically save tokens to environment variables
3. Verify response structure

## Testing Order (Recommended)
1. **Quick Start > Login as Developer** - Get tokens quickly
2. **Get Profile** - Verify authentication works
3. **Update Profile** - Test profile update
4. **List Users** - Get all users
5. **RBAC endpoints** - Test role-based access
6. **Logout** - End session

## Running Tests Locally via Command Line
All 41 Django unit tests pass:
```bash
python manage.py test users_auth
```

## Manual cURL Tests
```bash
# Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test@1234","confirm_password":"Test@1234","first_name":"Test","last_name":"User"}'

# Login (with email)
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"dev@credbuzz.com","password":"Developer@123"}'

# Login (with username)
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"developer","password":"Developer@123"}'

# Login (with user_code)
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"identifier":"CGX0R0","password":"Developer@123"}'

# Get Profile (with token)
curl -X GET http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```
