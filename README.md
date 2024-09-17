Investment Account Management API

#### Project Overview
This project is a Django Rest Framework (DRF) API designed to manage investment accounts. It allows multiple users to belong to an investment account and supports various permission levels for different accounts.

#### Features
- **Investment Accounts**: Users can have multiple investment accounts with different permission levels:
  - **View Only**: Users can only view account details.
  - **Full Access**: Users have full CRUD (Create, Read, Update, Delete) permissions.
  - **Post Only**: Users can post transactions but cannot view them.
- **User Accounts**: Each user can have multiple accounts, each with a unique account number and balance.
- **Transactions**: Supports debit and credit transactions with validation to prevent negative balances.
- **Admin Endpoint**: Allows admin users to retrieve all transactions for a specific user within a date range and calculate the total balance.

#### Models
- **InvestmentAccount**: Represents an investment account with a name, description, and permission level.
- **UserAccount**: Represents a user's instance of an investment account, including balance and account number.
- **Transaction**: Represents a financial transaction (debit or credit) on a user's investment account.

#### Permissions
- **BaseAccountPermission**: Base class for account-based permissions.
- **IsViewOnlyForInvestmentAccount1**: Enforces view-only access for Investment Account 1.
- **IsFullAccessForInvestmentAccount2**: Allows full CRUD access for Investment Account 2.
- **IsPostOnlyForInvestmentAccount3**: Allows post-only access for Investment Account 3.
- **DynamicAccountPermission**: Dynamically checks the user's account permission level and grants appropriate access.

#### API Endpoints
- **InvestmentAccountCreateView**: Create a new investment account.
- **UserAccountCreateView**: Create a new user account.
- **UserCreateView**: Register a new user.
- **UserAccountListView**: List all user accounts for the authenticated user.
- **UserAccountDetailView**: Retrieve, update, or delete a specific user account.
- **TransactionListView**: List transactions for a specified account.
- **CreateTransactionView**: Create a new transaction.
- **TransactionDetailView**: Retrieve, update, or delete a specific transaction.
- **AdminUserTransactionsView**: Retrieve all transactions for a specific user within a date range and calculate the total balance.

#### Unit Tests
- Unit tests are included to validate the functionality of the APIs.

#### GitHub Actions
- A GitHub Action is set up to automatically run the unit tests.

#### Setup Instructions
1. **Clone the repository**:
   ```bash
   git clone https://github.com/felixojiambo/investements_accounts
   cd investements_accounts
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```
4. **Run the development server**:
   ```bash
   python manage.py runserver
   ```
   ```
5. **Run the tests**:
   ```bash
   python manage.py test
   ```
#### Contact
For any further clarification, please contact the project maintainer.
