import tempfile
from pathlib import Path
from datetime import datetime, time, timedelta

from models import (
    AccountFrozenError,
    AuditLog,
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
    RiskAnalyzer,
    SavingsAccount,
    SecurityRestrictionError,
    Transaction,
    TransactionProcessor,
    TransactionQueue,
    TransactionStatus,
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



def run_day_4_demo() -> None:
    """Run a demo for Day 4 transaction queue and processor requirements."""
    bank = Bank("Transaction Bank", now_provider=lambda: time(11, 0))
    queue = TransactionQueue()
    processor = TransactionProcessor(bank)

    first_client = Client("Transaction Sender", age=35, password="sender-pass")
    second_client = Client("Transaction Receiver", age=28, password="receiver-pass")
    third_client = Client("Frozen Client", age=45, password="frozen-pass")

    bank.add_client(first_client)
    bank.add_client(second_client)
    bank.add_client(third_client)

    sender_account = bank.open_account(
        first_client.client_id,
        account_type="base",
        balance=50_000,
        currency=Currency.RUB,
    )
    receiver_account = bank.open_account(
        second_client.client_id,
        account_type="base",
        balance=10_000,
        currency=Currency.RUB,
    )
    usd_account = bank.open_account(
        second_client.client_id,
        account_type="base",
        balance=500,
        currency=Currency.USD,
    )
    premium_account = bank.open_account(
        first_client.client_id,
        account_type="premium",
        balance=100,
        currency=Currency.RUB,
        overdraft_limit=1_000,
        withdrawal_limit=10_000,
        fixed_commission=0,
    )
    frozen_account = bank.open_account(
        third_client.client_id,
        account_type="base",
        balance=5_000,
        currency=Currency.RUB,
    )
    bank.freeze_account(frozen_account.account_id, reason="Day 4 frozen account test")

    transactions = [
        Transaction(
            "deposit",
            1_000,
            Currency.RUB,
            recipient_account_id=receiver_account.account_id,
            priority=3,
        ),
        Transaction(
            "withdraw",
            2_000,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
            priority=2,
        ),
        Transaction(
            "transfer",
            3_000,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
            recipient_account_id=receiver_account.account_id,
            priority=4,
        ),
        Transaction(
            "transfer",
            100,
            Currency.USD,
            sender_account_id=usd_account.account_id,
            recipient_account_id=receiver_account.account_id,
            is_external=True,
            max_retries=1,
            priority=5,
        ),
        Transaction(
            "transfer",
            500,
            Currency.RUB,
            sender_account_id=frozen_account.account_id,
            recipient_account_id=receiver_account.account_id,
            max_retries=1,
            priority=6,
        ),
        Transaction(
            "withdraw",
            200_000,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
            max_retries=1,
            priority=1,
        ),
        Transaction(
            "deposit",
            300,
            Currency.RUB,
            recipient_account_id=sender_account.account_id,
            scheduled_at=datetime.now() + timedelta(days=1),
            priority=10,
        ),
        Transaction(
            "deposit",
            700,
            Currency.RUB,
            recipient_account_id=sender_account.account_id,
            priority=7,
        ),
        Transaction(
            "withdraw",
            120,
            Currency.RUB,
            sender_account_id=premium_account.account_id,
            priority=9,
        ),
        Transaction(
            "transfer",
            10,
            Currency.RUB,
            sender_account_id=premium_account.account_id,
            recipient_account_id=receiver_account.account_id,
            priority=8,
        ),
    ]

    for transaction in transactions:
        queue.add(transaction)

    queue.cancel(transactions[7].transaction_id, reason="Demo cancellation before processing.")
    processed_transactions = processor.process_queue(queue)

    print("Day 4. Transactions:")
    print(f"Created transactions: {len(transactions)}")
    print(f"Processed ready transactions: {len(processed_transactions)}")
    print(f"Pending delayed transactions: {queue.pending_count()}")

    for transaction in transactions:
        print(transaction.to_dict())

    print("Transaction errors:")
    print(processor.error_log)
    print("Final balances:")
    show_account(sender_account)
    show_account(receiver_account)
    show_account(usd_account)
    show_account(premium_account)
    show_account(frozen_account)
    print("Completed:", len([
        transaction
        for transaction in transactions
        if transaction.status == TransactionStatus.COMPLETED
    ]))
    print("Failed:", len([
        transaction
        for transaction in transactions
        if transaction.status == TransactionStatus.FAILED
    ]))
    print("Canceled:", len([
        transaction
        for transaction in transactions
        if transaction.status == TransactionStatus.CANCELED
    ]))
    print("-" * 80)



def run_day_5_demo() -> None:
    """Run a demo for Day 5 audit and risk analysis requirements."""
    audit_file_path = str(Path(tempfile.gettempdir()) / "bankapp_day5_audit.jsonl")
    audit_log = AuditLog(file_path=audit_file_path)
    risk_analyzer = RiskAnalyzer(
        large_amount_threshold=100_000,
        frequent_operations_threshold=3,
        frequent_operations_window_minutes=30,
    )
    bank = Bank("Audit Bank", now_provider=lambda: time(14, 0))
    processor = TransactionProcessor(
        bank,
        audit_log=audit_log,
        risk_analyzer=risk_analyzer,
    )

    first_client = Client("Audit Sender", age=36, password="sender-pass")
    second_client = Client("Known Receiver", age=32, password="known-pass")
    third_client = Client("New Receiver", age=27, password="new-pass")
    bank.add_client(first_client)
    bank.add_client(second_client)
    bank.add_client(third_client)

    sender_account = bank.open_account(
        first_client.client_id,
        account_type="base",
        balance=300_000,
        currency=Currency.RUB,
    )
    known_receiver = bank.open_account(
        second_client.client_id,
        account_type="base",
        balance=10_000,
        currency=Currency.RUB,
    )
    new_receiver = bank.open_account(
        third_client.client_id,
        account_type="base",
        balance=5_000,
        currency=Currency.RUB,
    )

    transactions = [
        Transaction(
            "transfer",
            1_000,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
            recipient_account_id=known_receiver.account_id,
        ),
        Transaction(
            "deposit",
            500,
            Currency.RUB,
            recipient_account_id=sender_account.account_id,
        ),
        Transaction(
            "withdraw",
            300,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
        ),
        Transaction(
            "transfer",
            2_000,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
            recipient_account_id=known_receiver.account_id,
        ),
        Transaction(
            "transfer",
            150_000,
            Currency.RUB,
            sender_account_id=sender_account.account_id,
            recipient_account_id=new_receiver.account_id,
        ),
    ]

    for transaction in transactions:
        processor.process_transaction(transaction)

    night_bank = Bank("Night Audit Bank", now_provider=lambda: time(14, 0))
    night_client = Client("Night Sender", age=40, password="night-pass")
    night_receiver_client = Client("Night Receiver", age=41, password="night-receiver")
    night_bank.add_client(night_client)
    night_bank.add_client(night_receiver_client)
    night_sender = night_bank.open_account(
        night_client.client_id,
        account_type="base",
        balance=50_000,
        currency=Currency.RUB,
    )
    night_receiver = night_bank.open_account(
        night_receiver_client.client_id,
        account_type="base",
        balance=1_000,
        currency=Currency.RUB,
    )
    night_bank.now_provider = lambda: time(2, 30)
    night_processor = TransactionProcessor(
        night_bank,
        audit_log=audit_log,
        risk_analyzer=risk_analyzer,
    )
    night_transaction = Transaction(
        "transfer",
        1_000,
        Currency.RUB,
        sender_account_id=night_sender.account_id,
        recipient_account_id=night_receiver.account_id,
    )
    night_processor.process_transaction(night_transaction)

    audit_log.save_to_file(audit_file_path)

    print("Day 5. Audit and risk analysis:")
    for transaction in transactions + [night_transaction]:
        print(transaction.to_dict())

    print("Suspicious audit operations:")
    print(audit_log.get_suspicious_operations())
    print("Client risk profile:")
    print(risk_analyzer.get_client_risk_profile(first_client.client_id))
    print("Night client risk profile:")
    print(risk_analyzer.get_client_risk_profile(night_client.client_id))
    print("Error statistics:")
    print(audit_log.get_error_statistics())
    print("Critical audit events:")
    print(audit_log.filter_events(min_level="critical"))
    print(f"Audit file: {audit_file_path}")
    print("Final balances:")
    show_account(sender_account)
    show_account(known_receiver)
    show_account(new_receiver)
    print("-" * 80)



def run_day_6_demo() -> dict:
    """Run a full-system demo with clients, accounts, queue, audit, and reports."""
    audit_log = AuditLog()
    risk_analyzer = RiskAnalyzer(
        large_amount_threshold=75_000,
        frequent_operations_threshold=20,
        frequent_operations_window_minutes=60,
    )
    bank = Bank("Full Demo Bank", now_provider=lambda: time(13, 0))
    queue = TransactionQueue()
    processor = TransactionProcessor(
        bank,
        audit_log=audit_log,
        risk_analyzer=risk_analyzer,
    )

    clients = [
        Client("Alice Demo", 31, "pass-1", contacts={"email": "alice@example.com"}),
        Client("Boris Demo", 42, "pass-2", contacts={"email": "boris@example.com"}),
        Client("Clara Demo", 29, "pass-3", contacts={"email": "clara@example.com"}),
        Client("Denis Demo", 37, "pass-4", contacts={"email": "denis@example.com"}),
        Client("Eva Demo", 45, "pass-5", contacts={"email": "eva@example.com"}),
        Client("Farid Demo", 33, "pass-6", contacts={"email": "farid@example.com"}),
        Client("Gala Demo", 39, "pass-7", contacts={"email": "gala@example.com"}),
    ]

    for client in clients:
        bank.add_client(client)

    accounts = []
    accounts.append(bank.open_account(clients[0].client_id, "base", 120_000, Currency.RUB))
    accounts.append(bank.open_account(clients[0].client_id, "savings", 90_000, Currency.RUB, min_balance=10_000, monthly_interest_rate="0.01"))
    accounts.append(bank.open_account(clients[1].client_id, "premium", 15_000, Currency.RUB, overdraft_limit=20_000, withdrawal_limit=80_000, fixed_commission=20))
    accounts.append(bank.open_account(clients[1].client_id, "base", 1_500, Currency.USD))
    accounts.append(bank.open_account(clients[2].client_id, "base", 70_000, Currency.RUB))
    accounts.append(bank.open_account(clients[2].client_id, "investment", 20_000, Currency.USD, portfolio={"stocks": 25_000, "bonds": 10_000, "etf": 15_000}))
    accounts.append(bank.open_account(clients[3].client_id, "base", 45_000, Currency.RUB))
    accounts.append(bank.open_account(clients[3].client_id, "savings", 60_000, Currency.EUR, min_balance=5_000, monthly_interest_rate="0.008"))
    accounts.append(bank.open_account(clients[4].client_id, "base", 30_000, Currency.RUB))
    accounts.append(bank.open_account(clients[5].client_id, "premium", 5_000, Currency.RUB, overdraft_limit=10_000, withdrawal_limit=30_000, fixed_commission=10))
    accounts.append(bank.open_account(clients[6].client_id, "base", 25_000, Currency.RUB))
    accounts.append(bank.open_account(clients[6].client_id, "base", 700, Currency.CNY))
    frozen_account = accounts[10]
    bank.freeze_account(frozen_account.account_id, "Day 6 frozen account sample")

    transactions = []

    for index in range(12):
        transactions.append(
            Transaction(
                "deposit",
                500 + index * 100,
                Currency.RUB,
                recipient_account_id=accounts[index % len(accounts)].account_id,
                priority=index % 3,
            )
        )

    for index in range(8):
        transactions.append(
            Transaction(
                "withdraw",
                300 + index * 150,
                Currency.RUB,
                sender_account_id=accounts[index % 10].account_id,
                priority=2,
            )
        )

    transfer_pairs = [
        (0, 4, 2_000),
        (4, 6, 1_500),
        (6, 8, 1_000),
        (8, 0, 1_200),
        (1, 4, 2_500),
        (2, 0, 3_000),
        (3, 5, 100),
        (5, 3, 120),
        (9, 8, 900),
        (0, 7, 700),
    ]
    for priority, (sender_index, recipient_index, amount) in enumerate(transfer_pairs, start=3):
        transactions.append(
            Transaction(
                "transfer",
                amount,
                accounts[sender_index].currency,
                sender_account_id=accounts[sender_index].account_id,
                recipient_account_id=accounts[recipient_index].account_id,
                is_external=sender_index in {3, 5},
                priority=priority,
            )
        )

    suspicious_specs = [
        (0, 8, 85_000),
        (1, 6, 95_000),
        (4, 9, 120_000),
        (6, 2, 80_000),
        (8, 0, 150_000),
    ]
    for sender_index, recipient_index, amount in suspicious_specs:
        transactions.append(
            Transaction(
                "transfer",
                amount,
                Currency.RUB,
                sender_account_id=accounts[sender_index].account_id,
                recipient_account_id=accounts[recipient_index].account_id,
                priority=8,
            )
        )

    error_specs = [
        (frozen_account.account_id, accounts[0].account_id, 500),
        (frozen_account.account_id, accounts[1].account_id, 700),
        (accounts[8].account_id, accounts[4].account_id, 500_000),
        (accounts[6].account_id, accounts[0].account_id, 400_000),
        (accounts[4].account_id, accounts[2].account_id, 300_000),
    ]
    for sender_id, recipient_id, amount in error_specs:
        transactions.append(
            Transaction(
                "transfer",
                amount,
                Currency.RUB,
                sender_account_id=sender_id,
                recipient_account_id=recipient_id,
                max_retries=1,
                priority=6,
            )
        )

    delayed_transactions = [
        Transaction(
            "deposit",
            1_500,
            Currency.RUB,
            recipient_account_id=accounts[0].account_id,
            scheduled_at=datetime.now() + timedelta(days=1),
            priority=10,
        ),
        Transaction(
            "withdraw",
            500,
            Currency.RUB,
            sender_account_id=accounts[4].account_id,
            scheduled_at=datetime.now() + timedelta(days=1),
            priority=9,
        ),
    ]
    transactions.extend(delayed_transactions)

    cancelable_transactions = [
        Transaction(
            "deposit",
            777,
            Currency.RUB,
            recipient_account_id=accounts[2].account_id,
            priority=7,
        ),
        Transaction(
            "withdraw",
            888,
            Currency.RUB,
            sender_account_id=accounts[0].account_id,
            priority=7,
        ),
        Transaction(
            "transfer",
            999,
            Currency.RUB,
            sender_account_id=accounts[0].account_id,
            recipient_account_id=accounts[2].account_id,
            priority=7,
        ),
    ]
    transactions.extend(cancelable_transactions)

    queue_log = []
    for transaction in transactions:
        queue.add(transaction)
        queue_log.append(
            {
                "transaction_id": transaction.transaction_id,
                "status": "queued",
                "priority": transaction.priority,
                "scheduled_at": transaction.scheduled_at.isoformat(),
            }
        )

    for transaction in cancelable_transactions[:2]:
        queue.cancel(transaction.transaction_id, reason="Canceled by demo scenario.")
        queue_log.append({"transaction_id": transaction.transaction_id, "status": "canceled"})

    processed_transactions = processor.process_queue(queue)
    history = list(transactions)
    suspicious_transaction_ids = {
        event["transaction_id"]
        for event in audit_log.get_suspicious_operations()
        if event["transaction_id"]
    }
    transaction_stats = {
        "total": len(history),
        "queued": len(history),
        "queue_events": len(queue_log),
        "processed_ready": len(processed_transactions),
        "completed": len([item for item in history if item.status == TransactionStatus.COMPLETED]),
        "failed": len([item for item in history if item.status == TransactionStatus.FAILED]),
        "canceled": len([item for item in history if item.status == TransactionStatus.CANCELED]),
        "pending_delayed": queue.pending_count(),
        "suspicious": len(suspicious_transaction_ids),
        "errors": len(processor.error_log),
    }

    selected_client = clients[0]
    selected_client_accounts = [
        bank.accounts[account_id]
        for account_id in selected_client.account_ids
    ]
    selected_account_ids = set(selected_client.account_ids)
    selected_client_history = [
        transaction.to_dict()
        for transaction in history
        if transaction.sender_account_id in selected_account_ids
        or transaction.recipient_account_id in selected_account_ids
    ]

    print("Day 6. Full banking system demo:")
    print(f"Bank: {bank.name}")
    print(f"Clients: {len(clients)}")
    print(f"Accounts: {len(accounts)}")
    print(f"Transactions created: {len(transactions)}")
    print("Queue log sample:")
    print(queue_log[:8])
    print("Execution log:")
    print([transaction.to_dict() for transaction in processed_transactions[:10]])
    print("Rejected transactions:")
    print([transaction.to_dict() for transaction in history if transaction.status == TransactionStatus.FAILED])
    print("Selected client accounts:")
    print(selected_client.get_client_info())
    for account in selected_client_accounts:
        show_account(account)
    print("Selected client transaction history:")
    print(selected_client_history[:10])
    print("Suspicious operations:")
    print(audit_log.get_suspicious_operations()[:10])
    print("Reports:")
    print("Top 3 clients:", bank.get_clients_ranking()[:3])
    print("Transaction stats:", transaction_stats)
    print("Total balance:", bank.get_total_balance())
    print("Error statistics:", audit_log.get_error_statistics())
    print("-" * 80)

    return {
        "bank": bank,
        "clients": clients,
        "accounts": accounts,
        "transactions": history,
        "queue": queue,
        "queue_log": queue_log,
        "processor": processor,
        "audit_log": audit_log,
        "risk_analyzer": risk_analyzer,
        "transaction_stats": transaction_stats,
        "selected_client_history": selected_client_history,
    }

def main() -> None:
    """Run demonstration scenarios for implemented project days."""
    run_day_1_demo()
    run_day_2_demo()
    run_day_3_demo()
    run_day_4_demo()
    run_day_5_demo()
    run_day_6_demo()


if __name__ == "__main__":
    main()
