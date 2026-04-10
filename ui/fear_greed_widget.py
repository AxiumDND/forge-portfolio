"""Fear & Greed Index gauge widget."""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPen, QFont, QPolygonF


# Score ranges and their Catppuccin colours
RANGES = [
    (0, 24, "Extreme Fear", "#f38ba8"),
    (25, 44, "Fear", "#fab387"),
    (45, 55, "Neutral", "#f9e2af"),
    (56, 74, "Greed", "#a6e3a1"),
    (75, 100, "Extreme Greed", "#94e2d5"),
]

# Gradient stops for the bar (red → orange → yellow → green → teal)
GRADIENT_STOPS = [
    (0.0, "#f38ba8"),
    (0.25, "#fab387"),
    (0.5, "#f9e2af"),
    (0.75, "#a6e3a1"),
    (1.0, "#94e2d5"),
]


def _colour_for_score(score):
    """Return the Catppuccin colour for a given F&G score."""
    if score is None:
        return "#a6adc8"
    for lo, hi, _, colour in RANGES:
        if lo <= score <= hi:
            return colour
    return "#a6adc8"


def _label_for_score(score):
    """Return the label for a given F&G score."""
    if score is None:
        return "Unavailable"
    for lo, hi, label, _ in RANGES:
        if lo <= score <= hi:
            return label
    return "Unknown"


class GradientBar(QWidget):
    """Custom-painted gradient bar with a position marker."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.score = None
        self.setFixedHeight(14)
        self.setMinimumWidth(180)

    def set_score(self, score):
        self.score = score
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bar_h = 8
        bar_y = 0

        # Draw gradient bar
        gradient = QLinearGradient(0, 0, w, 0)
        for stop, colour in GRADIENT_STOPS:
            gradient.setColorAt(stop, QColor(colour))

        painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawRoundedRect(QRectF(0, bar_y, w, bar_h), 4, 4)

        # Draw position marker (triangle below the bar)
        if self.score is not None:
            x = (self.score / 100.0) * w
            x = max(4, min(x, w - 4))
            colour = QColor(_colour_for_score(self.score))

            painter.setPen(Qt.NoPen)
            painter.setBrush(colour)
            triangle = QPolygonF()
            triangle.append(QRectF(x - 4, bar_y + bar_h + 1, 0, 0).topLeft())
            triangle.append(QRectF(x + 4, bar_y + bar_h + 1, 0, 0).topLeft())
            triangle.append(QRectF(x, bar_y + bar_h + 5, 0, 0).topLeft())
            painter.drawPolygon(triangle)

        painter.end()


class FearGreedWidget(QWidget):
    """Compact Fear & Greed Index gauge for the header area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(2)

        # Title
        title = QLabel("Fear & Greed")
        title.setStyleSheet("font-size: 14px; color: #a6adc8; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Score + rating row
        score_row = QHBoxLayout()
        score_row.setSpacing(8)

        self.score_label = QLabel("--")
        self.score_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #a6adc8;")
        self.score_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        score_row.addWidget(self.score_label)

        self.rating_label = QLabel("Loading...")
        self.rating_label.setStyleSheet("font-size: 15px; color: #a6adc8;")
        self.rating_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        score_row.addWidget(self.rating_label)

        layout.addLayout(score_row)

        # Gradient bar
        self.bar = GradientBar()
        layout.addWidget(self.bar)

    def set_data(self, score, rating):
        """Update the widget with new Fear & Greed data."""
        colour = _colour_for_score(score)

        if score is not None:
            self.score_label.setText(str(int(score)))
            self.score_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {colour};")
        else:
            self.score_label.setText("--")
            self.score_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #a6adc8;")

        display_rating = _label_for_score(score) if score is not None else rating
        self.rating_label.setText(display_rating.upper())
        self.rating_label.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {colour};")

        self.bar.set_score(score)
