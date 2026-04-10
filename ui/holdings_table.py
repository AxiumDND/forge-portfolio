from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView


COLUMNS = [
    "Ticker",
    "Name",
    "Type",
    "Qty",
    "Avg Buy (GBP)",
    "Current (GBP)",
    "P&L (%)",
    "Signal",
]


class HoldingsTable(QTableWidget):
    """Table widget that displays portfolio holdings with live data."""

    def __init__(self, parent=None):
        super().__init__(0, len(COLUMNS), parent)
        self.setHorizontalHeaderLabels(COLUMNS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)

    def load_holdings(self, holdings: list[dict]) -> None:
        """Populate the table from a list of holding dicts."""
        self.setRowCount(len(holdings))
        for row, holding in enumerate(holdings):
            self.setItem(row, 0, QTableWidgetItem(holding.get("ticker", "")))
            self.setItem(row, 1, QTableWidgetItem(holding.get("name", "")))
            self.setItem(row, 2, QTableWidgetItem(holding.get("type", "")))
            self.setItem(row, 3, QTableWidgetItem(str(holding.get("quantity", 0))))
            self.setItem(row, 4, QTableWidgetItem("--"))
            self.setItem(row, 5, QTableWidgetItem("--"))
            self.setItem(row, 6, QTableWidgetItem("--"))
            self.setItem(row, 7, QTableWidgetItem("--"))
