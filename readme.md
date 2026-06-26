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

## How to Run

```bash
python src/main.py
```

## Validation Commands

```bash
python src/main.py
python -m compileall -q src
```
