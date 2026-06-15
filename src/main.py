from models import (
    AccountFrozenError,
    BankAccount,
    Currency,
    InsufficientFundsError,
    InvalidOperationError,
)


def show_account(account: BankAccount) -> None:
    """
    Print account state in both human-readable and structured formats.

    The dictionary output imitates what could later be sent to logs,
    reports, APIs, or analytical pipelines.
    """
    print(account)
    print(account.get_account_info())
    print("-" * 80)


def main() -> None:
    """Run a simple demo for Day 1 requirements."""
    active_account = BankAccount(
        owner="Ivan Petrov",
        balance=1000,
        currency=Currency.RUB,
    )

    frozen_account = BankAccount(
        owner="Petr Sidorov",
        balance=500,
        status="frozen",
        currency=Currency.USD,
    )

    print("Created accounts:")
    show_account(active_account)
    show_account(frozen_account)

    print("Valid operations with active account:")

    active_account.deposit(250)
    print("After deposit 250:")
    show_account(active_account)

    active_account.withdraw(400)
    print("After withdraw 400:")
    show_account(active_account)

    print("Trying to operate with frozen account:")

    try:
        frozen_account.deposit(100)
    except AccountFrozenError as error:
        print(f"Expected error: {error}")
        print("-" * 80)

    print("Trying invalid operations:")

    try:
        active_account.withdraw(10_000)
    except InsufficientFundsError as error:
        print(f"Expected error: {error}")
        print("-" * 80)

    try:
        active_account.deposit(-100)
    except InvalidOperationError as error:
        print(f"Expected error: {error}")
        print("-" * 80)


if __name__ == "__main__":
    main()