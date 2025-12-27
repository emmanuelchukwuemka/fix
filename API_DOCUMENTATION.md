# MyFigPoint API Documentation

This document provides comprehensive documentation for the MyFigPoint API endpoints that can be consumed by your mobile application. All endpoints are accessible via `https://your-domain.com/api/` and require appropriate authentication unless otherwise specified.

## Base URL

```
https://72.62.4.119/api/
```

## Authentication

Most API endpoints require authentication using JWT (JSON Web Tokens). After successful login or registration, you'll receive an access token that must be included in the Authorization header of subsequent requests:

```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Rate Limiting

API requests are rate-limited to prevent abuse:
- 100 requests per hour for authenticated users
- 10 requests per hour for unauthenticated users

Exceeding these limits will result in a 429 (Too Many Requests) response.

## Error Responses

All error responses follow this format:

```json
{
  "message": "Error description",
  "error": "Detailed error information (optional)"
}
```

Common HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 409: Conflict
- 500: Internal Server Error

---

## Authentication Endpoints

### Register User

**POST** `/auth/register`

Register a new user account.

#### Request Body

```json
{
  "full_name": "string (required)",
  "email": "string (required, valid email format)",
  "password": "string (required, min 6 characters)",
  "referral_code": "string (optional)"
}
```

#### Response

```json
{
  "message": "User registered successfully",
  "access_token": "string",
  "user": {
    "id": "integer",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "phone": "string or null",
    "bank_name": "string or null",
    "account_name": "string or null",
    "account_number": "string or null",
    "referral_code": "string",
    "referred_by": "integer or null",
    "points_balance": "float",
    "total_points_earned": "float",
    "total_points_withdrawn": "float",
    "total_earnings": "float",
    "total_withdrawn": "float",
    "daily_code_requirement": "integer",
    "is_approved": "boolean",
    "is_suspended": "boolean",
    "is_verified": "boolean",
    "verification_pending": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 400: Missing required fields
- 400: Invalid email format
- 409: Email already registered

---

### Login User

**POST** `/auth/login`

Authenticate a user and receive an access token.

#### Request Body

```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

#### Response

```json
{
  "message": "Login successful",
  "access_token": "string",
  "user": {
    "id": "integer",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "phone": "string or null",
    "bank_name": "string or null",
    "account_name": "string or null",
    "account_number": "string or null",
    "referral_code": "string",
    "referred_by": "integer or null",
    "points_balance": "float",
    "total_points_earned": "float",
    "total_points_withdrawn": "float",
    "total_earnings": "float",
    "total_withdrawn": "float",
    "daily_code_requirement": "integer",
    "is_approved": "boolean",
    "is_suspended": "boolean",
    "is_verified": "boolean",
    "verification_pending": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 400: Missing email or password
- 401: Invalid credentials

---

### Forgot Password

**POST** `/auth/forgot-password`

Request a password reset link.

#### Request Body

```json
{
  "email": "string (required)"
}
```

#### Response

```json
{
  "message": "If your email is registered, you will receive a password reset link"
}
```

---

### Reset Password

**POST** `/auth/reset-password`

Reset user password using a reset token.

#### Request Body

```json
{
  "token": "string (required)",
  "password": "string (required, min 6 characters)"
}
```

#### Response

```json
{
  "message": "Password reset successfully"
}
```

#### Possible Errors

- 400: Missing token or password
- 400: Password too short
- 400: Invalid or expired reset token

---

## User Profile Endpoints

### Get User Profile

**GET** `/auth/profile`

Get the authenticated user's profile information.

#### Response

```json
{
  "user": {
    "id": "integer",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "phone": "string or null",
    "bank_name": "string or null",
    "account_name": "string or null",
    "account_number": "string or null",
    "referral_code": "string",
    "referred_by": "integer or null",
    "points_balance": "float",
    "total_points_earned": "float",
    "total_points_withdrawn": "float",
    "total_earnings": "float",
    "total_withdrawn": "float",
    "daily_code_requirement": "integer",
    "is_approved": "boolean",
    "is_suspended": "boolean",
    "is_verified": "boolean",
    "verification_pending": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

---

### Update User Profile

**PUT** `/users/profile`

Update the authenticated user's profile information.

#### Request Body

```json
{
  "full_name": "string (optional)",
  "phone": "string (optional)",
  "bank_name": "string (optional)",
  "account_name": "string (optional)",
  "account_number": "string (optional)"
}
```

#### Response

```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "integer",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "phone": "string or null",
    "bank_name": "string or null",
    "account_name": "string or null",
    "account_number": "string or null",
    "referral_code": "string",
    "referred_by": "integer or null",
    "points_balance": "float",
    "total_points_earned": "float",
    "total_points_withdrawn": "float",
    "total_earnings": "float",
    "total_withdrawn": "float",
    "daily_code_requirement": "integer",
    "is_approved": "boolean",
    "is_suspended": "boolean",
    "is_verified": "boolean",
    "verification_pending": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

---

### Change Password

**POST** `/users/change-password`

Change the authenticated user's password.

#### Request Body

```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 6 characters)"
}
```

#### Response

```json
{
  "message": "Password changed successfully"
}
```

#### Possible Errors

- 400: Missing current or new password
- 400: Current password is incorrect
- 400: New password too short

---

## Points Endpoints

### Get Points Balance

**GET** `/points/balance`

Get the authenticated user's points balance and related information.

#### Response

```json
{
  "points_balance": "float",
  "total_points_earned": "float",
  "total_points_withdrawn": "float",
  "tier_level": "string"
}
```

---

### Withdraw Points

**POST** `/points/withdraw`

Request to withdraw points.

#### Request Body

```json
{
  "points": "float (required, must be > 0)",
  "method": "string (optional, default: 'bank', values: 'bank', 'gift_card')",
  "bank_name": "string (optional, required if method is 'bank' and user doesn't have bank details)",
  "account_holder_name": "string (optional, required if method is 'bank' and user doesn't have bank details)",
  "account_number": "string (optional, required if method is 'bank' and user doesn't have bank details)",
  "gift_card_type": "string (optional, required if method is 'gift_card')"
}
```

#### Response

```json
{
  "message": "Withdrawal request for X points ($X.XX) submitted successfully. Payment will be processed within 24-48 hours.",
  "points_requested": "float",
  "usd_amount": "float",
  "method": "string",
  "tier": "string",
  "transaction_id": "integer",
  "new_balance": "float"
}
```

#### Possible Errors

- 400: Insufficient points balance
- 400: Points must be greater than 0
- 400: Invalid payment method
- 400: Missing required banking details

---

### Convert Points (Preview)

**POST** `/points/convert`

Preview the USD value of a certain number of points.

#### Request Body

```json
{
  "points": "float (required, must be > 0)"
}
```

#### Response

```json
{
  "message": "Preview: X points = $X.XX",
  "points": "float",
  "usd_amount": "float",
  "current_balance": "float"
}
```

#### Possible Errors

- 400: Points must be greater than 0
- 400: Insufficient points balance

---

## Reward Codes Endpoints

### Redeem Code

**POST** `/codes/redeem`

Redeem a reward code for points.

#### Request Body

```json
{
  "code": "string (required, format: 5 uppercase letters + 3 digits, e.g., ABCDE123)"
}
```

#### Response

```json
{
  "message": "Successfully redeemed code for X points",
  "points_added": "float",
  "new_balance": "float"
}
```

#### Possible Errors

- 400: Invalid code format
- 404: Invalid code
- 400: Code has already been used

---

### Validate Code

**GET** `/codes/validate/{code}`

Check if a code is valid and unused.

#### Response (Valid Code)

```json
{
  "valid": true,
  "code": "string",
  "point_value": "float",
  "created_at": "ISO 8601 date string"
}
```

#### Response (Invalid Code)

```json
{
  "valid": false,
  "message": "Invalid code or Code has already been used"
}
```

---

### Get Redemption History

**GET** `/codes/history?page={page}&per_page={per_page}`

Get the authenticated user's code redemption history.

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10, max: 50)

#### Response

```json
{
  "codes": [
    {
      "id": "integer",
      "code": "string",
      "point_value": "float",
      "is_used": true,
      "used_by": "integer",
      "used_at": "ISO 8601 date string",
      "created_at": "ISO 8601 date string",
      "batch_id": "string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

---

## Tasks Endpoints

### Get Available Tasks

**GET** `/tasks/?category={category}&page={page}&per_page={per_page}`

Get a list of available tasks.

#### Query Parameters

- `category`: string (optional, e.g., "Survey", "Video", "Daily")
- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10, max: 50)

#### Response

```json
{
  "tasks": [
    {
      "id": "integer",
      "title": "string",
      "description": "string",
      "reward_amount": "float",
      "points_reward": "float",
      "category": "string",
      "time_required": "integer",
      "is_active": "boolean",
      "requires_admin_verification": "boolean",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string",
      "user_status": "string (values: 'available', 'in_progress', 'completed', 'pending_review', 'rejected')"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

---

### Start Task

**POST** `/tasks/{task_id}/start`

Mark a task as in progress.

#### Response

```json
{
  "message": "Task started successfully",
  "task": {
    "id": "integer",
    "title": "string",
    "description": "string",
    "reward_amount": "float",
    "points_reward": "float",
    "category": "string",
    "time_required": "integer",
    "is_active": "boolean",
    "requires_admin_verification": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  },
  "user_task": {
    "id": "integer",
    "user_id": "integer",
    "task_id": "integer",
    "status": "string",
    "completed_at": "ISO 8601 date string or null",
    "created_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 404: Task not found or inactive
- 400: Task already started or completed

---

### Complete Task

**POST** `/tasks/{task_id}/complete`

Mark a task as completed.

#### Response (For tasks requiring admin verification)

```json
{
  "message": "Task submitted for admin review",
  "status": "pending_review",
  "task": {
    "id": "integer",
    "title": "string",
    "description": "string",
    "reward_amount": "float",
    "points_reward": "float",
    "category": "string",
    "time_required": "integer",
    "is_active": "boolean",
    "requires_admin_verification": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Response (For regular tasks)

```json
{
  "message": "Task completed successfully",
  "points_awarded": "float",
  "reward_awarded": "float",
  "new_points_balance": "float",
  "new_total_earnings": "float"
}
```

#### Possible Errors

- 404: Task not found or inactive
- 400: Task not started or already completed

---

### Upload Daily Codes

**POST** `/tasks/daily/upload-codes`

Upload multiple codes for daily tasks.

#### Request Body

```json
{
  "codes": [
    "string (format: 5 uppercase letters + 3 digits)"
  ]
}
```

#### Response

```json
{
  "message": "Successfully processed X codes",
  "valid_codes": "integer",
  "invalid_codes": [
    {
      "code": "string",
      "reason": "string"
    }
  ],
  "points_earned": "float",
  "extra_points": "float",
  "total_points": "float",
  "new_balance": "float"
}
```

#### Possible Errors

- 400: Codes array is required
- 400: Invalid code format
- 404: Code not found or already used

---

## Transactions Endpoints

### Get Transaction History

**GET** `/transactions/?page={page}&per_page={per_page}&type={type}`

Get the authenticated user's transaction history.

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10, max: 50)
- `type`: string (optional, values: "earning", "point_withdrawal", "deposit", "referral_bonus", "code_redemption")

#### Response

```json
{
  "transactions": [
    {
      "id": "integer",
      "user_id": "integer",
      "type": "string",
      "status": "string",
      "description": "string",
      "amount": "float",
      "points_amount": "float",
      "currency": "string",
      "reference_id": "string or null",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

---

### Get Specific Transaction

**GET** `/transactions/{transaction_id}`

Get details of a specific transaction.

#### Response

```json
{
  "transaction": {
    "id": "integer",
    "user_id": "integer",
    "type": "string",
    "status": "string",
    "description": "string",
    "amount": "float",
    "points_amount": "float",
    "currency": "string",
    "reference_id": "string or null",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 404: Transaction not found

---

### Get Transaction Summary

**GET** `/transactions/summary`

Get a summary of the user's transactions.

#### Response

```json
{
  "total_earnings": "float",
  "total_withdrawn": "float",
  "total_referral_bonus": "float",
  "total_code_redemption_points": "float"
}
```

---

## Referrals Endpoints

### Get Referral Stats

**GET** `/referrals/stats`

Get the authenticated user's referral statistics.

#### Response

```json
{
  "referral_code": "string",
  "referred_users_count": "integer",
  "total_referral_earnings": "float",
  "total_referral_points": "float"
}
```

---

### Get Referred Users

**GET** `/referrals/users?page={page}&per_page={per_page}`

Get a list of users referred by the authenticated user.

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10, max: 50)

#### Response

```json
{
  "users": [
    {
      "id": "integer",
      "full_name": "string",
      "email": "string",
      "role": "string",
      "phone": "string or null",
      "bank_name": "string or null",
      "account_name": "string or null",
      "account_number": "string or null",
      "referral_code": "string",
      "referred_by": "integer or null",
      "points_balance": "float",
      "total_points_earned": "float",
      "total_points_withdrawn": "float",
      "total_earnings": "float",
      "total_withdrawn": "float",
      "daily_code_requirement": "integer",
      "is_approved": "boolean",
      "is_suspended": "boolean",
      "is_verified": "boolean",
      "verification_pending": "boolean",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

---

### Get Referral Link

**GET** `/referrals/link`

Get the authenticated user's referral link.

#### Response

```json
{
  "referral_code": "string",
  "referral_link": "string"
}
```

---

## Notifications Endpoints

### Get Notifications

**GET** `/notifications/?page={page}&per_page={per_page}&unread_only={unread_only}`

Get the authenticated user's notifications.

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 20, max: 50)
- `unread_only`: boolean (optional, default: false)

#### Response

```json
{
  "notifications": [
    {
      "id": "integer",
      "user_id": "integer",
      "title": "string",
      "message": "string",
      "type": "string",
      "is_read": "boolean",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer",
  "unread_count": "integer"
}
```

---

### Mark Notification as Read

**PUT** `/notifications/{notification_id}/read`

Mark a specific notification as read.

#### Response

```json
{
  "message": "Notification marked as read",
  "notification": {
    "id": "integer",
    "user_id": "integer",
    "title": "string",
    "message": "string",
    "type": "string",
    "is_read": true,
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 404: Notification not found

---

### Mark All Notifications as Read

**PUT** `/notifications/mark-all-read`

Mark all notifications as read.

#### Response

```json
{
  "message": "Marked X notifications as read"
}
```

---

### Get Unread Notification Count

**GET** `/notifications/unread-count`

Get the count of unread notifications.

#### Response

```json
{
  "unread_count": "integer"
}
```

---

## Support Endpoints

### Create Support Message

**POST** `/support/`

Send a support message.

#### Request Body

```json
{
  "subject": "string (required, max 200 characters)",
  "message": "string (required)"
}
```

#### Response

```json
{
  "message": "Support message sent successfully",
  "support_message": {
    "id": "integer",
    "user_id": "integer",
    "subject": "string",
    "message": "string",
    "response": "string or null",
    "message_type": "string",
    "status": "string",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 400: Subject and message are required
- 400: Subject too long

---

### Get Support Messages

**GET** `/support/?page={page}&per_page={per_page}`

Get the authenticated user's support messages.

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10, max: 50)

#### Response

```json
{
  "messages": [
    {
      "id": "integer",
      "user_id": "integer",
      "subject": "string",
      "message": "string",
      "response": "string or null",
      "message_type": "string",
      "status": "string",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

---

### Get Specific Support Message

**GET** `/support/{message_id}`

Get a specific support message.

#### Response

```json
{
  "message": {
    "id": "integer",
    "user_id": "integer",
    "subject": "string",
    "message": "string",
    "response": "string or null",
    "message_type": "string",
    "status": "string",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 404: Support message not found

---

### Get WhatsApp Support Info

**GET** `/support/whatsapp`

Get WhatsApp support contact information.

#### Response

```json
{
  "whatsapp_number": "string",
  "message": "string"
}
```

---

## Partners Endpoints

### Get Partner Stats

**GET** `/partners/stats`

Get partner-specific statistics (requires partner role).

#### Response

```json
{
  "referred_users_count": "integer",
  "total_earnings": "float",
  "total_points_earned": "float",
  "partner_since": "ISO 8601 date string"
}
```

#### Possible Errors

- 403: Access denied. Partner access required.
- 403: Partner account pending approval.

---

### Get Partner Referrals

**GET** `/partners/referrals?page={page}&per_page={per_page}`

Get users referred by the authenticated partner.

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 10, max: 50)

#### Response

```json
{
  "referrals": [
    {
      "id": "integer",
      "full_name": "string",
      "email": "string",
      "role": "string",
      "phone": "string or null",
      "bank_name": "string or null",
      "account_name": "string or null",
      "account_number": "string or null",
      "referral_code": "string",
      "referred_by": "integer or null",
      "points_balance": "float",
      "total_points_earned": "float",
      "total_points_withdrawn": "float",
      "total_earnings": "float",
      "total_withdrawn": "float",
      "daily_code_requirement": "integer",
      "is_approved": "boolean",
      "is_suspended": "boolean",
      "is_verified": "boolean",
      "verification_pending": "boolean",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

#### Possible Errors

- 403: Access denied. Partner access required.
- 403: Partner account pending approval.

---

### Get Commission Rates

**GET** `/partners/commission-rates`

Get partner commission rates based on tier.

#### Response

```json
{
  "current_tier": "string",
  "referred_users_count": "integer",
  "commission_rate": "float",
  "payout_terms": "string",
  "next_tier_requirements": {
    "silver": "integer",
    "gold": "integer",
    "platinum": "integer"
  }
}
```

#### Possible Errors

- 403: Access denied. Partner access required.
- 403: Partner account pending approval.

---

## Admin Endpoints

These endpoints require admin authentication and are primarily used by the web admin panel, but documented here for completeness.

### Generate Reward Codes

**POST** `/admin/codes/generate`

Generate a batch of reward codes (admin only).

#### Request Body

```json
{
  "count": "integer (optional, default: 100, min: 1, max: 10000)",
  "point_value": "float (optional, default: 0.1, must be > 0)"
}
```

#### Response

```json
{
  "message": "Successfully generated X codes",
  "batch_id": "string",
  "codes": [
    "string"
  ],
  "total_generated": "integer"
}
```

#### Possible Errors

- 403: Access denied
- 400: Invalid count or point value

---

### Get All Users

**GET** `/admin/users?page={page}&per_page={per_page}&search={search}`

Get a list of all users (admin only).

#### Query Parameters

- `page`: integer (optional, default: 1)
- `per_page`: integer (optional, default: 20, max: 100)
- `search`: string (optional, search by name or email)

#### Response

```json
{
  "users": [
    {
      "id": "integer",
      "full_name": "string",
      "email": "string",
      "role": "string",
      "phone": "string or null",
      "bank_name": "string or null",
      "account_name": "string or null",
      "account_number": "string or null",
      "referral_code": "string",
      "referred_by": "integer or null",
      "points_balance": "float",
      "total_points_earned": "float",
      "total_points_withdrawn": "float",
      "total_earnings": "float",
      "total_withdrawn": "float",
      "daily_code_requirement": "integer",
      "is_approved": "boolean",
      "is_suspended": "boolean",
      "is_verified": "boolean",
      "verification_pending": "boolean",
      "created_at": "ISO 8601 date string",
      "updated_at": "ISO 8601 date string"
    }
  ],
  "total": "integer",
  "pages": "integer",
  "current_page": "integer"
}
```

#### Possible Errors

- 403: Access denied

---

### Update User Role

**PUT** `/users/admin/{user_id}/role`

Update a user's role (admin only).

#### Request Body

```json
{
  "role": "string (required, values: 'user', 'partner', 'admin')"
}
```

#### Response

```json
{
  "message": "User role updated successfully",
  "user": {
    "id": "integer",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "phone": "string or null",
    "bank_name": "string or null",
    "account_name": "string or null",
    "account_number": "string or null",
    "referral_code": "string",
    "referred_by": "integer or null",
    "points_balance": "float",
    "total_points_earned": "float",
    "total_points_withdrawn": "float",
    "total_earnings": "float",
    "total_withdrawn": "float",
    "daily_code_requirement": "integer",
    "is_approved": "boolean",
    "is_suspended": "boolean",
    "is_verified": "boolean",
    "verification_pending": "boolean",
    "created_at": "ISO 8601 date string",
    "updated_at": "ISO 8601 date string"
  }
}
```

#### Possible Errors

- 403: Access denied
- 404: User not found
- 400: Invalid role value

---

### Update User Points

**PUT** `/users/admin/{user_id}/points`

Update a user's points balance (admin only).

#### Request Body

```json
{
  "points": "float (required)",
  "operation": "string (optional, default: 'set', values: 'set', 'add', 'subtract')"
}
```

#### Response

```json
{
  "message": "User points {operation} successfully",
  "user_id": "integer",
  "new_balance": "float"
}
```

#### Possible Errors

- 403: Access denied
- 404: User not found
- 400: Invalid operation
- 400: Insufficient points balance (for subtract operation)

---

## Data Types and Enums

### User Roles

- `user`: Regular user
- `partner`: Partner user (requires admin approval)
- `admin`: Administrator

### Transaction Types

- `earning`: Points earned from completing tasks
- `point_withdrawal`: Points withdrawn by user
- `deposit`: Points deposited (not commonly used)
- `referral_bonus`: Bonus points for referrals
- `code_redemption`: Points from redeeming codes

### Transaction Statuses

- `pending`: Transaction is pending processing
- `completed`: Transaction completed successfully
- `failed`: Transaction failed

### Notification Types

- `info`: Informational notification
- `warning`: Warning notification
- `success`: Success notification
- `error`: Error notification

### Support Message Types

- `user_to_support`: Message from user to support
- `support_to_user`: Message from support to user

### Support Message Statuses

- `sent`: Message sent by user
- `read`: Message read by support
- `replied`: Support has replied to message
- `closed`: Message thread closed

### Task Statuses

- `available`: Task is available to start
- `in_progress`: User has started the task
- `completed`: User has completed the task
- `pending_review`: Task completion pending admin review
- `rejected`: Task completion rejected by admin

---

## Best Practices for Mobile App Integration

1. **Token Management**: Store the JWT token securely and handle expiration gracefully
2. **Error Handling**: Implement comprehensive error handling for all API calls
3. **Pagination**: Use pagination for endpoints that return lists to improve performance
4. **Caching**: Cache static data like task categories when appropriate
5. **Offline Support**: Implement offline support for critical features where possible
6. **Rate Limiting**: Respect rate limits and implement exponential backoff for retries
7. **Security**: Never log sensitive information like passwords or tokens
8. **User Experience**: Provide clear feedback for all user actions

## Version Information

API Version: v1
Last Updated: December 22, 2025