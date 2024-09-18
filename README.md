# Investment Accounts API

## Overview
This is a Django REST Framework (DRF) based API for managing **Investment Accounts**. It allows multiple users to belong to various investment accounts with distinct permission levels, enabling role-based access for transactions. The project also includes an admin endpoint for retrieving a user’s transactions within a specified date range and calculating their total balance.

### Features
- Users can be assigned to multiple investment accounts with different levels of access:
  - **Investment Account 1**: View-only access (cannot create or modify transactions).
  - **Investment Account 2**: Full CRUD (Create, Read, Update, Delete) access.
  - **Investment Account 3**: Post-only access (can create transactions but cannot view them).
- Admin endpoint that returns all transactions for a user, filtered by date range and includes a sum of the user’s total balance.
- JWT authentication for secure access.
- Unit tests to validate API functionality.
- Automated testing with GitHub Actions.

## Setup and Installation

### Prerequisites
- Docker
- Docker Compose
- Python 3.12
- Django 5.1
- Django Rest Framework
- JWT Authentication (Simple JWT)

### Clone the Repository
```bash
git clone https://github.com/felixojiambo/investements_accounts
cd investment-accounts
```

### Environment Variables
Set the following environment variable:
- `DJANGO_SETTINGS_MODULE=investment_accounts.settings`

You can set this up in the `Dockerfile` (as it is done already) or by creating a `.env` file.

### Docker Setup
1. Build and start the application using Docker:
    ```bash
    docker-compose up --build
    ```

2. To run the app:
    ```bash
    docker-compose up
    ```

This command will:
- Start the Django app on `http://localhost:8000`.
- Set up a SQLite database in a Docker container (`db` service).

### Local Development Setup (Optional)

1. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Make  migrations:
    ```bash
    python manage.py makemigrations
4. Run migrations:
    ```bash
    python manage.py migrate
    ```

5. Run the development server:
    ```bash
    python manage.py runserver
    ```

## API Endpoints Documentation

### 1. User Registration
**Permissions**: Open to all users. No authentication required.

New users can register by providing their email, username, and password via the `/auth/register/` endpoint.

**Example Request to Register a New User**:
```
POST /auth/register/

{
  "email": "user@example.com",
  "username": "newuser",
  "password": "securepassword123"
}
```

**Example Response**:
```
{
  "id": 1,
  "username": "newuser",
  "email": "user@example.com"
}
```

---

### 2. Obtain JWT Token
**Permissions**: No authentication required.

To access protected resources, users must obtain a JWT token by providing their username and password via the `/auth/token/` endpoint.

**Example Request to Obtain Token**:
```
POST /auth/token/

{
  "username": "newuser",
  "password": "securepassword123"
}
```

**Example Response**:
```
{
  "refresh": "your_refresh_token",
  "access": "your_access_token"
}
```

---

### 3. Refresh JWT Token
**Permissions**: JWT token required (refresh token).

To refresh the access token when it expires, users can send the refresh token to the `/auth/token/refresh/` endpoint.

**Example Request to Refresh Token**:
```
POST /auth/token/refresh/

{
  "refresh": "your_refresh_token"
}
```

**Example Response**:
```
{
  "access": "new_access_token"
}
```
### 4. **Creating Investment Accounts (Account Types)**

**Permissions**: Admin or authorized users with permission to create investment accounts.

Investment accounts are created with specific permission levels (`view_only`, `full_access`, `post_only`). These accounts are created via the `/investment-accounts/` endpoint.

#### Example Request to Create Investment Accounts:
```bash
POST /investment-accounts/

{
  "name": "Savings Account",
  "description": "This account allows view-only access.",
  "permission_level": "view_only"
}
```

#### Available Permission Levels:
- **view_only**: Users can only view transactions.
- **full_access**: Users can perform full CRUD operations.
- **post_only**: Users can only create (post) transactions but cannot view or modify existing ones.

#### Example Response:
```json
{
  "id": 1,
  "name": "Savings Account",
  "description": "This account allows view-only access.",
  "permission_level": "view_only",
  "created_at": "2024-09-20T10:00:00Z"
}
```

---

### 5. **Assigning Users to Investment Accounts (Creating User Accounts)**

**Permissions**: Requires JWT authentication for the authenticated user.

Once the investment accounts (account types) are created, users are assigned to these accounts by creating **UserAccount** instances via the `/user-accounts/create/` endpoint.

#### Example Request to Create User Accounts:
```bash
POST /user-accounts/create/

{
  "user": 1,  # User ID
  "account_type": 1  # Investment Account Type ID
}
```

This request assigns a user to an investment account (based on the `InvestmentAccount` type). The user now has an individual **UserAccount** with its own balance and account number.

#### Example Response:
```json
{
  "id": 1,
  "user": 1,
  "balance": "1000.00",
  "account_type": {
    "id": 1,
    "name": "Savings Account",
    "permission_level": "view_only"
  },
  "account_number": "123456789",
  "created_at": "2024-09-20T10:00:00Z"
}
```

---

### 6. **Listing User Accounts**

**Permissions**: Requires JWT authentication for the authenticated user.

Users can list all their assigned accounts via the `/user-accounts/` endpoint. This will return all **UserAccount** instances associated with the authenticated user.

#### Example Request to List User Accounts:
```bash
GET /user-accounts/
```

#### Example Response:
```json
[
  {
    "id": 1,
    "user": 1,
    "balance": "1000.00",
    "account_type": {
      "id": 1,
      "name": "Savings Account",
      "permission_level": "view_only"
    }
  },
  {
    "id": 2,
    "user": 1,
    "balance": "500.00",
    "account_type": {
      "id": 2,
      "name": "Investment Account",
      "permission_level": "full_access"
    }
  }
]
```

---

### 7. **Creating Transactions**

**Permissions**:
- **view_only** accounts: Users **cannot** create transactions.
- **full_access** accounts: Users **can** create transactions (debit or credit).
- **post_only** accounts: Users **can only post** (create) transactions, but cannot view existing ones.

Transactions (debits or credits) can be created for user accounts via the `/transactions/create/` endpoint. This allows users to post new financial transactions (such as adding or withdrawing funds) to their accounts.

#### Example Request to Create Transactions:
```bash
POST /transactions/create/

{
  "account_id": 1,  # User Account ID
  "amount": 100.00,
  "transaction_type": "credit"
}
```

#### Available Transaction Types:
- **credit**: Add funds to the user’s account.
- **debit**: Withdraw funds from the user’s account.

#### Example Response:
```json
{
  "id": 1,
  "user_account": 1,
  "amount": "100.00",
  "transaction_type": "credit",
  "created_at": "2024-09-20T10:00:00Z"
}
```

---

### 8. **Listing Transactions**

**Permissions**:
- **view_only** accounts: Users can view transactions.
- **full_access** accounts: Users can view transactions.
- **post_only** accounts: Users **cannot** view transactions.

Users can view a list of all transactions for a specific account by sending a request to the `/transactions/list/` endpoint, specifying the account for which they want to view the transactions.

#### Example Request to List Transactions:
```bash
GET /transactions/list/?account_id=1
```

#### Example Response:
```json
[
  {
    "id": 1,
    "user_account": 1,
    "amount": "100.00",
    "transaction_type": "credit",
    "created_at": "2024-09-20T10:00:00Z"
  },
  {
    "id": 2,
    "user_account": 1,
    "amount": "50.00",
    "transaction_type": "debit",
    "created_at": "2024-09-21T10:00:00Z"
  }
]
```

---

### 9. **Retrieving Transaction Details**

**Permissions**:
- **view_only** accounts: Users can view transaction details.
- **full_access** accounts: Users can view transaction details.
- **post_only** accounts: Users **cannot** view transaction details.

To retrieve the details of a specific transaction, users can send a request to the `/transactions/<transaction_id>/` endpoint. This will return detailed information about the selected transaction.

#### Example Request to Retrieve Transaction Details:
```bash
GET /transactions/1/
```

#### Example Response:
```json
{
  "id": 1,
  "user_account": 1,
  "amount": "100.00",
  "transaction_type": "credit",
  "created_at": "2024-09-20T10:00:00Z"
}
```

---

### 10. **Admin: Viewing User Transactions**

**Permissions**: Requires **Admin** privileges.

Admins can view all transactions for a specific user across all their accounts, with filtering by date range, using the `/transactions/admin/user-transactions/` endpoint.

#### Example Request to View User Transactions (Admin Only):
```bash
GET /transactions/admin/user-transactions/?user_id=1&start_date=2024-09-01&end_date=2024-09-30
```

#### Example Response:
```json
{
  "transactions": [
    {
      "id": 1,
      "user_account": 1,
      "amount": "100.00",
      "transaction_type": "credit",
      "created_at": "2024-09-10T10:00:00Z"
    },
    {
      "id": 2,
      "user_account": 2,
      "amount": "50.00",
      "transaction_type": "debit",
      "created_at": "2024-09-15T10:00:00Z"
    }
  ],
  "total_balance": "150.00"
}
```

This response includes:
- A list of all transactions for the specified user within the date range.
- The total balance (sum) of the user’s transactions during the specified period.

---

### 11. **Updating Transactions (Full Access)**

**Permissions**:
- **view_only** accounts: Users **cannot** update transactions.
- **full_access** accounts: Users **can** update transactions.
- **post_only** accounts: Users **cannot** update transactions.

Users with full CRUD access (for **Investment Account 2**) can update existing transactions via the `/transactions/<transaction_id>/` endpoint using `PUT` or `PATCH` requests.

#### Example Request to Update Transactions:
```bash
PUT /transactions/1/

{
  "amount": 200.00,
  "transaction_type": "credit"
}
```

#### Example Response:
```json
{
  "id": 1,
  "user_account": 1,
  "amount": "200.00",
  "transaction_type": "credit",
  "created_at": "2024-09-20T10:00:00Z"
}
```

---

### 12. **Deleting Transactions (Full Access)**

**Permissions**:
- **view_only** accounts: Users **cannot** delete transactions.
- **full_access** accounts: Users **can** delete transactions.
- **post_only** accounts: Users **cannot** delete transactions.

Users with full CRUD access can delete transactions using the `/transactions/<transaction_id>/` endpoint.

#### Example Request to Delete Transactions:
```bash
DELETE /transactions/1/
```

#### Example Response:
```bash
HTTP 204 No Content
```

The response indicates the transaction has been successfully deleted.

## API Endpoints

### Authentication
- `POST /auth/token/`: Obtain a JWT token.
- `POST /auth/token/refresh/`: Refresh the JWT token.
- `POST /auth/register/`: Register a new user.

### User Accounts
- `GET /user-accounts/`: List all user accounts for the authenticated user.
- `POST /user-accounts/create/`: Create a new user account.
- `GET /user-accounts/<int:pk>/`: Retrieve a specific user account.

### Investment Accounts
- `POST /investment-accounts/`: Create a new investment account.

### Transactions
- `GET /transactions/list/`: List all transactions for a specific user account.
- `POST /transactions/create/`: Create a new transaction (debit or credit).
- `GET /transactions/<int:transaction_id>/`: Retrieve transaction details.

### Admin
- `GET /transactions/admin/user-transactions/`: Retrieve all transactions for a specific user, filtered by date range, along with the total balance.

## Permissions

### Custom Permissions

- **IsViewOnlyForInvestmentAccount1**: Restricts access to view-only for Investment Account 1.
- **IsFullAccessForInvestmentAccount2**: Allows full CRUD access for Investment Account 2.
- **IsPostOnlyForInvestmentAccount3**: Allows only posting (creating) transactions for Investment Account 3.

### Middleware and Authentication
- JWT Authentication is used to secure the API endpoints. Ensure that you provide a valid token when accessing secured endpoints.

## Running Unit Tests

To run the tests:
```bash
python manage.py test
```

Alternatively, to run the tests via Docker:
```bash
docker-compose run web python manage.py test
```

## Continuous Integration (CI)

A GitHub Action is configured to run the tests automatically when code is pushed to the repository. You can find the configuration in `.github/workflows/ci.yml`.
