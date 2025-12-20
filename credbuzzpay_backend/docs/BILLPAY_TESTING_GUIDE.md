# Bill Pay API Testing Guide

## Quick Start

### Prerequisites
1. Server running: `python manage.py runserver`
2. Postman installed
3. A registered user account

### Import Postman Collection
1. Open Postman
2. Click **Import** → Select file:
   ```
   docs/postman/BillPay_Expansion_APIs.postman_collection.json
   ```
3. Set `base_url` variable to `http://127.0.0.1:8000/api`

---

## API Testing Flow

### Step 1: Login (Get Token)
```
POST /api/auth-user/login/
{
    "identifier": "your_email@example.com",
    "password": "your_password"
}
```
Copy `access_token` from response and use as Bearer token for all subsequent requests.

---

### Step 2: Bank Account APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bills/bank-accounts/` | GET | List all your bank accounts |
| `/api/bills/bank-accounts/` | POST | Add a new bank account |
| `/api/bills/bank-accounts/{id}/` | GET | Get specific account details |
| `/api/bills/bank-accounts/{id}/` | PUT | Update nickname/primary status |
| `/api/bills/bank-accounts/{id}/` | DELETE | Soft delete account |
| `/api/bills/bank-accounts/{id}/verify/` | POST | Verify account (mock) |

**Add Bank Account:**
```json
POST /api/bills/bank-accounts/
{
    "account_holder_name": "Your Name",
    "account_number": "123456789012",
    "confirm_account_number": "123456789012",
    "ifsc_code": "SBIN0001234",
    "bank_name": "State Bank of India",
    "account_type": "SAVINGS",
    "nickname": "Salary Account"
}
```

---

### Step 3: Card APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bills/cards/` | GET | List all your cards |
| `/api/bills/cards/` | POST | Add a new card |
| `/api/bills/cards/{id}/` | GET | Get specific card details |
| `/api/bills/cards/{id}/` | PUT | Update nickname/primary status |
| `/api/bills/cards/{id}/` | DELETE | Soft delete card |

**Add Card:**
```json
POST /api/bills/cards/
{
    "card_number": "4111111111111111",
    "card_holder_name": "Your Name",
    "expiry_month": "12",
    "expiry_year": "2028",
    "card_type": "DEBIT",
    "card_network": "VISA",
    "nickname": "Primary Card"
}
```

---

### Step 4: MPIN APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bills/mpin/setup/` | GET | Check if MPIN is set |
| `/api/bills/mpin/setup/` | POST | Set up new MPIN |
| `/api/bills/mpin/verify/` | POST | Verify MPIN |
| `/api/bills/mpin/change/` | POST | Change existing MPIN |

**Setup MPIN:**
```json
POST /api/bills/mpin/setup/
{
    "mpin": "123456",
    "confirm_mpin": "123456",
    "password": "your_account_password"
}
```

**Verify MPIN:**
```json
POST /api/bills/mpin/verify/
{
    "mpin": "123456"
}
```

> ⚠️ **Note:** MPIN is locked for 30 minutes after 3 failed attempts.

---

### Step 5: Payment Gateways

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bills/gateways/` | GET | List payment gateways |
| `/api/bills/gateways/?type=UPI` | GET | Filter by type |

---

### Step 6: IFSC Verification

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bills/ifsc/{code}/` | GET | Verify IFSC code |

**Supported Banks (Mock):**
- SBI: `SBIN0XXXXXX`
- HDFC: `HDFC0XXXXXX`
- ICICI: `ICIC0XXXXXX`
- Axis: `UTIB0XXXXXX`
- Kotak: `KKBK0XXXXXX`

---

### Step 7: Transaction Logs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/bills/transactions/` | GET | List transactions |
| `/api/bills/transactions/{id}/` | GET | Transaction details |

**Filters:**
- `?type=BILL_PAYMENT` or `MONEY_TRANSFER`
- `?status=SUCCESS` or `FAILED`
- `?start_date=2025-01-01`
- `?page=1&page_size=20`

---

### Step 8: Money Transfer

**Prerequisites:**
1. ✅ Verified bank account
2. ✅ MPIN set up

```json
POST /api/bills/transfer/
{
    "source_bank_account_id": 1,
    "beneficiary_name": "Recipient Name",
    "beneficiary_account_number": "987654321012",
    "beneficiary_ifsc": "HDFC0001234",
    "amount": 5000.00,
    "remarks": "Payment",
    "mpin": "123456"
}
```

---

## Complete Test Sequence

1. **Login** → Get access token
2. **IFSC Check** → Verify `SBIN0001234`
3. **Add Bank Account** → Use verified IFSC
4. **List Bank Accounts** → Confirm added
5. **Verify Bank Account** → `/bank-accounts/1/verify/`
6. **Add Card** → Test card storage
7. **Check MPIN Status** → Should be false
8. **Setup MPIN** → Create `123456`
9. **Verify MPIN** → Confirm works
10. **List Gateways** → See available options
11. **Money Transfer** → Transfer funds
12. **List Transactions** → See transfer log

---

## Error Scenarios to Test

| Scenario | Expected |
|----------|----------|
| Add account with mismatched numbers | 400 Error |
| Add account with invalid IFSC | 400 Error |
| Setup MPIN with wrong password | 400 Error |
| Verify wrong MPIN 3 times | 429 (Locked) |
| Transfer without verified account | 400 Error |
| Transfer with wrong MPIN | 401 Error |
| IFSC with invalid format | 400 Error |

---

## Running Unit Tests

```bash
# Run all bill_pay tests
python manage.py test bill_pay -v 2

# Run specific test class
python manage.py test bill_pay.tests.BankAccountTests -v 2
python manage.py test bill_pay.tests.MPINTests -v 2
```
