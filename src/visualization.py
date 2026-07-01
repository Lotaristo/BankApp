import os
from decimal import Decimal
from pathlib import Path


RUB_EXCHANGE_RATES = {
    "RUB": Decimal("1"),
    "USD": Decimal("90"),
    "EUR": Decimal("100"),
    "KZT": Decimal("0.2"),
    "CNY": Decimal("12"),
}


def save_report_charts(
    bank,
    transactions: list,
    transaction_statistics: dict,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Save report charts and return generated file paths."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    matplotlib_config_dir = target_dir / ".matplotlib-cache"
    matplotlib_config_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_config_dir))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_paths = {
        "balance_by_currency": target_dir / "balance_by_currency_pie.png",
        "transaction_statuses": target_dir / "transaction_statuses_bar.png",
        "balance_movement": target_dir / "balance_movement_line.png",
    }

    _save_balance_by_currency_pie(plt, bank, chart_paths["balance_by_currency"])
    _save_transaction_status_bar(
        plt,
        transaction_statistics,
        chart_paths["transaction_statuses"],
    )
    _save_balance_movement_line(plt, transactions, chart_paths["balance_movement"])
    return chart_paths


def _save_balance_by_currency_pie(plt, bank, file_path: Path) -> None:
    """Save a pie chart with total balances by currency."""
    balances = bank.get_total_balance()
    labels = list(balances) or ["empty"]
    values = [float(Decimal(value)) for value in balances.values()] or [1.0]

    figure, axis = plt.subplots(figsize=(7, 5))
    axis.pie(values, labels=labels, autopct="%1.1f%%")
    axis.set_title("Bank Balance by Currency")
    figure.tight_layout()
    figure.savefig(file_path)
    plt.close(figure)


def _save_transaction_status_bar(
    plt,
    transaction_statistics: dict,
    file_path: Path,
) -> None:
    """Save a bar chart with transaction statuses."""
    status_counts = transaction_statistics["by_status"]
    labels = list(status_counts) or ["empty"]
    values = list(status_counts.values()) or [0]

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(labels, values, color="#2f6f73")
    axis.set_title("Transactions by Status")
    axis.set_xlabel("Status")
    axis.set_ylabel("Count")
    figure.tight_layout()
    figure.savefig(file_path)
    plt.close(figure)


def _save_balance_movement_line(plt, transactions: list, file_path: Path) -> None:
    """Save a line chart with cumulative completed transaction movement."""
    completed_transactions = [
        transaction
        for transaction in transactions
        if transaction.status.value == "completed"
    ]
    completed_transactions.sort(
        key=lambda transaction: transaction.processed_at or transaction.updated_at
    )
    cumulative_values = []
    current_value = Decimal("0")

    for transaction in completed_transactions:
        current_value += _get_signed_transaction_value(transaction)
        cumulative_values.append(float(current_value))

    if not cumulative_values:
        cumulative_values = [0.0]

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.plot(range(1, len(cumulative_values) + 1), cumulative_values, marker="o")
    axis.set_title("Completed Transaction Balance Movement")
    axis.set_xlabel("Completed transaction number")
    axis.set_ylabel("Net movement, RUB equivalent")
    figure.tight_layout()
    figure.savefig(file_path)
    plt.close(figure)


def _get_signed_transaction_value(transaction) -> Decimal:
    """Return signed transaction value converted to RUB equivalent."""
    value = transaction.amount * RUB_EXCHANGE_RATES[transaction.currency.value]

    if transaction.transaction_type.value == "withdraw":
        return -value

    if transaction.transaction_type.value == "transfer":
        return -transaction.commission * RUB_EXCHANGE_RATES[transaction.currency.value]

    return value
