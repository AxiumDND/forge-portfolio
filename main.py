import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class ForgePortfolioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forge Portfolio Tracker")
        self.setMinimumSize(1024, 640)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        label = QLabel("Forge Portfolio Tracker — Loading...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; color: #ccc;")
        layout.addWidget(label)

        self.setStyleSheet("background-color: #1e1e2e;")


def main():
    app = QApplication(sys.argv)
    window = ForgePortfolioWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
