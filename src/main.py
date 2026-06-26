from models import (
    AccountFrozenError,
    BankAccount,
    Currency,
    InsufficientFundsError,
    InvestmentAccount,
    InvalidOperationError,
    PremiumAccount,
    SavingsAccount,
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


def run_day_1_demo() -> None:
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

    print("Day 1. Basic accounts:")
    show_account(active_account)
    show_account(frozen_account)

    active_account.deposit(250)
    active_account.withdraw(400)
    print("After valid deposit and withdrawal:")
    show_account(active_account)

    try:
        frozen_account.deposit(100)
    except AccountFrozenError as error:
        print(f"Expected frozen account error: {error}")
        print("-" * 80)

    try:
        active_account.withdraw(10_000)
    except InsufficientFundsError as error:
        print(f"Expected insufficient funds error: {error}")
        print("-" * 80)

    try:
        active_account.deposit(-100)
    except InvalidOperationError as error:
        print(f"Expected invalid operation error: {error}")
        print("-" * 80)


def run_day_2_demo() -> None:
    """Run a demo for Day 2 advanced account types."""
    savings_account = SavingsAccount(
        owner="Anna Smirnova",
        balance=50_000,
        currency=Currency.RUB,
        min_balance=10_000,
        monthly_interest_rate="0.015",
    )

    premium_account = PremiumAccount(
        owner="Sergey Volkov",
        balance=20_000,
        currency=Currency.EUR,
        overdraft_limit=5_000,
        withdrawal_limit=50_000,
        fixed_commission=25,
    )

    investment_account = InvestmentAccount(
        owner="Maria Kuznetsova",
        balance=15_000,
        currency=Currency.USD,
        portfolio={
            "stocks": 40_000,
            "bonds": 20_000,
            "etf": 30_000,
        },
    )

    print("Day 2. Advanced accounts:")
    show_account(savings_account)
    show_account(premium_account)
    show_account(investment_account)

    interest_amount = savings_account.apply_monthly_interest()
    savings_account.withdraw(5_000)
    print(f"Savings account after interest {interest_amount} and withdrawal:")
    show_account(savings_account)

    try:
        savings_account.withdraw(40_000)
    except InsufficientFundsError as error:
        print(f"Expected savings minimum balance error: {error}")
        print("-" * 80)

    premium_account.withdraw(23_000)
    print("Premium account after overdraft withdrawal with commission:")
    show_account(premium_account)

    try:
        premium_account.withdraw(60_000)
    except InvalidOperationError as error:
        print(f"Expected premium limit error: {error}")
        print("-" * 80)

    investment_account.withdraw(5_000)
    print("Investment account after cash withdrawal:")
    show_account(investment_account)

    print("Investment yearly growth projection:")
    print(investment_account.project_yearly_growth())
    print("-" * 80)

    try:
        investment_account.withdraw(20_000)
    except InsufficientFundsError as error:
        print(f"Expected investment cash error: {error}")
        print("-" * 80)


def main() -> None:
    """Run demonstration scenarios for implemented project days."""
    run_day_1_demo()
    run_day_2_demo()


if __name__ == "__main__":
    main()
