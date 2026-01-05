# Bill Pay API Documentation

## Overview

The Bill Pay module provides APIs for paying utility bills, recharges, and other payments. It supports multiple bill categories and billers with features like bill fetch, payment, payment history, and saved billers.

**Base URL:** `http://127.0.0.1:8000/api/bills`

**Authentication:** All endpoints require JWT Bearer token authentication.

---

## Table of Contents

1. [Bill Categories](#1-bill-categories)
2. [Billers](#2-billers)
3. [Bill Fetch & Payment](#3-bill-fetch--payment)
4. [Payment History](#4-payment-history)
5. [Saved Billers](#5-saved-billers)
6. [Quick Access](#6-quick-access)

---

## Bill Pay Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BILL PAYMENT FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Browse Categories & Billers                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ GET /api/bills/categories/        → List all bill categories         │   │
│  │ GET /api/bills/billers/           → List billers (filter by category)│   │
│  │ GET /api/bills/billers/<id>/      → Get biller details               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 2: Fetch Bill                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /api/bills/fetch/                                               │   │
│  │ Body: biller_id, consumer_number                                     │   │
│  │ Response: Bill details with amount, due date, fees                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 3: Pay Bill                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /api/bills/pay/                                                 │   │
│  │ Body: biller_id, consumer_number, amount, payment_method             │   │
│  │ Response: Payment confirmation with transaction_id                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓                                              │
│  STEP 4: View Payment Status                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ GET /api/bills/payments/<transaction_id>/                            │   │
│  │ Response: Complete payment details                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Bill Categories

### 1.1 List All Categories

**Endpoint:** `GET /api/bills/categories/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Bill categories retrieved successfully.",
    "data": {
        "categories": [
            {
                "id": 1,
                "name": "Electricity",
                "code": "ELECTRICITY",
                "description": "Electricity bill payments",
                "icon": "zap",
                "is_active": true,
                "display_order": 1,
                "billers_count": 5
            },
            {
                "id": 2,
                "name": "Gas",
                "code": "GAS",
                "description": "Gas bill payments",
                "icon": "flame",
                "is_active": true,
                "display_order": 2,
                "billers_count": 3
            }
        ]
    }
}
```

**Available Categories:**
| Code | Name | Icon |
|------|------|------|
| ELECTRICITY | Electricity | zap |
| GAS | Gas | flame |
| WATER | Water | droplet |
| MOBILE_PREPAID | Mobile Prepaid | smartphone |
| MOBILE_POSTPAID | Mobile Postpaid | phone |
| DTH | DTH | tv |
| BROADBAND | Broadband | wifi |
| LANDLINE | Landline | phone-call |
| INSURANCE | Insurance | shield |
| CREDIT_CARD | Credit Card | credit-card |
| LOAN_EMI | Loan EMI | dollar-sign |
| MUNICIPAL_TAX | Municipal Tax | building |

---

## 2. Billers

### 2.1 List Billers

**Endpoint:** `GET /api/bills/billers/`  
**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category_id | integer | Filter by category ID |
| category_code | string | Filter by category code (e.g., ELECTRICITY) |
| search | string | Search by biller name or code |
| featured | boolean | Filter featured billers only |

**Example Requests:**
```
GET /api/bills/billers/
GET /api/bills/billers/?category_id=1
GET /api/bills/billers/?category_code=ELECTRICITY
GET /api/bills/billers/?search=tata
GET /api/bills/billers/?featured=true
```

**Response:**
```json
{
    "success": true,
    "message": "Billers retrieved successfully.",
    "data": {
        "billers": [
            {
                "id": 1,
                "name": "Adani Electricity Mumbai",
                "code": "ADANI_ELEC_MUM",
                "logo": null,
                "category_name": "Electricity",
                "is_featured": true
            },
            {
                "id": 2,
                "name": "Tata Power Mumbai",
                "code": "TATA_POWER_MUM",
                "logo": "/media/billers/logos/tata.png",
                "category_name": "Electricity",
                "is_featured": true
            }
        ],
        "count": 2
    }
}
```

### 2.2 Get Biller Details

**Endpoint:** `GET /api/bills/billers/<biller_id>/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Biller details retrieved successfully.",
    "data": {
        "biller": {
            "id": 1,
            "category": 1,
            "category_name": "Electricity",
            "category_code": "ELECTRICITY",
            "name": "Adani Electricity Mumbai",
            "code": "ADANI_ELEC_MUM",
            "description": "Pay your Adani Electricity bills",
            "logo": null,
            "min_amount": "10.00",
            "max_amount": "100000.00",
            "required_fields": {
                "consumer_number": {
                    "label": "Consumer Number",
                    "type": "text",
                    "required": true,
                    "pattern": "^[0-9]{10,12}$"
                }
            },
            "platform_fee": "5.00",
            "platform_fee_type": "FIXED",
            "is_active": true,
            "is_featured": true
        }
    }
}
```

---

## 3. Bill Fetch & Payment

### 3.1 Fetch Bill

**Endpoint:** `POST /api/bills/fetch/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "biller_id": 1,
    "consumer_number": "1234567890",
    "additional_params": {}
}
```

**Response:**
```json
{
    "success": true,
    "message": "Bill fetched successfully.",
    "data": {
        "bill": {
            "consumer_number": "1234567890",
            "consumer_name": "John Doe",
            "bill_amount": "1500.00",
            "bill_date": "2025-12-01",
            "due_date": "2025-12-23",
            "bill_number": "BILL20251208001",
            "bill_period": "December 2025",
            "additional_info": {
                "last_payment_date": "2025-11-15",
                "last_payment_amount": "1200.00"
            },
            "platform_fee": "5.00",
            "total_amount": "1505.00"
        },
        "biller": {
            "id": 1,
            "name": "Adani Electricity Mumbai",
            "code": "ADANI_ELEC_MUM",
            "logo": null,
            "category_name": "Electricity",
            "is_featured": true
        }
    }
}
```

### 3.2 Pay Bill

**Endpoint:** `POST /api/bills/pay/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "biller_id": 1,
    "consumer_number": "1234567890",
    "amount": 1500.00,
    "payment_method": "WALLET",
    "consumer_name": "John Doe",
    "bill_date": "2025-12-01",
    "due_date": "2025-12-23",
    "bill_number": "BILL20251208001",
    "bill_period": "December 2025"
}
```

**Payment Methods:**
| Method | Description |
|--------|-------------|
| WALLET | Pay from CredBuzz wallet |
| UPI | Pay via UPI |
| CARD | Pay via Credit/Debit Card |
| NETBANKING | Pay via Net Banking |

**Response:**
```json
{
    "success": true,
    "message": "Bill payment successful.",
    "data": {
        "payment": {
            "id": 1,
            "transaction_id": "BP20251208123456ABC123",
            "biller": 1,
            "biller_name": "Adani Electricity Mumbai",
            "biller_code": "ADANI_ELEC_MUM",
            "category_name": "Electricity",
            "consumer_number": "1234567890",
            "consumer_name": "John Doe",
            "bill_amount": "1500.00",
            "platform_fee": "5.00",
            "total_amount": "1505.00",
            "bill_date": "2025-12-01",
            "due_date": "2025-12-23",
            "bill_number": "BILL20251208001",
            "bill_period": "December 2025",
            "status": "SUCCESS",
            "status_display": "Success",
            "payment_method": "WALLET",
            "biller_ref_number": "REF20251208123456",
            "initiated_at": "2025-12-08T10:30:00Z",
            "completed_at": "2025-12-08T10:30:05Z",
            "failure_reason": ""
        }
    }
}
```

**Payment Status Values:**
| Status | Description |
|--------|-------------|
| INITIATED | Payment initiated |
| PENDING | Waiting for confirmation |
| PROCESSING | Being processed |
| SUCCESS | Payment successful |
| FAILED | Payment failed |
| REFUNDED | Payment refunded |
| CANCELLED | Payment cancelled |

---

## 4. Payment History

### 4.1 Get Payment History

**Endpoint:** `GET /api/bills/history/`  
**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status (SUCCESS, FAILED, etc.) |
| category_id | integer | Filter by category ID |
| biller_id | integer | Filter by biller ID |
| start_date | date | Filter payments from this date |
| end_date | date | Filter payments until this date |
| page | integer | Page number (default: 1) |
| page_size | integer | Items per page (default: 20, max: 100) |

**Example Requests:**
```
GET /api/bills/history/
GET /api/bills/history/?status=SUCCESS
GET /api/bills/history/?category_id=1&start_date=2025-12-01
GET /api/bills/history/?page=2&page_size=10
```

**Response:**
```json
{
    "success": true,
    "message": "Payment history retrieved successfully.",
    "data": {
        "payments": [
            {
                "id": 1,
                "transaction_id": "BP20251208123456ABC123",
                "biller_name": "Adani Electricity Mumbai",
                "category_name": "Electricity",
                "consumer_number": "1234567890",
                "total_amount": "1505.00",
                "status": "SUCCESS",
                "initiated_at": "2025-12-08T10:30:00Z",
                "completed_at": "2025-12-08T10:30:05Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total_count": 1,
            "total_pages": 1
        }
    }
}
```

### 4.2 Get Payment Details

**Endpoint:** `GET /api/bills/payments/<transaction_id>/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Payment details retrieved successfully.",
    "data": {
        "payment": {
            "id": 1,
            "transaction_id": "BP20251208123456ABC123",
            "biller": 1,
            "biller_name": "Adani Electricity Mumbai",
            "biller_code": "ADANI_ELEC_MUM",
            "category_name": "Electricity",
            "consumer_number": "1234567890",
            "consumer_name": "John Doe",
            "bill_amount": "1500.00",
            "platform_fee": "5.00",
            "total_amount": "1505.00",
            "bill_date": "2025-12-01",
            "due_date": "2025-12-23",
            "bill_number": "BILL20251208001",
            "bill_period": "December 2025",
            "status": "SUCCESS",
            "status_display": "Success",
            "payment_method": "WALLET",
            "biller_ref_number": "REF20251208123456",
            "initiated_at": "2025-12-08T10:30:00Z",
            "completed_at": "2025-12-08T10:30:05Z",
            "failure_reason": ""
        }
    }
}
```

---

## 5. Saved Billers

### 5.1 List Saved Billers

**Endpoint:** `GET /api/bills/saved/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Saved billers retrieved successfully.",
    "data": {
        "saved_billers": [
            {
                "id": 1,
                "biller": 1,
                "biller_name": "Adani Electricity Mumbai",
                "biller_code": "ADANI_ELEC_MUM",
                "category_name": "Electricity",
                "biller_logo": null,
                "consumer_number": "1234567890",
                "nickname": "Home Electricity",
                "is_autopay_enabled": false,
                "autopay_amount_limit": null,
                "created_at": "2025-12-08T10:00:00Z"
            }
        ]
    }
}
```

### 5.2 Save a Biller

**Endpoint:** `POST /api/bills/saved/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "biller": 1,
    "consumer_number": "1234567890",
    "nickname": "Home Electricity",
    "is_autopay_enabled": false,
    "autopay_amount_limit": null
}
```

**Response:**
```json
{
    "success": true,
    "message": "Biller saved successfully.",
    "data": {
        "saved_biller": {
            "id": 1,
            "biller": 1,
            "biller_name": "Adani Electricity Mumbai",
            "biller_code": "ADANI_ELEC_MUM",
            "category_name": "Electricity",
            "biller_logo": null,
            "consumer_number": "1234567890",
            "nickname": "Home Electricity",
            "is_autopay_enabled": false,
            "autopay_amount_limit": null,
            "created_at": "2025-12-08T10:00:00Z"
        }
    }
}
```

### 5.3 Get Saved Biller Details

**Endpoint:** `GET /api/bills/saved/<id>/`  
**Auth Required:** Yes

### 5.4 Update Saved Biller

**Endpoint:** `PUT /api/bills/saved/<id>/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "nickname": "Updated Nickname",
    "is_autopay_enabled": true,
    "autopay_amount_limit": 5000.00
}
```

### 5.5 Delete Saved Biller

**Endpoint:** `DELETE /api/bills/saved/<id>/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Saved biller removed successfully."
}
```

---

## 6. Quick Access

### 6.1 Featured Billers

**Endpoint:** `GET /api/bills/featured/`  
**Auth Required:** Yes

Returns top 10 featured billers for quick access on home screen.

**Response:**
```json
{
    "success": true,
    "message": "Featured billers retrieved successfully.",
    "data": {
        "featured_billers": [
            {
                "id": 1,
                "name": "Adani Electricity Mumbai",
                "code": "ADANI_ELEC_MUM",
                "logo": null,
                "category_name": "Electricity",
                "is_featured": true
            }
        ]
    }
}
```

### 6.2 Recent Payments

**Endpoint:** `GET /api/bills/recent/`  
**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Number of recent payments (default: 5) |

**Response:**
```json
{
    "success": true,
    "message": "Recent payments retrieved successfully.",
    "data": {
        "recent_payments": [
            {
                "id": 1,
                "transaction_id": "BP20251208123456ABC123",
                "biller_name": "Adani Electricity Mumbai",
                "category_name": "Electricity",
                "consumer_number": "1234567890",
                "total_amount": "1505.00",
                "status": "SUCCESS",
                "initiated_at": "2025-12-08T10:30:00Z",
                "completed_at": "2025-12-08T10:30:05Z"
            }
        ]
    }
}
```

---

## Error Responses

### 400 Bad Request
```json
{
    "success": false,
    "message": "Invalid request.",
    "errors": {
        "biller_id": ["This field is required."],
        "consumer_number": ["This field is required."]
    }
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 404 Not Found
```json
{
    "success": false,
    "message": "Biller not found."
}
```

### 429 Too Many Requests
```json
{
    "detail": "Request was throttled. Expected available in 60 seconds."
}
```

---

## Rate Limits

| Endpoint Type | Rate Limit |
|---------------|------------|
| Bill Fetch | 100 requests/hour |
| Bill Payment | 50 requests/hour |
| Other Endpoints | 1000 requests/hour |

---

## Security Features

1. **JWT Authentication** - All endpoints require valid access token
2. **Rate Limiting** - Prevent abuse and DDoS attacks
3. **Transaction Logging** - All payments are logged for audit
4. **Bill Fetch Logging** - All bill fetch attempts are logged
5. **Amount Validation** - Min/max amount limits per biller

---

## Database Models

### BillCategory
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String | Category name |
| code | String | Unique category code |
| description | Text | Category description |
| icon | String | Icon name for frontend |
| is_active | Boolean | Active status |
| display_order | Integer | Display order |

### Biller
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| category | FK | Reference to BillCategory |
| name | String | Biller name |
| code | String | Unique biller code |
| min_amount | Decimal | Minimum payment amount |
| max_amount | Decimal | Maximum payment amount |
| required_fields | JSON | Fields required for bill fetch |
| platform_fee | Decimal | Platform fee amount |
| platform_fee_type | String | FIXED or PERCENTAGE |
| is_active | Boolean | Active status |
| is_featured | Boolean | Featured on home screen |

### BillPayment
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| transaction_id | String | Unique transaction ID (BP...) |
| user | FK | Reference to User |
| biller | FK | Reference to Biller |
| consumer_number | String | Consumer/Account number |
| bill_amount | Decimal | Bill amount |
| platform_fee | Decimal | Platform fee |
| total_amount | Decimal | Total amount charged |
| status | String | Payment status |
| payment_method | String | WALLET/UPI/CARD/NETBANKING |
| initiated_at | DateTime | Payment initiated time |
| completed_at | DateTime | Payment completed time |

### SavedBiller
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| user | FK | Reference to User |
| biller | FK | Reference to Biller |
| consumer_number | String | Saved consumer number |
| nickname | String | User-friendly name |
| is_autopay_enabled | Boolean | Auto-pay enabled |
| autopay_amount_limit | Decimal | Max auto-pay amount |

---

## 7. Bank Account Management

### 7.1 List Bank Accounts

**Endpoint:** `GET /api/bills/bank-accounts/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Bank accounts retrieved successfully.",
    "data": {
        "bank_accounts": [
            {
                "id": 1,
                "account_holder_name": "John Doe",
                "account_number_masked": "XXXXXX1234",
                "ifsc_code": "SBIN0001234",
                "bank_name": "State Bank of India",
                "branch_name": "Mumbai Main",
                "account_type": "SAVINGS",
                "is_verified": true,
                "verification_status": "VERIFIED",
                "is_primary": true,
                "nickname": "Salary Account",
                "created_at": "2025-12-10T10:00:00Z"
            }
        ],
        "count": 1
    }
}
```

### 7.2 Add Bank Account

**Endpoint:** `POST /api/bills/bank-accounts/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "account_holder_name": "John Doe",
    "account_number": "123456789012",
    "confirm_account_number": "123456789012",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India",
    "branch_name": "Mumbai Main",
    "account_type": "SAVINGS",
    "is_primary": false,
    "nickname": "Salary Account"
}
```

### 7.3 Get/Update/Delete Bank Account

**Endpoints:**
- `GET /api/bills/bank-accounts/<id>/` - Get details
- `PUT /api/bills/bank-accounts/<id>/` - Update (nickname, is_primary only)
- `DELETE /api/bills/bank-accounts/<id>/` - Soft delete

### 7.4 Verify Bank Account

**Endpoint:** `POST /api/bills/bank-accounts/<id>/verify/`  
**Auth Required:** Yes

Verifies bank account ownership (mock implementation - uses penny drop in production).

---

## 8. Card Management

### 8.1 List Cards

**Endpoint:** `GET /api/bills/cards/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "Cards retrieved successfully.",
    "data": {
        "cards": [
            {
                "id": 1,
                "card_number_masked": "XXXX-XXXX-XXXX-1111",
                "card_last_four": "1111",
                "card_holder_name": "John Doe",
                "expiry_display": "12/28",
                "is_expired": false,
                "card_type": "DEBIT",
                "card_network": "VISA",
                "is_verified": true,
                "is_primary": true,
                "nickname": "Primary Card"
            }
        ],
        "count": 1
    }
}
```

### 8.2 Add Card

**Endpoint:** `POST /api/bills/cards/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "card_number": "4111111111111111",
    "card_holder_name": "John Doe",
    "expiry_month": "12",
    "expiry_year": "2028",
    "card_type": "DEBIT",
    "card_network": "VISA",
    "issuing_bank": "HDFC Bank",
    "is_primary": false,
    "nickname": "Shopping Card"
}
```

**Card Types:** DEBIT, CREDIT, PREPAID  
**Card Networks:** VISA, MASTERCARD, RUPAY, AMEX, DINERS

### 8.3 Get/Update/Delete Card

**Endpoints:**
- `GET /api/bills/cards/<id>/` - Get details
- `PUT /api/bills/cards/<id>/` - Update (nickname, is_primary only)
- `DELETE /api/bills/cards/<id>/` - Soft delete

---

## 9. MPIN Management

### 9.1 Check MPIN Status

**Endpoint:** `GET /api/bills/mpin/setup/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "data": {
        "has_mpin": false
    }
}
```

### 9.2 Setup MPIN

**Endpoint:** `POST /api/bills/mpin/setup/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "mpin": "123456",
    "confirm_mpin": "123456",
    "password": "user_password"
}
```

MPIN must be 6 digits. User password is required for verification.

### 9.3 Verify MPIN

**Endpoint:** `POST /api/bills/mpin/verify/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "mpin": "123456"
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "MPIN verified successfully.",
    "data": {
        "verified": true
    }
}
```

**Response (Failed):**
```json
{
    "success": false,
    "message": "Invalid MPIN. 2 attempts remaining.",
    "data": {
        "verified": false,
        "remaining_attempts": 2
    }
}
```

Note: MPIN is locked for 30 minutes after 3 failed attempts.

### 9.4 Change MPIN

**Endpoint:** `POST /api/bills/mpin/change/`  
**Auth Required:** Yes

**Request Body:**
```json
{
    "current_mpin": "123456",
    "new_mpin": "654321",
    "confirm_mpin": "654321"
}
```

---

## 10. Payment Gateways

### 10.1 List Payment Gateways

**Endpoint:** `GET /api/bills/gateways/`  
**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter by gateway type (UPI, CARD, NETBANKING, WALLET) |

**Response:**
```json
{
    "success": true,
    "message": "Payment gateways retrieved successfully.",
    "data": {
        "gateways": [
            {
                "id": 1,
                "name": "Razorpay",
                "code": "RAZORPAY",
                "gateway_type": "UPI",
                "min_amount": "1.00",
                "max_amount": "100000.00",
                "transaction_fee": "0.00",
                "fee_type": "FIXED",
                "is_active": true
            }
        ]
    }
}
```

---

## 11. IFSC Verification

### 11.1 Verify IFSC Code

**Endpoint:** `GET /api/bills/ifsc/<ifsc_code>/`  
**Auth Required:** Yes

**Response:**
```json
{
    "success": true,
    "message": "IFSC code verified successfully.",
    "data": {
        "ifsc_code": "SBIN0001234",
        "bank_name": "State Bank of India",
        "branch_name": "Mumbai Branch",
        "address": "Mumbai, India",
        "city": "Mumbai",
        "state": "Maharashtra",
        "contact": "+91-1800-XXX-XXXX"
    }
}
```

---

## 12. Transaction Logs

### 12.1 List Transactions

**Endpoint:** `GET /api/bills/transactions/`  
**Auth Required:** Yes

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | BILL_PAYMENT, MONEY_TRANSFER, WALLET_TOPUP, REFUND, REVERSAL |
| status | string | INITIATED, PENDING, PROCESSING, SUCCESS, FAILED, REFUNDED |
| start_date | date | Filter from date |
| end_date | date | Filter until date |
| page | integer | Page number |
| page_size | integer | Items per page (max 100) |

**Response:**
```json
{
    "success": true,
    "message": "Transaction logs retrieved successfully.",
    "data": {
        "transactions": [
            {
                "id": 1,
                "transaction_id": "TXN20251210123456ABC",
                "transaction_type": "MONEY_TRANSFER",
                "status": "SUCCESS",
                "amount": "5000.00",
                "fee": "0.00",
                "total_amount": "5000.00",
                "currency": "INR",
                "payment_method": "NEFT",
                "gateway_name": null,
                "description": "Transfer to John Doe",
                "initiated_at": "2025-12-10T10:00:00Z",
                "completed_at": "2025-12-10T10:00:05Z"
            }
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total_count": 1,
            "total_pages": 1
        }
    }
}
```

### 12.2 Get Transaction Details

**Endpoint:** `GET /api/bills/transactions/<transaction_id>/`  
**Auth Required:** Yes

Returns detailed transaction information including source account, destination details, and gateway response.

---

## 13. Money Transfer

### 13.1 Transfer Money

**Endpoint:** `POST /api/bills/transfer/`  
**Auth Required:** Yes

**Prerequisites:**
1. User must have a verified bank account
2. User must have MPIN set up

**Request Body:**
```json
{
    "source_bank_account_id": 1,
    "beneficiary_name": "Jane Doe",
    "beneficiary_account_number": "987654321012",
    "beneficiary_ifsc": "HDFC0001234",
    "amount": 5000.00,
    "remarks": "Rent payment",
    "mpin": "123456"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Money transfer initiated successfully.",
    "data": {
        "transaction": {
            "id": 1,
            "transaction_id": "TXN20251210123456ABC",
            "transaction_type": "MONEY_TRANSFER",
            "status": "SUCCESS",
            "amount": "5000.00",
            "fee": "0.00",
            "total_amount": "5000.00",
            "currency": "INR",
            "payment_method": "NEFT",
            "description": "Transfer to Jane Doe",
            "initiated_at": "2025-12-10T10:00:00Z",
            "completed_at": "2025-12-10T10:00:05Z"
        }
    }
}
```

---

## New Database Models

### UserBankAccount
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| user | FK | Reference to User |
| account_holder_name | String | Account holder name |
| account_number_encrypted | String | Encrypted account number |
| ifsc_code | String | IFSC code |
| bank_name | String | Bank name |
| is_verified | Boolean | Verification status |
| is_primary | Boolean | Primary account flag |

### UserCard
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| user | FK | Reference to User |
| card_number_encrypted | String | Encrypted card number |
| card_last_four | String | Last 4 digits |
| card_holder_name | String | Cardholder name |
| expiry_month | String | Expiry month (MM) |
| expiry_year | String | Expiry year (YYYY) |
| card_type | String | DEBIT/CREDIT/PREPAID |
| card_network | String | VISA/MASTERCARD/RUPAY/AMEX |

### UserMPIN
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| user | FK | One-to-one with User |
| mpin_hash | String | Hashed MPIN |
| mpin_salt | String | Salt for hashing |
| failed_attempts | Integer | Failed attempt count |
| is_locked | Boolean | Lock status |
| locked_until | DateTime | Lock expiry time |

### PaymentGateway
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | String | Gateway name |
| code | String | Unique code |
| gateway_type | String | UPI/CARD/NETBANKING/WALLET |
| is_active | Boolean | Active status |
| min_amount | Decimal | Minimum transaction amount |
| max_amount | Decimal | Maximum transaction amount |

### TransactionLog
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| transaction_id | String | Unique transaction ID (TXN...) |
| user | FK | Reference to User |
| transaction_type | String | Type of transaction |
| status | String | Transaction status |
| amount | Decimal | Transaction amount |
| fee | Decimal | Transaction fee |
| total_amount | Decimal | Total amount |
| payment_method | String | Payment method used |
| payment_gateway | FK | Reference to PaymentGateway |
| initiated_at | DateTime | Transaction start time |
| completed_at | DateTime | Transaction end time |

