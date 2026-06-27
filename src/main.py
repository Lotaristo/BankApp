from datetime import time

from models import (
    AccountFrozenError,
    AuthenticationError,
    Bank,
    BankAccount,
    Client,
    ClientBlockedError,
    Currency,
    InsufficientFundsError,
    InvestmentAccount,
    InvalidOperationError,
    PremiumAccount,
    SavingsAccount,
    SecurityRestrictionError,
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




def run_day_3_demo() -> None:
    """Run a demo for Day 3 bank management and security requirements."""
    bank = Bank("Training Bank", now_provider=lambda: time(10, 30))

    first_client = Client(
        full_name="Alexey Orlov",
        age=34,
        password="secure-123",
        contacts={"phone": "+7 900 100-20-30", "email": "alexey@example.com"},
    )
    second_client = Client(
        full_name="Elena Morozova",
        age=29,
        password="strong-456",
        contacts={"phone": "+7 900 200-30-40"},
    )
    blocked_client = Client(
        full_name="Dmitry Sokolov",
        age=41,
        password="valid-789",
        contacts={"email": "dmitry@example.com"},
    )

    bank.add_client(first_client)
    bank.add_client(second_client)
    bank.add_client(blocked_client)

    base_account = bank.open_account(
        first_client.client_id,
        account_type="base",
        balance=25_000,
        currency=Currency.RUB,
    )
    savings_account = bank.open_account(
        first_client.client_id,
        account_type="savings",
        balance=80_000,
        currency=Currency.RUB,
        min_balance=20_000,
        monthly_interest_rate="0.012",
    )
    investment_account = bank.open_account(
        second_client.client_id,
        account_type="investment",
        balance=10_000,
        currency=Currency.USD,
        portfolio={"stocks": 30_000, "bonds": 10_000, "etf": 15_000},
    )

    print("Day 3. Bank system:")
    print(first_client)
    print(second_client)
    print(blocked_client)
    show_account(base_account)
    show_account(savings_account)
    show_account(investment_account)

    print("Authentication scenarios:")
    print(f"Valid login: {bank.authenticate_client(first_client.client_id, 'secure-123')}")

    for attempt in range(1, 4):
        try:
            bank.authenticate_client(blocked_client.client_id, "wrong-password")
        except AuthenticationError as error:
            print(f"Failed login attempt {attempt}: {error}")
        except ClientBlockedError as error:
            print(f"Client blocked on attempt {attempt}: {error}")
    print(blocked_client.get_client_info())
    print("-" * 80)

    print("Account freeze and unfreeze:")
    bank.freeze_account(base_account.account_id, reason="Manual suspicious activity check")
    show_account(base_account)
    print(first_client.get_client_info())
    bank.unfreeze_account(base_account.account_id)
    show_account(base_account)

    print("Search and analytics:")
    print([account.account_id for account in bank.search_accounts(status="active")])
    print(bank.get_total_balance())
    print(bank.get_clients_ranking())
    print("-" * 80)

    print("Night restriction scenario:")
    night_bank = Bank("Night Bank", now_provider=lambda: time(2, 15))
    try:
        night_bank.add_client(
            Client(
                full_name="Night Client",
                age=30,
                password="night-pass",
                contacts={"phone": "+7 900 000-00-00"},
            )
        )
    except SecurityRestrictionError as error:
        print(f"Expected night restriction error: {error}")
        print(night_bank.get_bank_info())
        print("-" * 80)

def main() -> None:
    """Run demonstration scenarios for implemented project days."""
    run_day_1_demo()
    run_day_2_demo()
    run_day_3_demo()


if __name__ == "__main__":
    main()
