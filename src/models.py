from abc import ABC, abstractmethod
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


class AccountStatus(str, Enum):
    """
    Account lifecycle status.

    String-based enum is used to keep values easy to serialize
    into JSON, logs, reports, or ML/analytics datasets.
    """

    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


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