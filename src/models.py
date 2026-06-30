import json
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from uuid import uuid4


class AccountFrozenError(Exception):
    """Raised when an operation is attempted on a frozen account."""


class AccountClosedError(Exception):
    """Raised when an operation is attempted on a closed account."""


class InvalidOperationError(Exception):
    """Raised when an operation violates account business rules."""


class InsufficientFundsError(Exception):
    """Raised when an account has insufficient funds for withdrawal."""


class AuthenticationError(Exception):
    """Raised when client authentication fails."""


class ClientBlockedError(Exception):
    """Raised when a blocked client attempts a restricted operation."""


class SecurityRestrictionError(Exception):
    """Raised when a security policy blocks an operation."""


class AccountStatus(str, Enum):
    """
    Account lifecycle status.

    String-based enum is used to keep values easy to serialize
    into JSON, logs, reports, or ML/analytics datasets.
    """

    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class ClientStatus(str, Enum):
    """Client lifecycle and security status."""

    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPICIOUS = "suspicious"




class TransactionType(str, Enum):
    """Supported transaction operation types."""

    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction lifecycle status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"



class AuditLevel(str, Enum):
    """Audit event importance level."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Risk severity level for banking operations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Currency(str, Enum):
    """
    Supported account currencies.

    String-based enum keeps the domain model compatible with
    downstream reporting, APIs, and tabular analytics.
    """

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class AbstractAccount(ABC):
    """
    Abstract base class for all account types.

    This class defines the common contract for future account models:
    debit accounts, credit accounts, saving accounts, investment accounts, etc.

    The balance is intentionally protected, not public.
    External code should change it only through domain methods:
    deposit() and withdraw().
    """

    def __init__(
        self,
        owner: str,
        balance: Decimal | int | float | str = Decimal("0"),
        account_id: str | None = None,
        status: AccountStatus | str = AccountStatus.ACTIVE,
    ) -> None:
        self.account_id = account_id or self._generate_account_id()
        self.owner = self._validate_owner(owner)
        self._balance = self._validate_amount(balance)
        self.status = self._validate_status(status)

    @staticmethod
    def _generate_account_id() -> str:
        """
        Generate a short UUID-based account identifier.

        Full UUID is not necessary for a training project,
        but the generated value is still stable enough for demos and tests.
        """
        return uuid4().hex[:12]

    @staticmethod
    def _validate_owner(owner: str) -> str:
        """Validate and normalize account owner name."""
        if not isinstance(owner, str):
            raise InvalidOperationError("Owner must be a string.")

        normalized_owner = owner.strip()

        if not normalized_owner:
            raise InvalidOperationError("Owner cannot be empty.")

        return normalized_owner

    @staticmethod
    def _validate_amount(amount: Decimal | int | float | str) -> Decimal:
        """
        Validate and convert money amount to Decimal.

        Decimal is used instead of float because financial operations
        must avoid binary floating point precision errors.
        """
        try:
            normalized_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise InvalidOperationError("Amount must be a valid number.")

        if not normalized_amount.is_finite():
            raise InvalidOperationError("Amount must be a finite number.")

        if normalized_amount < 0:
            raise InvalidOperationError("Amount cannot be negative.")

        return normalized_amount

    @staticmethod
    def _validate_status(status: AccountStatus | str) -> AccountStatus:
        """Validate account status and convert it to AccountStatus enum."""
        try:
            return AccountStatus(status)
        except ValueError:
            valid_statuses = ", ".join(status.value for status in AccountStatus)
            raise InvalidOperationError(
                f"Invalid account status: {status}. "
                f"Available statuses: {valid_statuses}."
            )

    def _ensure_account_is_available(self) -> None:
        """
        Ensure that the account can process money operations.

        This method centralizes lifecycle checks, so deposit() and withdraw()
        do not duplicate the same status validation logic.
        """
        if self.status == AccountStatus.FROZEN:
            raise AccountFrozenError("Operation denied: account is frozen.")

        if self.status == AccountStatus.CLOSED:
            raise AccountClosedError("Operation denied: account is closed.")

    @abstractmethod
    def deposit(self, amount: Decimal | int | float | str) -> None:
        """Increase account balance by the given amount."""

    @abstractmethod
    def withdraw(self, amount: Decimal | int | float | str) -> None:
        """Decrease account balance by the given amount."""

    @abstractmethod
    def get_account_info(self) -> dict:
        """Return account information as a dictionary."""


class BankAccount(AbstractAccount):
    """
    Basic bank account implementation.

    This class is intentionally small but extensible.
    Later project days can add transactions, audit events, reports,
    user behavior features, fraud signals, or ML-ready event logs.
    """

    def __init__(
        self,
        owner: str,
        balance: Decimal | int | float | str = Decimal("0"),
        account_id: str | None = None,
        status: AccountStatus | str = AccountStatus.ACTIVE,
        currency: Currency | str = Currency.RUB,
    ) -> None:
        super().__init__(
            owner=owner,
            balance=balance,
            account_id=account_id,
            status=status,
        )
        self.currency = self._validate_currency(currency)

    @staticmethod
    def _validate_currency(currency: Currency | str) -> Currency:
        """Validate currency and convert it to Currency enum."""
        try:
            return Currency(currency)
        except ValueError:
            valid_currencies = ", ".join(currency.value for currency in Currency)
            raise InvalidOperationError(
                f"Invalid currency: {currency}. "
                f"Available currencies: {valid_currencies}."
            )

    @property
    def balance(self) -> Decimal:
        """
        Read-only balance property.

        External code can read the balance, but cannot assign it directly.
        This keeps balance changes controlled by domain methods.
        """
        return self._balance

    def deposit(self, amount: Decimal | int | float | str) -> None:
        """Deposit money into the account."""
        self._ensure_account_is_available()

        normalized_amount = self._validate_amount(amount)

        if normalized_amount == 0:
            raise InvalidOperationError("Deposit amount must be greater than zero.")

        self._balance += normalized_amount

    def withdraw(self, amount: Decimal | int | float | str) -> None:
        """Withdraw money from the account."""
        self._ensure_account_is_available()

        normalized_amount = self._validate_amount(amount)

        if normalized_amount == 0:
            raise InvalidOperationError("Withdraw amount must be greater than zero.")

        if normalized_amount > self._balance:
            raise InsufficientFundsError("Not enough funds on the account.")

        self._balance -= normalized_amount

    def to_dict(self) -> dict:
        """
        Return account state as a serializable dictionary.

        This format is convenient for:
        - structured logging
        - test assertions
        - JSON APIs
        - future pandas DataFrame reports
        - ML feature/event pipelines
        """
        return {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": str(self._balance),
            "status": self.status.value,
            "currency": self.currency.value,
            "account_type": self.__class__.__name__,
        }

    def get_account_info(self) -> dict:
        """
        Return account information.

        Kept as a required public method from the task specification.
        Internally delegates to to_dict() to avoid duplicate serialization logic.
        """
        return self.to_dict()

    def __str__(self) -> str:
        """Return human-readable account representation."""
        last_digits = self.account_id[-4:]

        return (
            f"{self.__class__.__name__} | "
            f"Owner: {self.owner} | "
            f"Account: ****{last_digits} | "
            f"Status: {self.status.value} | "
            f"Balance: {self._balance} {self.currency.value}"
        )


class SavingsAccount(BankAccount):
    """Savings account with minimum balance and monthly interest."""

    def __init__(
        self,
        owner: str,
        balance: Decimal | int | float | str = Decimal("0"),
        account_id: str | None = None,
        status: AccountStatus | str = AccountStatus.ACTIVE,
        currency: Currency | str = Currency.RUB,
        min_balance: Decimal | int | float | str = Decimal("0"),
        monthly_interest_rate: Decimal | int | float | str = Decimal("0.01"),
    ) -> None:
        super().__init__(
            owner=owner,
            balance=balance,
            account_id=account_id,
            status=status,
            currency=currency,
        )
        self.min_balance = self._validate_amount(min_balance)
        self.monthly_interest_rate = self._validate_amount(monthly_interest_rate)

        if self._balance < self.min_balance:
            raise InvalidOperationError("Balance cannot be lower than minimum balance.")

    def apply_monthly_interest(self) -> Decimal:
        """Apply monthly interest and return the credited amount."""
        self._ensure_account_is_available()

        interest_amount = self._balance * self.monthly_interest_rate

        if interest_amount == 0:
            return Decimal("0")

        self._balance += interest_amount
        return interest_amount

    def withdraw(self, amount: Decimal | int | float | str) -> None:
        """Withdraw money while preserving the minimum balance."""
        self._ensure_account_is_available()

        normalized_amount = self._validate_amount(amount)

        if normalized_amount == 0:
            raise InvalidOperationError("Withdraw amount must be greater than zero.")

        if self._balance - normalized_amount < self.min_balance:
            raise InsufficientFundsError("Withdrawal would break minimum balance.")

        self._balance -= normalized_amount

    def get_account_info(self) -> dict:
        """Return savings account information."""
        account_info = super().get_account_info()
        account_info.update(
            {
                "min_balance": str(self.min_balance),
                "monthly_interest_rate": str(self.monthly_interest_rate),
            }
        )
        return account_info

    def __str__(self) -> str:
        """Return human-readable savings account representation."""
        return (
            f"{super().__str__()} | "
            f"Min balance: {self.min_balance} {self.currency.value} | "
            f"Monthly interest: {self.monthly_interest_rate}"
        )


class PremiumAccount(BankAccount):
    """Premium account with overdraft, higher withdrawal limit, and commission."""

    def __init__(
        self,
        owner: str,
        balance: Decimal | int | float | str = Decimal("0"),
        account_id: str | None = None,
        status: AccountStatus | str = AccountStatus.ACTIVE,
        currency: Currency | str = Currency.RUB,
        overdraft_limit: Decimal | int | float | str = Decimal("10000"),
        withdrawal_limit: Decimal | int | float | str = Decimal("100000"),
        fixed_commission: Decimal | int | float | str = Decimal("50"),
    ) -> None:
        super().__init__(
            owner=owner,
            balance=balance,
            account_id=account_id,
            status=status,
            currency=currency,
        )
        self.overdraft_limit = self._validate_amount(overdraft_limit)
        self.withdrawal_limit = self._validate_amount(withdrawal_limit)
        self.fixed_commission = self._validate_amount(fixed_commission)

    def withdraw(self, amount: Decimal | int | float | str) -> None:
        """Withdraw money using premium limits and overdraft when needed."""
        self._ensure_account_is_available()

        normalized_amount = self._validate_amount(amount)

        if normalized_amount == 0:
            raise InvalidOperationError("Withdraw amount must be greater than zero.")

        if normalized_amount > self.withdrawal_limit:
            raise InvalidOperationError("Withdraw amount exceeds premium limit.")

        total_charge = normalized_amount + self.fixed_commission

        if total_charge > self._balance + self.overdraft_limit:
            raise InsufficientFundsError("Not enough funds including overdraft limit.")

        self._balance -= total_charge

    def get_account_info(self) -> dict:
        """Return premium account information."""
        account_info = super().get_account_info()
        account_info.update(
            {
                "overdraft_limit": str(self.overdraft_limit),
                "withdrawal_limit": str(self.withdrawal_limit),
                "fixed_commission": str(self.fixed_commission),
            }
        )
        return account_info

    def __str__(self) -> str:
        """Return human-readable premium account representation."""
        return (
            f"{super().__str__()} | "
            f"Overdraft: {self.overdraft_limit} {self.currency.value} | "
            f"Withdraw limit: {self.withdrawal_limit} {self.currency.value} | "
            f"Commission: {self.fixed_commission} {self.currency.value}"
        )


class InvestmentAccount(BankAccount):
    """Investment account with virtual assets and yearly growth projection."""

    ALLOWED_ASSETS = ("stocks", "bonds", "etf")
    DEFAULT_YEARLY_GROWTH_RATES = {
        "stocks": Decimal("0.08"),
        "bonds": Decimal("0.04"),
        "etf": Decimal("0.06"),
    }

    def __init__(
        self,
        owner: str,
        balance: Decimal | int | float | str = Decimal("0"),
        account_id: str | None = None,
        status: AccountStatus | str = AccountStatus.ACTIVE,
        currency: Currency | str = Currency.RUB,
        portfolio: dict[str, Decimal | int | float | str] | None = None,
    ) -> None:
        super().__init__(
            owner=owner,
            balance=balance,
            account_id=account_id,
            status=status,
            currency=currency,
        )
        self.portfolio = self._validate_portfolio(portfolio or {})

    def _validate_portfolio(
        self,
        portfolio: dict[str, Decimal | int | float | str],
    ) -> dict[str, Decimal]:
        """Validate investment portfolio asset values."""
        invalid_assets = set(portfolio) - set(self.ALLOWED_ASSETS)

        if invalid_assets:
            valid_assets = ", ".join(self.ALLOWED_ASSETS)
            raise InvalidOperationError(
                f"Invalid portfolio assets: {', '.join(invalid_assets)}. "
                f"Available assets: {valid_assets}."
            )

        return {
            asset: self._validate_amount(portfolio.get(asset, Decimal("0")))
            for asset in self.ALLOWED_ASSETS
        }

    @property
    def portfolio_value(self) -> Decimal:
        """Return total current value of virtual assets."""
        return sum(self.portfolio.values(), Decimal("0"))

    def withdraw(self, amount: Decimal | int | float | str) -> None:
        """Withdraw only free cash, leaving virtual assets untouched."""
        self._ensure_account_is_available()

        normalized_amount = self._validate_amount(amount)

        if normalized_amount == 0:
            raise InvalidOperationError("Withdraw amount must be greater than zero.")

        if normalized_amount > self._balance:
            raise InsufficientFundsError("Investment assets cannot be withdrawn as cash.")

        self._balance -= normalized_amount

    def project_yearly_growth(
        self,
        yearly_growth_rates: dict[str, Decimal | int | float | str] | None = None,
    ) -> dict:
        """Project portfolio value after one year using asset growth rates."""
        rates = yearly_growth_rates or self.DEFAULT_YEARLY_GROWTH_RATES
        normalized_rates = {
            asset: self._validate_amount(rates.get(asset, Decimal("0")))
            for asset in self.ALLOWED_ASSETS
        }
        projected_assets = {
            asset: value * (Decimal("1") + normalized_rates[asset])
            for asset, value in self.portfolio.items()
        }
        projected_portfolio_value = sum(projected_assets.values(), Decimal("0"))

        return {
            "current_portfolio_value": str(self.portfolio_value),
            "projected_portfolio_value": str(projected_portfolio_value),
            "projected_total_value": str(self._balance + projected_portfolio_value),
            "projected_assets": {
                asset: str(value)
                for asset, value in projected_assets.items()
            },
        }

    def get_account_info(self) -> dict:
        """Return investment account information."""
        account_info = super().get_account_info()
        account_info.update(
            {
                "portfolio": {
                    asset: str(value)
                    for asset, value in self.portfolio.items()
                },
                "portfolio_value": str(self.portfolio_value),
                "total_value": str(self._balance + self.portfolio_value),
            }
        )
        return account_info

    def __str__(self) -> str:
        """Return human-readable investment account representation."""
        return (
            f"{super().__str__()} | "
            f"Portfolio value: {self.portfolio_value} {self.currency.value} | "
            f"Total value: {self._balance + self.portfolio_value} {self.currency.value}"
        )



class Transaction:
    """Money operation request with processing metadata."""

    def __init__(
        self,
        transaction_type: TransactionType | str,
        amount: Decimal | int | float | str,
        currency: Currency | str,
        sender_account_id: str | None = None,
        recipient_account_id: str | None = None,
        commission: Decimal | int | float | str = Decimal("0"),
        transaction_id: str | None = None,
        status: TransactionStatus | str = TransactionStatus.PENDING,
        failure_reason: str | None = None,
        priority: int = 0,
        scheduled_at: datetime | None = None,
        is_external: bool = False,
        max_retries: int = 0,
    ) -> None:
        self.transaction_id = transaction_id or uuid4().hex[:14]
        self.transaction_type = self._validate_transaction_type(transaction_type)
        self.amount = AbstractAccount._validate_amount(amount)
        self.currency = BankAccount._validate_currency(currency)
        self.commission = AbstractAccount._validate_amount(commission)
        self.sender_account_id = sender_account_id
        self.recipient_account_id = recipient_account_id
        self.status = self._validate_status(status)
        self.failure_reason = failure_reason
        self.priority = self._validate_priority(priority)
        self.scheduled_at = self._validate_scheduled_at(scheduled_at or datetime.now())
        self.is_external = bool(is_external)
        self.max_retries = self._validate_retry_count(max_retries)
        self.retry_count = 0
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.processed_at: datetime | None = None

        if self.amount == 0:
            raise InvalidOperationError("Transaction amount must be greater than zero.")

    @staticmethod
    def _validate_transaction_type(transaction_type: TransactionType | str) -> TransactionType:
        """Validate transaction type."""
        try:
            return TransactionType(transaction_type)
        except ValueError:
            valid_types = ", ".join(item.value for item in TransactionType)
            raise InvalidOperationError(
                f"Invalid transaction type: {transaction_type}. Available types: {valid_types}."
            )

    @staticmethod
    def _validate_status(status: TransactionStatus | str) -> TransactionStatus:
        """Validate transaction status."""
        try:
            return TransactionStatus(status)
        except ValueError:
            valid_statuses = ", ".join(item.value for item in TransactionStatus)
            raise InvalidOperationError(
                f"Invalid transaction status: {status}. Available statuses: {valid_statuses}."
            )

    @staticmethod
    def _validate_priority(priority: int) -> int:
        """Validate queue priority."""
        if not isinstance(priority, int):
            raise InvalidOperationError("Transaction priority must be an integer.")

        return priority

    @staticmethod
    def _validate_retry_count(max_retries: int) -> int:
        """Validate retry attempts count."""
        if not isinstance(max_retries, int):
            raise InvalidOperationError("Max retries must be an integer.")

        if max_retries < 0:
            raise InvalidOperationError("Max retries cannot be negative.")

        return max_retries

    @staticmethod
    def _validate_scheduled_at(scheduled_at: datetime) -> datetime:
        """Validate scheduled processing timestamp."""
        if not isinstance(scheduled_at, datetime):
            raise InvalidOperationError("Transaction scheduled_at must be a datetime.")

        return scheduled_at

    def mark_processing(self) -> None:
        """Mark transaction as currently being processed."""
        self.status = TransactionStatus.PROCESSING
        self.updated_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark transaction as completed."""
        self.status = TransactionStatus.COMPLETED
        self.failure_reason = None
        self.processed_at = datetime.now()
        self.updated_at = self.processed_at

    def mark_failed(self, reason: str) -> None:
        """Mark transaction as failed and record the reason."""
        self.status = TransactionStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.now()

    def mark_canceled(self, reason: str = "Canceled by request.") -> None:
        """Mark transaction as canceled."""
        self.status = TransactionStatus.CANCELED
        self.failure_reason = reason
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Return transaction state as a serializable dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "transaction_type": self.transaction_type.value,
            "amount": str(self.amount),
            "currency": self.currency.value,
            "commission": str(self.commission),
            "sender_account_id": self.sender_account_id,
            "recipient_account_id": self.recipient_account_id,
            "status": self.status.value,
            "failure_reason": self.failure_reason,
            "priority": self.priority,
            "scheduled_at": self.scheduled_at.isoformat(),
            "is_external": self.is_external,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }

    def __str__(self) -> str:
        """Return human-readable transaction representation."""
        return (
            f"Transaction {self.transaction_id} | "
            f"Type: {self.transaction_type.value} | "
            f"Amount: {self.amount} {self.currency.value} | "
            f"Status: {self.status.value}"
        )


class TransactionQueue:
    """Priority queue for immediate, delayed, and canceled transactions."""

    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def add(
        self,
        transaction: Transaction,
        priority: int | None = None,
        scheduled_at: datetime | None = None,
    ) -> None:
        """Add transaction to the queue with optional priority and delay."""
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidOperationError("Only pending transactions can be queued.")

        if self.get_transaction(transaction.transaction_id):
            raise InvalidOperationError(
                f"Transaction already exists in queue: {transaction.transaction_id}."
            )

        if priority is not None:
            transaction.priority = Transaction._validate_priority(priority)

        if scheduled_at is not None:
            transaction.scheduled_at = Transaction._validate_scheduled_at(scheduled_at)

        transaction.updated_at = datetime.now()
        self._transactions.append(transaction)

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Return transaction by id if it is queued."""
        for transaction in self._transactions:
            if transaction.transaction_id == transaction_id:
                return transaction

        return None

    def cancel(self, transaction_id: str, reason: str = "Canceled in queue.") -> bool:
        """Cancel a queued transaction by id."""
        transaction = self.get_transaction(transaction_id)

        if not transaction or transaction.status != TransactionStatus.PENDING:
            return False

        transaction.mark_canceled(reason)
        self._transactions.remove(transaction)
        return True

    def get_ready_transactions(self, current_time: datetime | None = None) -> list[Transaction]:
        """Return ready pending transactions ordered by priority and creation time."""
        now = current_time or datetime.now()

        if not isinstance(now, datetime):
            raise InvalidOperationError("Current time must be a datetime.")

        ready_transactions = [
            transaction
            for transaction in self._transactions
            if transaction.status == TransactionStatus.PENDING
            and transaction.scheduled_at <= now
        ]
        return sorted(
            ready_transactions,
            key=lambda transaction: (-transaction.priority, transaction.created_at),
        )

    def remove(self, transaction_id: str) -> bool:
        """Remove a transaction from the queue."""
        transaction = self.get_transaction(transaction_id)

        if not transaction:
            return False

        self._transactions.remove(transaction)
        return True

    def pending_count(self) -> int:
        """Return number of pending transactions in the queue."""
        return len([
            transaction
            for transaction in self._transactions
            if transaction.status == TransactionStatus.PENDING
        ])

    def all_transactions(self) -> list[Transaction]:
        """Return a queue snapshot."""
        return list(self._transactions)

class Client:
    """Bank client with profile, security status, and linked accounts."""

    def __init__(
        self,
        full_name: str,
        age: int,
        password: str,
        contacts: dict[str, str] | None = None,
        client_id: str | None = None,
        status: ClientStatus | str = ClientStatus.ACTIVE,
    ) -> None:
        self.client_id = client_id or self._generate_client_id()
        self.full_name = self._validate_full_name(full_name)
        self.age = self._validate_age(age)
        self.password = self._validate_password(password)
        self.contacts = self._validate_contacts(contacts or {})
        self.status = self._validate_status(status)
        self.account_ids: list[str] = []
        self.failed_login_attempts = 0
        self.suspicious_actions: list[str] = []

    @staticmethod
    def _generate_client_id() -> str:
        """Generate a short UUID-based client identifier."""
        return uuid4().hex[:10]

    @staticmethod
    def _validate_full_name(full_name: str) -> str:
        """Validate and normalize client full name."""
        if not isinstance(full_name, str):
            raise InvalidOperationError("Client full name must be a string.")

        normalized_name = full_name.strip()

        if not normalized_name:
            raise InvalidOperationError("Client full name cannot be empty.")

        return normalized_name

    @staticmethod
    def _validate_age(age: int) -> int:
        """Validate that a client is an adult."""
        if not isinstance(age, int):
            raise InvalidOperationError("Client age must be an integer.")

        if age < 18:
            raise InvalidOperationError("Client must be at least 18 years old.")

        return age

    @staticmethod
    def _validate_password(password: str) -> str:
        """Validate authentication password for training purposes."""
        if not isinstance(password, str) or not password:
            raise InvalidOperationError("Client password cannot be empty.")

        return password

    @staticmethod
    def _validate_contacts(contacts: dict[str, str]) -> dict[str, str]:
        """Validate contact data and keep string keys and values."""
        if not isinstance(contacts, dict):
            raise InvalidOperationError("Client contacts must be a dictionary.")

        return {str(key): str(value) for key, value in contacts.items()}

    @staticmethod
    def _validate_status(status: ClientStatus | str) -> ClientStatus:
        """Validate client status and convert it to ClientStatus enum."""
        try:
            return ClientStatus(status)
        except ValueError:
            valid_statuses = ", ".join(status.value for status in ClientStatus)
            raise InvalidOperationError(
                f"Invalid client status: {status}. "
                f"Available statuses: {valid_statuses}."
            )

    def add_account(self, account_id: str) -> None:
        """Attach an account number to the client."""
        if account_id not in self.account_ids:
            self.account_ids.append(account_id)

    def remove_account(self, account_id: str) -> None:
        """Detach an account number from the client."""
        if account_id in self.account_ids:
            self.account_ids.remove(account_id)

    def mark_suspicious(self, reason: str) -> None:
        """Record a suspicious client action."""
        self.suspicious_actions.append(reason)

        if self.status == ClientStatus.ACTIVE:
            self.status = ClientStatus.SUSPICIOUS

    def block(self, reason: str) -> None:
        """Block the client and record the reason."""
        self.status = ClientStatus.BLOCKED
        self.suspicious_actions.append(reason)

    def reset_authentication_failures(self) -> None:
        """Reset failed login counter after a successful login."""
        self.failed_login_attempts = 0

    def get_client_info(self) -> dict:
        """Return client information as a serializable dictionary."""
        return {
            "client_id": self.client_id,
            "full_name": self.full_name,
            "age": self.age,
            "status": self.status.value,
            "account_ids": list(self.account_ids),
            "contacts": dict(self.contacts),
            "failed_login_attempts": self.failed_login_attempts,
            "suspicious_actions": list(self.suspicious_actions),
        }

    def __str__(self) -> str:
        """Return human-readable client representation."""
        return (
            f"Client | Name: {self.full_name} | "
            f"ID: {self.client_id} | "
            f"Status: {self.status.value} | "
            f"Accounts: {len(self.account_ids)}"
        )

class Bank:
    """Central bank system for clients, accounts, and security policies."""

    ACCOUNT_TYPES = {
        "base": BankAccount,
        "bank": BankAccount,
        "savings": SavingsAccount,
        "premium": PremiumAccount,
        "investment": InvestmentAccount,
    }

    def __init__(self, name: str, now_provider=None) -> None:
        self.name = self._validate_name(name)
        self.clients: dict[str, Client] = {}
        self.accounts: dict[str, BankAccount] = {}
        self.security_events: list[dict] = []
        self.now_provider = now_provider or datetime.now

    @staticmethod
    def _validate_name(name: str) -> str:
        """Validate bank name."""
        if not isinstance(name, str):
            raise InvalidOperationError("Bank name must be a string.")

        normalized_name = name.strip()

        if not normalized_name:
            raise InvalidOperationError("Bank name cannot be empty.")

        return normalized_name

    def _get_current_time(self) -> time:
        """Return current time using injected provider for deterministic demos/tests."""
        current_value = self.now_provider()

        if isinstance(current_value, datetime):
            return current_value.time()

        if isinstance(current_value, time):
            return current_value

        raise InvalidOperationError("now_provider must return datetime or time.")

    def _ensure_operations_are_allowed(self) -> None:
        """Block sensitive bank operations during the night restriction window."""
        current_time = self._get_current_time()

        if time(0, 0) <= current_time < time(5, 0):
            self._record_security_event(
                "system",
                "Operation blocked by night restriction.",
            )
            raise SecurityRestrictionError("Bank operations are blocked from 00:00 to 05:00.")

    def _record_security_event(self, client_id: str, reason: str) -> None:
        """Append a structured security event."""
        self.security_events.append(
            {
                "client_id": client_id,
                "reason": reason,
                "date": date.today().isoformat(),
            }
        )

    def _get_client(self, client_id: str) -> Client:
        """Return client by id or raise a domain error."""
        try:
            return self.clients[client_id]
        except KeyError:
            self._record_security_event(client_id, "Unknown client access attempt.")
            raise InvalidOperationError(f"Client not found: {client_id}.")

    def _get_account(self, account_id: str) -> BankAccount:
        """Return account by id or raise a domain error."""
        try:
            return self.accounts[account_id]
        except KeyError:
            raise InvalidOperationError(f"Account not found: {account_id}.")

    def _ensure_client_can_operate(self, client: Client) -> None:
        """Ensure client is not blocked."""
        if client.status == ClientStatus.BLOCKED:
            self._record_security_event(client.client_id, "Blocked client operation attempt.")
            raise ClientBlockedError("Client is blocked.")

    def _create_account(
        self,
        account_type: str | type[BankAccount],
        owner: str,
        balance: Decimal | int | float | str,
        currency: Currency | str,
        **account_options,
    ) -> BankAccount:
        """Create an account object using a registered account type."""
        if isinstance(account_type, str):
            normalized_account_type = account_type.strip().lower()
            try:
                account_class = self.ACCOUNT_TYPES[normalized_account_type]
            except KeyError:
                valid_types = ", ".join(sorted(self.ACCOUNT_TYPES))
                raise InvalidOperationError(
                    f"Invalid account type: {account_type}. Available types: {valid_types}."
                )
        elif isinstance(account_type, type) and issubclass(account_type, BankAccount):
            account_class = account_type
        else:
            raise InvalidOperationError("Account type must be a supported name or class.")

        return account_class(
            owner=owner,
            balance=balance,
            currency=currency,
            **account_options,
        )

    def add_client(self, client: Client) -> None:
        """Register a client in the bank."""
        self._ensure_operations_are_allowed()

        if client.client_id in self.clients:
            raise InvalidOperationError(f"Client already exists: {client.client_id}.")

        self.clients[client.client_id] = client

    def open_account(
        self,
        client_id: str,
        account_type: str | type[BankAccount] = "base",
        balance: Decimal | int | float | str = Decimal("0"),
        currency: Currency | str = Currency.RUB,
        **account_options,
    ) -> BankAccount:
        """Open an account for a registered client."""
        self._ensure_operations_are_allowed()
        client = self._get_client(client_id)
        self._ensure_client_can_operate(client)

        account = self._create_account(
            account_type=account_type,
            owner=client.full_name,
            balance=balance,
            currency=currency,
            **account_options,
        )

        if account.account_id in self.accounts:
            raise InvalidOperationError(f"Account already exists: {account.account_id}.")

        self.accounts[account.account_id] = account
        client.add_account(account.account_id)
        return account

    def close_account(self, account_id: str) -> None:
        """Close an account."""
        self._ensure_operations_are_allowed()
        account = self._get_account(account_id)

        if account.status == AccountStatus.CLOSED:
            raise AccountClosedError("Account is already closed.")

        account.status = AccountStatus.CLOSED

    def freeze_account(self, account_id: str, reason: str = "Manual freeze") -> None:
        """Freeze an account and mark the related client as suspicious."""
        self._ensure_operations_are_allowed()
        account = self._get_account(account_id)

        if account.status == AccountStatus.CLOSED:
            raise AccountClosedError("Closed account cannot be frozen.")

        account.status = AccountStatus.FROZEN
        self.mark_suspicious_action(account_id, reason)

    def unfreeze_account(self, account_id: str) -> None:
        """Return a frozen account to active status."""
        self._ensure_operations_are_allowed()
        account = self._get_account(account_id)

        if account.status == AccountStatus.CLOSED:
            raise AccountClosedError("Closed account cannot be unfrozen.")

        account.status = AccountStatus.ACTIVE

    def authenticate_client(self, client_id: str, password: str) -> bool:
        """Authenticate a client and block after three failed attempts."""
        self._ensure_operations_are_allowed()
        client = self._get_client(client_id)

        if client.status == ClientStatus.BLOCKED:
            self._record_security_event(client_id, "Blocked client authentication attempt.")
            raise ClientBlockedError("Client is blocked.")

        if client.password == password:
            client.reset_authentication_failures()
            return True

        client.failed_login_attempts += 1
        self._record_security_event(client_id, "Failed authentication attempt.")

        if client.failed_login_attempts >= 3:
            client.block("Three failed authentication attempts.")
            self._record_security_event(client_id, "Client blocked after failed attempts.")
            raise ClientBlockedError("Client was blocked after three failed attempts.")

        raise AuthenticationError("Invalid client credentials.")

    def mark_suspicious_action(self, account_id: str, reason: str) -> None:
        """Mark an account-related action as suspicious for the owning client."""
        account = self._get_account(account_id)

        for client in self.clients.values():
            if account.account_id in client.account_ids:
                client.mark_suspicious(reason)
                self._record_security_event(client.client_id, reason)
                return

        self._record_security_event("unknown", f"Suspicious action for unowned account {account_id}.")

    def search_accounts(
        self,
        owner: str | None = None,
        status: AccountStatus | str | None = None,
        currency: Currency | str | None = None,
        account_type: str | None = None,
    ) -> list[BankAccount]:
        """Search accounts by owner, status, currency, and account type."""
        normalized_owner = owner.lower().strip() if owner else None
        normalized_status = AccountStatus(status) if status else None
        normalized_currency = Currency(currency) if currency else None
        normalized_account_class = None

        if account_type:
            normalized_account_type = account_type.lower().strip()
            normalized_account_class = self.ACCOUNT_TYPES.get(normalized_account_type)

            if normalized_account_class is None:
                for registered_account_class in set(self.ACCOUNT_TYPES.values()):
                    if registered_account_class.__name__.lower() == normalized_account_type:
                        normalized_account_class = registered_account_class
                        break

            if normalized_account_class is None:
                valid_types = ", ".join(sorted(self.ACCOUNT_TYPES))
                raise InvalidOperationError(
                    f"Invalid account type: {account_type}. Available types: {valid_types}."
                )

        result = []

        for account in self.accounts.values():
            if normalized_owner and normalized_owner not in account.owner.lower():
                continue

            if normalized_status and account.status != normalized_status:
                continue

            if normalized_currency and account.currency != normalized_currency:
                continue

            if normalized_account_class and type(account) is not normalized_account_class:
                continue

            result.append(account)

        return result

    def get_total_balance(self, include_investments: bool = True) -> dict[str, str]:
        """Return total bank balance grouped by currency."""
        totals: dict[str, Decimal] = {}

        for account in self.accounts.values():
            if account.status == AccountStatus.CLOSED:
                continue

            account_total = account.balance

            if include_investments and isinstance(account, InvestmentAccount):
                account_total += account.portfolio_value

            currency = account.currency.value
            totals[currency] = totals.get(currency, Decimal("0")) + account_total

        return {currency: str(total) for currency, total in totals.items()}

    def get_clients_ranking(self) -> list[dict]:
        """Return clients ordered by total value of their active accounts."""
        ranking = []

        for client in self.clients.values():
            total_value = Decimal("0")

            for account_id in client.account_ids:
                account = self.accounts.get(account_id)

                if not account or account.status == AccountStatus.CLOSED:
                    continue

                total_value += account.balance

                if isinstance(account, InvestmentAccount):
                    total_value += account.portfolio_value

            ranking.append(
                {
                    "client_id": client.client_id,
                    "full_name": client.full_name,
                    "status": client.status.value,
                    "total_value": str(total_value),
                    "account_count": len(client.account_ids),
                }
            )

        return sorted(
            ranking,
            key=lambda client_info: Decimal(client_info["total_value"]),
            reverse=True,
        )

    def get_bank_info(self) -> dict:
        """Return bank state summary."""
        return {
            "name": self.name,
            "clients_count": len(self.clients),
            "accounts_count": len(self.accounts),
            "total_balance": self.get_total_balance(),
            "security_events": list(self.security_events),
        }


class AuditLog:
    """In-memory and file-backed audit event storage."""

    LEVEL_ORDER = {
        AuditLevel.INFO: 1,
        AuditLevel.WARNING: 2,
        AuditLevel.ERROR: 3,
        AuditLevel.CRITICAL: 4,
    }

    def __init__(self, file_path: str | None = None) -> None:
        self.events: list[dict] = []
        self.file_path = file_path

    def log(
        self,
        level: AuditLevel | str,
        event_type: str,
        message: str,
        transaction: Transaction | None = None,
        client_id: str | None = None,
        account_id: str | None = None,
        risk_level: RiskLevel | str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Store an audit event in memory and optionally append it to a file."""
        validated_level = AuditLevel(level)
        validated_risk_level = RiskLevel(risk_level).value if risk_level else None
        event = {
            "event_id": uuid4().hex[:14],
            "timestamp": datetime.now().isoformat(),
            "level": validated_level.value,
            "event_type": event_type,
            "message": message,
            "transaction_id": transaction.transaction_id if transaction else None,
            "client_id": client_id,
            "account_id": account_id,
            "risk_level": validated_risk_level,
            "metadata": metadata or {},
        }
        self.events.append(event)

        if self.file_path:
            self._append_to_file(event)

        return event

    def _append_to_file(self, event: dict) -> None:
        """Append one audit event as a JSON line."""
        with open(self.file_path, "a", encoding="utf-8") as audit_file:
            audit_file.write(json.dumps(event, ensure_ascii=True) + "\n")

    def save_to_file(self, file_path: str | None = None) -> None:
        """Persist all in-memory events to a JSONL file."""
        target_file_path = file_path or self.file_path

        if not target_file_path:
            raise InvalidOperationError("Audit file path is required.")

        with open(target_file_path, "w", encoding="utf-8") as audit_file:
            for event in self.events:
                audit_file.write(json.dumps(event, ensure_ascii=True) + "\n")

    def filter_events(
        self,
        level: AuditLevel | str | None = None,
        min_level: AuditLevel | str | None = None,
        event_type: str | None = None,
        transaction_id: str | None = None,
        client_id: str | None = None,
        account_id: str | None = None,
        risk_level: RiskLevel | str | None = None,
    ) -> list[dict]:
        """Filter audit events by common audit dimensions."""
        exact_level = AuditLevel(level).value if level else None
        minimum_level = AuditLevel(min_level) if min_level else None
        validated_risk_level = RiskLevel(risk_level).value if risk_level else None
        filtered_events = []

        for event in self.events:
            event_level = AuditLevel(event["level"])

            if exact_level and event["level"] != exact_level:
                continue

            if minimum_level and self.LEVEL_ORDER[event_level] < self.LEVEL_ORDER[minimum_level]:
                continue

            if event_type and event["event_type"] != event_type:
                continue

            if transaction_id and event["transaction_id"] != transaction_id:
                continue

            if client_id and event["client_id"] != client_id:
                continue

            if account_id and event["account_id"] != account_id:
                continue

            if validated_risk_level and event["risk_level"] != validated_risk_level:
                continue

            filtered_events.append(event)

        return filtered_events

    def get_suspicious_operations(self) -> list[dict]:
        """Return audit events for medium and high risk operations."""
        return [
            event
            for event in self.events
            if event.get("risk_level") in {RiskLevel.MEDIUM.value, RiskLevel.HIGH.value}
        ]

    def get_error_statistics(self) -> dict:
        """Return grouped error statistics from audit events."""
        statistics = {
            "total_errors": 0,
            "by_event_type": {},
            "by_message": {},
        }

        for event in self.filter_events(min_level=AuditLevel.ERROR):
            statistics["total_errors"] += 1
            event_type = event["event_type"]
            message = event["message"]
            statistics["by_event_type"][event_type] = (
                statistics["by_event_type"].get(event_type, 0) + 1
            )
            statistics["by_message"][message] = statistics["by_message"].get(message, 0) + 1

        return statistics


class RiskAnalyzer:
    """Analyze transaction risk and maintain client risk profiles."""

    def __init__(
        self,
        large_amount_threshold: Decimal | int | float | str = Decimal("100000"),
        frequent_operations_threshold: int = 3,
        frequent_operations_window_minutes: int = 10,
    ) -> None:
        self.large_amount_threshold = AbstractAccount._validate_amount(large_amount_threshold)
        self.frequent_operations_threshold = frequent_operations_threshold
        self.frequent_operations_window_minutes = frequent_operations_window_minutes
        self.client_operation_times: dict[str, list[datetime]] = {}
        self.known_recipients: dict[str, set[str]] = {}
        self.suspicious_operations: list[dict] = []
        self.client_risk_scores: dict[str, int] = {}
        self.client_risk_reasons: dict[str, list[str]] = {}

    def analyze(
        self,
        transaction: Transaction,
        bank: Bank,
        current_time: datetime | None = None,
    ) -> dict:
        """Analyze transaction and return risk details."""
        now = current_time or datetime.now()
        client_id = self._find_client_id_for_transaction(bank, transaction)
        reasons = []
        score = 0

        if transaction.amount >= self.large_amount_threshold:
            reasons.append("large_amount")
            score += 2

        if client_id and self._is_frequent_operation(client_id, now):
            reasons.append("frequent_operations")
            score += 2

        if self._is_new_recipient(transaction, client_id):
            reasons.append("new_recipient")
            score += 1

        if time(0, 0) <= now.time() < time(5, 0):
            reasons.append("night_operation")
            score += 2

        if score >= 3:
            risk_level = RiskLevel.HIGH
        elif score > 0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        risk_report = {
            "transaction_id": transaction.transaction_id,
            "client_id": client_id,
            "risk_level": risk_level.value,
            "risk_score": score,
            "reasons": reasons,
        }

        if risk_level != RiskLevel.LOW:
            self.suspicious_operations.append(risk_report)
            if client_id:
                self.client_risk_scores[client_id] = self.client_risk_scores.get(client_id, 0) + score
                self.client_risk_reasons.setdefault(client_id, []).extend(reasons)

        return risk_report

    def register_transaction(
        self,
        transaction: Transaction,
        bank: Bank,
        current_time: datetime | None = None,
    ) -> None:
        """Record a successfully processed transaction as known client activity."""
        client_id = self._find_client_id_for_transaction(bank, transaction)

        if not client_id:
            return

        operation_time = current_time or datetime.now()
        self.client_operation_times.setdefault(client_id, []).append(operation_time)

        if transaction.recipient_account_id:
            self.known_recipients.setdefault(client_id, set()).add(transaction.recipient_account_id)

    def _is_frequent_operation(self, client_id: str, now: datetime) -> bool:
        """Return True when client has too many recent operations."""
        window_start = now - timedelta(minutes=self.frequent_operations_window_minutes)
        recent_operations = [
            operation_time
            for operation_time in self.client_operation_times.get(client_id, [])
            if operation_time >= window_start
        ]
        self.client_operation_times[client_id] = recent_operations
        return len(recent_operations) + 1 >= self.frequent_operations_threshold

    def _is_new_recipient(self, transaction: Transaction, client_id: str | None) -> bool:
        """Return True when transfer recipient is new for the sender."""
        if (
            transaction.transaction_type != TransactionType.TRANSFER
            or not client_id
            or not transaction.recipient_account_id
        ):
            return False

        return transaction.recipient_account_id not in self.known_recipients.get(client_id, set())

    def _find_client_id_for_transaction(
        self,
        bank: Bank,
        transaction: Transaction,
    ) -> str | None:
        """Find the client related to a transaction."""
        return self._find_client_id_by_account(
            bank,
            transaction.sender_account_id or transaction.recipient_account_id,
        )

    @staticmethod
    def _find_client_id_by_account(bank: Bank, account_id: str | None) -> str | None:
        """Find owning client id for an account."""
        if not account_id:
            return None

        for client in bank.clients.values():
            if account_id in client.account_ids:
                return client.client_id

        return None

    def get_suspicious_operations(self) -> list[dict]:
        """Return suspicious risk reports."""
        return list(self.suspicious_operations)

    def get_client_risk_profile(self, client_id: str) -> dict:
        """Return aggregated risk profile for a client."""
        score = self.client_risk_scores.get(client_id, 0)

        if score >= 6:
            risk_level = RiskLevel.HIGH
        elif score > 0:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        reasons = self.client_risk_reasons.get(client_id, [])
        reason_counts = {
            reason: reasons.count(reason)
            for reason in sorted(set(reasons))
        }

        return {
            "client_id": client_id,
            "risk_level": risk_level.value,
            "risk_score": score,
            "reason_counts": reason_counts,
        }

class TransactionProcessor:
    """Process queued transactions for a bank account registry."""

    DEFAULT_EXCHANGE_RATES = {
        Currency.RUB.value: Decimal("1"),
        Currency.USD.value: Decimal("90"),
        Currency.EUR.value: Decimal("100"),
        Currency.KZT.value: Decimal("0.2"),
        Currency.CNY.value: Decimal("12"),
    }

    def __init__(
        self,
        bank: Bank,
        exchange_rates: dict[Currency | str, Decimal | int | float | str] | None = None,
        external_transfer_fee_rate: Decimal | int | float | str = Decimal("0.01"),
        internal_transfer_fee: Decimal | int | float | str = Decimal("0"),
        audit_log: AuditLog | None = None,
        risk_analyzer: RiskAnalyzer | None = None,
    ) -> None:
        self.bank = bank
        self.exchange_rates = self._validate_exchange_rates(
            exchange_rates or self.DEFAULT_EXCHANGE_RATES
        )
        self.external_transfer_fee_rate = AbstractAccount._validate_amount(
            external_transfer_fee_rate
        )
        self.internal_transfer_fee = AbstractAccount._validate_amount(internal_transfer_fee)
        self.error_log: list[dict] = []
        self.processed_transactions: list[str] = []
        self.audit_log = audit_log or AuditLog()
        self.risk_analyzer = risk_analyzer or RiskAnalyzer()

    @staticmethod
    def _validate_exchange_rates(
        exchange_rates: dict[Currency | str, Decimal | int | float | str],
    ) -> dict[str, Decimal]:
        """Validate conversion rates against the base currency."""
        validated_rates = {}

        for currency, rate in exchange_rates.items():
            validated_currency = BankAccount._validate_currency(currency)
            validated_rate = AbstractAccount._validate_amount(rate)

            if validated_rate == 0:
                raise InvalidOperationError("Exchange rate must be greater than zero.")

            validated_rates[validated_currency.value] = validated_rate

        missing_currencies = [
            currency.value
            for currency in Currency
            if currency.value not in validated_rates
        ]

        if missing_currencies:
            raise InvalidOperationError(
                f"Missing exchange rates for: {', '.join(missing_currencies)}."
            )

        return validated_rates

    def _get_account(self, account_id: str | None, role: str) -> BankAccount:
        """Return account from the managed bank by id."""
        if not account_id:
            raise InvalidOperationError(f"{role} account is required.")

        return self.bank._get_account(account_id)

    def _convert(
        self,
        amount: Decimal,
        source_currency: Currency,
        target_currency: Currency,
    ) -> Decimal:
        """Convert amount between supported currencies."""
        if source_currency == target_currency:
            return amount

        source_rate = self.exchange_rates[source_currency.value]
        target_rate = self.exchange_rates[target_currency.value]
        return amount * source_rate / target_rate

    def _calculate_commission(self, transaction: Transaction) -> Decimal:
        """Calculate transaction commission in transaction currency."""
        if transaction.commission > 0:
            return transaction.commission

        if transaction.transaction_type == TransactionType.TRANSFER and transaction.is_external:
            return transaction.amount * self.external_transfer_fee_rate

        if transaction.transaction_type == TransactionType.TRANSFER:
            return self.internal_transfer_fee

        return Decimal("0")

    def _ensure_transfer_is_allowed(self, sender_account: BankAccount) -> None:
        """Block transfers from negative balances except for premium accounts."""
        if sender_account.balance < 0 and not isinstance(sender_account, PremiumAccount):
            raise InvalidOperationError(
                "Transfers from negative balance are allowed only for premium accounts."
            )

    def process_transaction(self, transaction: Transaction) -> Transaction:
        """Process one transaction with retry attempts, audit, and risk checks."""
        if transaction.status != TransactionStatus.PENDING:
            raise InvalidOperationError("Only pending transactions can be processed.")

        risk_time = datetime.combine(date.today(), self.bank._get_current_time())
        risk_report = self.risk_analyzer.analyze(
            transaction,
            self.bank,
            current_time=risk_time,
        )
        self._audit_risk_report(transaction, risk_report)

        try:
            self.bank._ensure_operations_are_allowed()
        except Exception as error:
            reason = str(error)
            transaction.mark_failed(reason)
            self._record_error(transaction, reason)
            self.audit_log.log(
                AuditLevel.ERROR,
                "transaction_failed",
                reason,
                transaction=transaction,
            )
            return transaction

        if risk_report["risk_level"] == RiskLevel.HIGH.value:
            reasons = ", ".join(risk_report["reasons"])
            reason = f"High-risk transaction blocked: {reasons}."
            transaction.mark_failed(reason)
            self._record_error(transaction, reason)
            self.audit_log.log(
                AuditLevel.ERROR,
                "transaction_failed",
                reason,
                transaction=transaction,
            )
            return transaction

        while transaction.retry_count <= transaction.max_retries:
            try:
                transaction.mark_processing()
                self._apply_transaction(transaction)
                transaction.mark_completed()
                self.risk_analyzer.register_transaction(
                    transaction,
                    self.bank,
                    current_time=risk_time,
                )
                self.processed_transactions.append(transaction.transaction_id)
                self.audit_log.log(
                    AuditLevel.INFO,
                    "transaction_completed",
                    "Transaction completed.",
                    transaction=transaction,
                    risk_level=risk_report["risk_level"],
                    metadata=risk_report,
                )
                return transaction
            except Exception as error:
                reason = str(error)
                self._record_error(transaction, reason)

                if transaction.retry_count >= transaction.max_retries:
                    transaction.mark_failed(reason)
                    self.audit_log.log(
                        AuditLevel.ERROR,
                        "transaction_failed",
                        reason,
                        transaction=transaction,
                    )
                    return transaction

                transaction.retry_count += 1
                transaction.status = TransactionStatus.PENDING
                transaction.updated_at = datetime.now()

        return transaction


    def _audit_risk_report(self, transaction: Transaction, risk_report: dict) -> None:
        """Write risk analyzer output to the audit log."""
        risk_level = RiskLevel(risk_report["risk_level"])

        if risk_level == RiskLevel.HIGH:
            audit_level = AuditLevel.CRITICAL
            event_type = "transaction_blocked_by_risk"
            message = "High-risk transaction detected."
        elif risk_level == RiskLevel.MEDIUM:
            audit_level = AuditLevel.WARNING
            event_type = "transaction_suspicious"
            message = "Suspicious transaction detected."
        else:
            audit_level = AuditLevel.INFO
            event_type = "transaction_risk_checked"
            message = "Transaction risk checked."

        self.audit_log.log(
            audit_level,
            event_type,
            message,
            transaction=transaction,
            client_id=risk_report.get("client_id"),
            risk_level=risk_level,
            metadata=risk_report,
        )

    def _apply_transaction(self, transaction: Transaction) -> None:
        """Apply transaction balance changes."""
        self.bank._ensure_operations_are_allowed()

        commission = self._calculate_commission(transaction)
        transaction.commission = commission

        if transaction.transaction_type == TransactionType.DEPOSIT:
            recipient_account = self._get_account(
                transaction.recipient_account_id,
                "Recipient",
            )
            deposit_amount = self._convert(
                transaction.amount,
                transaction.currency,
                recipient_account.currency,
            )
            recipient_account.deposit(deposit_amount)
            return

        if transaction.transaction_type == TransactionType.WITHDRAW:
            sender_account = self._get_account(transaction.sender_account_id, "Sender")
            withdraw_amount = self._convert(
                transaction.amount + commission,
                transaction.currency,
                sender_account.currency,
            )
            sender_account.withdraw(withdraw_amount)
            return

        if transaction.transaction_type == TransactionType.TRANSFER:
            sender_account = self._get_account(transaction.sender_account_id, "Sender")
            recipient_account = self._get_account(
                transaction.recipient_account_id,
                "Recipient",
            )
            self._ensure_transfer_is_allowed(sender_account)
            sender_account._ensure_account_is_available()
            recipient_account._ensure_account_is_available()

            debit_amount = self._convert(
                transaction.amount + commission,
                transaction.currency,
                sender_account.currency,
            )
            credit_amount = self._convert(
                transaction.amount,
                transaction.currency,
                recipient_account.currency,
            )
            sender_account.withdraw(debit_amount)
            recipient_account.deposit(credit_amount)
            return

        raise InvalidOperationError("Unsupported transaction type.")

    def process_queue(
        self,
        transaction_queue: TransactionQueue,
        current_time: datetime | None = None,
    ) -> list[Transaction]:
        """Process all ready transactions from a queue."""
        processed = []

        for transaction in transaction_queue.get_ready_transactions(current_time):
            processed_transaction = self.process_transaction(transaction)
            processed.append(processed_transaction)
            transaction_queue.remove(transaction.transaction_id)

        return processed

    def _record_error(self, transaction: Transaction, reason: str) -> None:
        """Record transaction processing failure."""
        self.error_log.append(
            {
                "transaction_id": transaction.transaction_id,
                "reason": reason,
                "retry_count": transaction.retry_count,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.audit_log.log(
            AuditLevel.ERROR,
            "transaction_processing_error",
            reason,
            transaction=transaction,
            metadata={"retry_count": transaction.retry_count},
        )