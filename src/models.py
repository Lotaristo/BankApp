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
