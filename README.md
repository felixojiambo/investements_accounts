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
