import sys
import json
import datetime
import random
import requests

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QCalendarWidget
)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPainter, QPen, QColor


# ============================================================
# Matrix effect widget
# ============================================================
class MatrixBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.running = True
        self.timer.start(50)

        self.chars = [chr(i) for i in range(33, 127)]
        self.columns = []
        self.init_columns()

    def init_columns(self):
        width = self.width() or 400
        font_size = 12
        self.columns = [random.randint(0, 20) for _ in range(width // font_size)]
        self.font_size = font_size

    def resizeEvent(self, event):
        self.init_columns()
        super().resizeEvent(event)

    def paintEvent(self, event):
        if not self.running:
            return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 200))  # semi-transparent
        painter.setFont(QFont('Consolas', self.font_size))
        painter.setPen(QColor(0, 255, 0))

        for i, col in enumerate(self.columns):
            char = random.choice(self.chars)
            x = i * self.font_size
            y = col * self.font_size
            painter.drawText(QPoint(x, y), char)
            if col * self.font_size > self.height() and random.random() > 0.975:
                self.columns[i] = 0
            else:
                self.columns[i] += 1

    def toggle(self):
        self.running = not self.running
        self.update()


# ============================================================
# Analog Clock Widget
# ============================================================
class AnalogClock(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 300.0, side / 300.0)

        # Face
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#222"))
        painter.drawEllipse(-140, -140, 280, 280)

        # Hour / minute marks
        painter.setPen(QPen(QColor("white"), 3))
        for i in range(12):
            painter.drawLine(0, -120, 0, -135)
            painter.rotate(30)

        # Hands
        now = datetime.datetime.now()

        # Hour hand
        painter.save()
        painter.rotate(30 * ((now.hour % 12) + now.minute / 60))
        painter.setPen(QPen(QColor("#00aaff"), 6))
        painter.drawLine(0, 0, 0, -70)
        painter.restore()

        # Minute hand
        painter.save()
        painter.rotate(6 * (now.minute + now.second / 60))
        painter.setPen(QPen(QColor("white"), 4))
        painter.drawLine(0, 0, 0, -100)
        painter.restore()

        # Second hand
        painter.save()
        painter.rotate(6 * now.second)
        painter.setPen(QPen(QColor("red"), 2))
        painter.drawLine(0, 10, 0, -120)
        painter.restore()


# ============================================================
# Main Dashboard
# ============================================================
class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Dashboard")
        self.setStyleSheet(self.dark_mode())

        # Weather data
        self.api_key, self.location = self.load_weather_key()

        # Stack
        self.stack = QStackedWidget()

        self.main_screen = self.build_main_screen()
        self.weather_screen = self.build_weather_screen()
        self.calendar_screen = self.build_calendar_screen()

        self.stack.addWidget(self.main_screen)
        self.stack.addWidget(self.weather_screen)
        self.stack.addWidget(self.calendar_screen)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        # Update systems
        self.update_clock()
        self.update_weather()
        self.start_timers()

    # ------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------
    def dark_mode(self):
        return """
            QWidget {
                background-color: #111;
                color: white;
                font-family: Segoe UI;
            }
            QPushButton {
                background-color: #222;
                border: 1px solid #444;
                padding: 10px;
                border-radius: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #333;
            }
        """

    # ------------------------------------------------------------
    # Load Weather API Key
    # ------------------------------------------------------------
    def load_weather_key(self):
        try:
            with open("Wapi.json", "r") as f:
                data = json.load(f)
                return data["api_key"], data["location"]
        except:
            return None, None

    # ------------------------------------------------------------
    # Main Screen
    # ------------------------------------------------------------
    def build_main_screen(self):
        screen = QWidget()
        layout = QVBoxLayout()

        # Matrix background
        self.matrix_bg = MatrixBackground(screen)
        self.matrix_bg.setGeometry(screen.rect())
        self.matrix_bg.lower()  # behind everything

        # Top-left Matrix toggle button
        self.matrix_btn = QPushButton("Matrix ON", screen)
        self.matrix_btn.setCheckable(True)
        self.matrix_btn.move(10, 10)
        self.matrix_btn.clicked.connect(self.toggle_matrix)
        self.matrix_btn.setStyleSheet("""
            QPushButton {
                background-color: #222;
                color: white;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:checked {
                background-color: #00aa00;
            }
        """)
        self.matrix_btn.raise_()

        # Top temperature button
        self.temp_btn = QPushButton("Loading…")
        self.temp_btn.clicked.connect(self.show_weather)
        self.temp_btn.setFixedWidth(150)

        # Analog clock
        self.clock_widget = AnalogClock()

        # Date button
        self.date_btn = QPushButton("00/00/0000")
        self.date_btn.setFixedWidth(150)
        self.date_btn.clicked.connect(self.show_calendar)

        # Voice placeholder
        self.voice_label = QLabel("Voice Assistant\n(Coming Soon)")
        self.voice_label.setAlignment(Qt.AlignCenter)

        # Layout areas
        top = QHBoxLayout()
        top.addStretch()
        top.addWidget(self.temp_btn)

        bottom = QHBoxLayout()
        bottom.addWidget(self.date_btn)
        bottom.addStretch()
        bottom.addWidget(self.voice_label)

        layout.addLayout(top)
        layout.addStretch()
        layout.addWidget(self.clock_widget, alignment=Qt.AlignCenter)
        layout.addStretch()
        layout.addLayout(bottom)

        screen.setLayout(layout)
        return screen

    # ------------------------------------------------------------
    # Weather screen
    # ------------------------------------------------------------
    def build_weather_screen(self):
        screen = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Weather Details")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)

        self.weather_info = QLabel("Loading…")
        self.weather_info.setAlignment(Qt.AlignCenter)

        back = QPushButton("Back")
        back.clicked.connect(self.show_main)

        layout.addWidget(title)
        layout.addWidget(self.weather_info)
        layout.addWidget(back, alignment=Qt.AlignCenter)

        screen.setLayout(layout)
        return screen

    # ------------------------------------------------------------
    # Calendar screen
    # ------------------------------------------------------------
    def build_calendar_screen(self):
        screen = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Calendar")
        title.setFont(QFont("Arial", 24))
        title.setAlignment(Qt.AlignCenter)

        self.calendar = QCalendarWidget()
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { background-color: #002244; color: white; }
            QCalendarWidget QAbstractItemView:enabled { background-color: #001122; color: white; }
            QCalendarWidget QToolButton { background-color: #003366; color: white; }
        """)

        back = QPushButton("Back")
        back.clicked.connect(self.show_main)

        layout.addWidget(title)
        layout.addWidget(self.calendar)
        layout.addWidget(back, alignment=Qt.AlignCenter)

        screen.setLayout(layout)
        return screen

    # ------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------
    def show_main(self):
        self.stack.setCurrentIndex(0)

    def show_weather(self):
        self.stack.setCurrentIndex(1)

    def show_calendar(self):
        self.stack.setCurrentIndex(2)

    # ------------------------------------------------------------
    # Update clock + date
    # ------------------------------------------------------------
    def update_clock(self):
        now = datetime.datetime.now()
        self.date_btn.setText(now.strftime("%m/%d/%Y"))

    # ------------------------------------------------------------
    # Weather fetch
    # ------------------------------------------------------------
    def update_weather(self):
        if not self.api_key:
            self.temp_btn.setText("No API")
            return

        try:
            url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={self.location}"
            r = requests.get(url).json()

            temp_f = r["current"]["temp_f"]
            condition = r["current"]["condition"]["text"]

            self.temp_btn.setText(f"{temp_f}°F")
            self.weather_info.setText(
                f"Temperature: {temp_f}°F\nCondition: {condition}"
            )

        except Exception as e:
            self.temp_btn.setText("Err")
            self.weather_info.setText("Weather load error")

    # ------------------------------------------------------------
    # Timers
    # ------------------------------------------------------------
    def start_timers(self):
        # Clock
        clock_timer = QTimer()
        clock_timer.timeout.connect(self.update_clock)
        clock_timer.start(1000)
        self.clock_timer = clock_timer

        # Weather refresh (every 10 minutes)
        weather_timer = QTimer()
        weather_timer.timeout.connect(self.update_weather)
        weather_timer.start(600000)
        self.weather_timer = weather_timer

    # ------------------------------------------------------------
    # Matrix toggle
    # ------------------------------------------------------------
    def toggle_matrix(self):
        self.matrix_bg.toggle()
        if self.matrix_bg.running:
            self.matrix_btn.setText("Matrix ON")
        else:
            self.matrix_btn.setText("Matrix OFF")

    # ------------------------------------------------------------
    # Resize matrix on window resize
    # ------------------------------------------------------------
    def resizeEvent(self, event):
        self.matrix_bg.setGeometry(self.main_screen.rect())
        super().resizeEvent(event)


# ============================================================
# Run App
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.showFullScreen()
    sys.exit(app.exec_())
