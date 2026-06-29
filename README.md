# BankApp

A training object-oriented Python project that models a modular banking system. The project is developed step by step: each day adds new domain behavior while keeping the account model extensible and testable.

## Current Scope

The codebase currently contains:

- an abstract account contract;
- a concrete base bank account;
- custom domain exceptions;
- account lifecycle statuses;
- supported currencies;
- advanced account types for savings, premium, and investment scenarios;
- a central `Bank` class for clients, accounts, and security policies;
- a transaction model, priority queue, and transaction processor;
- audit logging and transaction risk analysis;
- demonstration scenarios in `src/main.py`.

## Project Structure

```text
src/
  main.py      # Demonstration scenarios for implemented project days
  models.py    # Account models, enums, validation, and domain exceptions
```

## Day 1: Base Bank Account Model

Implemented in `src/models.py`:

- `AbstractAccount` as the abstract base class for all account types.
- `BankAccount` as the first concrete account implementation.
- Short UUID-based account number generation when `account_id` is not provided.
- Protected balance storage through `_balance` and read-only `balance` property.
- Account statuses: `active`, `frozen`, `closed`.
- Supported currencies: `RUB`, `USD`, `EUR`, `KZT`, `CNY`.
- Custom exceptions:
  - `AccountFrozenError`
  - `AccountClosedError`
  - `InvalidOperationError`
  - `InsufficientFundsError`
- Deposit and withdrawal validation:
  - only active accounts can process money operations;
  - amounts must be valid finite numbers;
  - negative and zero operation amounts are rejected;
  - withdrawals cannot exceed available funds for a base account.
- Human-readable `__str__()` output with account type, owner, last account digits, status, balance, and currency.
- Structured `get_account_info()` output for future logs, APIs, reports, or tests.

The Day 1 demo creates active and frozen accounts, performs valid operations, and shows expected business-rule errors.

## Day 2: Advanced Account Types

Added advanced account classes in `src/models.py`:

### SavingsAccount

A savings account that extends `BankAccount` with:

- `min_balance` to protect the required minimum account balance;
- `monthly_interest_rate` for savings growth;
- `apply_monthly_interest()` to credit monthly interest;
- overridden `withdraw()` that prevents breaking the minimum balance;
- extended `get_account_info()` and `__str__()` output.

### PremiumAccount

A premium account that extends `BankAccount` with:

- increased withdrawal limits through `withdrawal_limit`;
- overdraft support through `overdraft_limit`;
- fixed withdrawal commission through `fixed_commission`;
- overridden `withdraw()` that applies commission and can use overdraft;
- extended `get_account_info()` and `__str__()` output.

### InvestmentAccount

An investment account that extends `BankAccount` with:

- virtual investment portfolio support;
- allowed assets: `stocks`, `bonds`, `etf`;
- `portfolio_value` calculation;
- `project_yearly_growth()` for one-year portfolio projections;
- overridden `withdraw()` that allows withdrawing only free cash, not virtual assets;
- extended `get_account_info()` and `__str__()` output.

The Day 2 demo creates each advanced account type, runs valid operations, and shows expected errors for minimum balance, premium limits, overdraft limits, and investment cash restrictions.


## Day 3: Bank Management System

Added a central bank layer in `src/models.py`:

### Client

A client model with:

- full name, generated or custom client ID, and lifecycle status;
- contacts dictionary for phone, email, or other contact channels;
- linked account number list through `account_ids`;
- age validation that rejects clients under 18;
- failed login counter and suspicious action history;
- serializable `get_client_info()` output.

### Bank

A bank management class with:

- `add_client()` to register clients;
- `open_account()` to create base, savings, premium, or investment accounts for clients;
- `close_account()`, `freeze_account()`, and `unfreeze_account()` for account lifecycle management;
- `authenticate_client()` with three failed login attempts leading to client blocking;
- `search_accounts()` by owner, status, currency, or account type;
- `get_total_balance()` grouped by currency;
- `get_clients_ranking()` ordered by total client account value.

### Security Policies

The bank layer now supports:

- blocking clients after three failed authentication attempts;
- recording structured security events;
- marking clients as suspicious after suspicious account actions;
- blocking sensitive bank operations from 00:00 to 05:00.

The Day 3 demo creates several clients, opens different account types, authenticates clients, blocks a client after failed logins, freezes and unfreezes an account, searches accounts, calculates balances, ranks clients, and demonstrates the night restriction.

## Day 4: Transaction System

Added an extended transaction layer in `src/models.py`:

### Transaction

A transaction model with:

- generated or custom transaction ID;
- operation type: `deposit`, `withdraw`, `transfer`;
- amount, currency, and commission;
- sender and recipient account IDs;
- lifecycle status and failure reason;
- timestamps for creation, updates, scheduling, and processing;
- retry metadata for processor-level retry attempts.

### TransactionQueue

A queue module with:

- adding pending transactions;
- priority-based processing order;
- delayed operations through `scheduled_at`;
- transaction cancellation before processing;
- queue snapshots and pending counters.

### TransactionProcessor

A processing module with:

- fee calculation, including external transfer fees;
- currency conversion through configurable exchange rates;
- retry attempts for failed transactions;
- structured error logging;
- support for deposits, withdrawals, and transfers.

### Transaction Rules

The processor enforces:

- no transfers from negative balances except for premium accounts;
- no operations on frozen or closed accounts through existing account status checks;
- external transfer commission;
- failed transaction status and refusal reason recording.

The Day 4 demo creates 10 transactions, queues them, cancels one, leaves one delayed, processes ready transactions, and prints final statuses, errors, and balances.

## Day 5: Audit and Risk Analysis

Added audit and risk monitoring in `src/models.py`:

### AuditLog

An audit log with:

- importance levels: `info`, `warning`, `error`, `critical`;
- in-memory event storage;
- optional JSONL file persistence;
- filtering by level, minimum level, event type, transaction, client, account, and risk level;
- suspicious operation reporting;
- grouped error statistics.

### RiskAnalyzer

A risk analyzer that detects suspicious operations by:

- large transaction amount;
- frequent client operations in a configurable time window;
- transfers to new recipient accounts;
- operations during the night window.

Risk levels are `low`, `medium`, and `high`. High-risk transactions are blocked by `TransactionProcessor` before balances are changed.

### Audit Reports

The audit/risk layer provides:

- suspicious operation reports through `AuditLog.get_suspicious_operations()` and `RiskAnalyzer.get_suspicious_operations()`;
- client risk profiles through `RiskAnalyzer.get_client_risk_profile()`;
- error statistics through `AuditLog.get_error_statistics()`.

The Day 5 demo creates ordinary and suspicious transactions, blocks dangerous operations, writes audit events to a JSONL file, and prints suspicious operations, client risk profiles, error statistics, and final balances.
## How to Run

```bash
python src/main.py
```

## Validation Commands

```bash
python src/main.py
python -m compileall -q src
```
