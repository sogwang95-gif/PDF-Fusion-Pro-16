import sys
import os
import ctypes
import hashlib
import hmac
import json
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QFrame, QSizePolicy, QLineEdit, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QEventLoop
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPainter, QPen, QKeySequence

PURCHASE_URL = "https://selar.com/67f7118528"
APP_NAME = "PDF Fusion Pro"
LICENSE_SECRET = b"pdf-fusion-pro-v26-local-license-secret-change-before-release"
VALID_SERIAL_HASH = "f4aded10b5c25197985e363bcefe757b18d8cfae7aafdd6936f81ef746eb9b11"
LICENSE_DAYS = 30
TRIAL_DAYS = 7
APP_USER_MODEL_ID = "KayXam.PDFFusionPro.26"


def app_icon_path():
    """Return the bundled icon path for source and PyInstaller builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, "app.ico")


def set_windows_app_id():
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


class LicenseManager:
    """Secure local licensing with anti-tampering protections and trial tracking."""

    @classmethod
    def license_path(cls):
        if getattr(sys, "frozen", False):
            app_dir = Path(sys.executable).resolve().parent
        else:
            app_dir = Path(__file__).resolve().parent
        return app_dir / "pdf_fusion_license.json"

    @classmethod
    def trial_path(cls):
        if getattr(sys, "frozen", False):
            app_dir = Path(sys.executable).resolve().parent
        else:
            app_dir = Path(__file__).resolve().parent
        return app_dir / "pdf_fusion_trial.json"

    @classmethod
    def machine_fingerprint(cls):
        """Generate stable machine fingerprint from platform identifiers."""
        import platform
        import uuid
        
        components = [
            platform.node(),
            platform.machine(),
            str(uuid.getnode()),
        ]
        fingerprint = "|".join(components)
        return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()

    @classmethod
    def normalize_key(cls, serial_key):
        return "".join(ch for ch in serial_key.upper() if ch.isalnum())

    @classmethod
    def serial_hash(cls, serial_key):
        return hashlib.sha256(cls.normalize_key(serial_key).encode("utf-8")).hexdigest()

    @classmethod
    def _license_signature(cls, serial_hash, activated_at, expires_at, machine_hash, last_checked_at):
        payload = f"{serial_hash}:{activated_at}:{expires_at}:{machine_hash}:{last_checked_at}"
        return hmac.new(LICENSE_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def _trial_signature(cls, machine_hash, trial_start):
        payload = f"{machine_hash}:{trial_start}"
        return hmac.new(LICENSE_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def validate_key(cls, serial_key):
        return hmac.compare_digest(cls.serial_hash(serial_key), VALID_SERIAL_HASH)

    @classmethod
    def _init_trial(cls):
        """Initialize trial tracking for this machine."""
        trial_path = cls.trial_path()
        if trial_path.exists():
            return
        
        machine_hash = cls.machine_fingerprint()
        now = datetime.now()
        data = {
            "machine_hash": machine_hash,
            "trial_start": now.isoformat(timespec="seconds"),
            "signature": cls._trial_signature(machine_hash, now.isoformat(timespec="seconds")),
        }
        try:
            trial_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

    @classmethod
    def is_trial_valid(cls):
        """Check if trial is still valid and not expired."""
        trial_path = cls.trial_path()
        if not trial_path.exists():
            cls._init_trial()
            return True
        
        try:
            data = json.loads(trial_path.read_text(encoding="utf-8"))
            machine_hash = data.get("machine_hash", "")
            trial_start = data.get("trial_start", "")
            signature = data.get("signature", "")
        except (OSError, json.JSONDecodeError):
            return False
        
        current_machine_hash = cls.machine_fingerprint()
        if not hmac.compare_digest(machine_hash, current_machine_hash):
            return False
        
        expected_sig = cls._trial_signature(machine_hash, trial_start)
        if not hmac.compare_digest(signature, expected_sig):
            return False
        
        try:
            start_time = datetime.fromisoformat(trial_start)
            expiry_time = start_time + timedelta(days=TRIAL_DAYS)
            return datetime.now() < expiry_time
        except ValueError:
            return False

    @classmethod
    def is_activated(cls):
        path = cls.license_path()
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            serial_hash = data.get("serial_hash", "")
            activated_at = data.get("activated_at", "")
            expires_at = data.get("expires_at", "")
            last_checked_at = data.get("last_checked_at", "")
            machine_hash = data.get("machine_hash", "")
            signature = data.get("signature", "")
        except (OSError, json.JSONDecodeError):
            return False

        if not hmac.compare_digest(serial_hash, VALID_SERIAL_HASH):
            return False

        current_machine_hash = cls.machine_fingerprint()
        if not hmac.compare_digest(machine_hash, current_machine_hash):
            return False

        try:
            last_check = datetime.fromisoformat(last_checked_at)
            now = datetime.now()
            if now < last_check:
                return False
        except (ValueError, TypeError):
            return False

        expected_signature = cls._license_signature(
            serial_hash, activated_at, expires_at, machine_hash, last_checked_at
        )
        if not hmac.compare_digest(signature, expected_signature):
            return False

        try:
            expiry = datetime.fromisoformat(expires_at)
        except ValueError:
            return False

        if datetime.now() >= expiry:
            try:
                path.unlink()
            except OSError:
                pass
            return False

        now = datetime.now()
        updated_data = data.copy()
        updated_data["last_checked_at"] = now.isoformat(timespec="seconds")
        updated_data["signature"] = cls._license_signature(
            serial_hash, activated_at, expires_at, machine_hash, updated_data["last_checked_at"]
        )
        try:
            path.write_text(json.dumps(updated_data, indent=2), encoding="utf-8")
        except OSError:
            pass

        return True

    @classmethod
    def activate(cls, serial_key):
        if not cls.validate_key(serial_key):
            return False

        path = cls.license_path()
        activated_at = datetime.now()
        expires_at = activated_at + timedelta(days=LICENSE_DAYS)
        machine_hash = cls.machine_fingerprint()
        
        data = {
            "app": APP_NAME,
            "serial_hash": cls.serial_hash(serial_key),
            "activated_at": activated_at.isoformat(timespec="seconds"),
            "expires_at": expires_at.isoformat(timespec="seconds"),
            "last_checked_at": activated_at.isoformat(timespec="seconds"),
            "machine_hash": machine_hash,
        }
        data["signature"] = cls._license_signature(
            data["serial_hash"],
            data["activated_at"],
            data["expires_at"],
            data["machine_hash"],
            data["last_checked_at"],
        )
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True


class GradientWidget(QWidget):
    """Widget with gradient background"""
    def __init__(self, parent=None, border_color=None, border_width=0):
        super().__init__(parent)
        self.start_color = QColor(45, 50, 80)
        self.end_color = QColor(30, 35, 60)
        self.border_color = border_color or QColor(74, 79, 127, 200)  # Semi-transparent blue
        self.border_width = border_width
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw border if specified
        if self.border_width > 0:
            border_rect = self.rect().adjusted(self.border_width//2, self.border_width//2, 
                                             -self.border_width//2, -self.border_width//2)
            painter.setPen(QPen(self.border_color, self.border_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawRoundedRect(border_rect, 12, 12)
        
        # Draw gradient background
        gradient_rect = self.rect().adjusted(self.border_width, self.border_width, 
                                           -self.border_width, -self.border_width)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.start_color)
        gradient.setColorAt(1, self.end_color)
        painter.fillRect(gradient_rect, gradient)


class ThemedDialog(QWidget):
    """Compact light dialog that stands apart from the dark main window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        
        background = GradientWidget(self, border_width=0)
        background.start_color = QColor(255, 255, 255)
        background.end_color = QColor(248, 250, 255)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 110))
        background.setGraphicsEffect(shadow)

        layout = QVBoxLayout(background)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(background)
        
        self.content_layout = layout
        self.background = background
        self.result = None
        
        # Apply theme styles
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #20243A;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QLabel {
                color: #20243A;
            }
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 12px;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """)
    
    def accept(self):
        self.result = True
        self.close()
    
    def reject(self):
        self.result = False
        self.close()
    
    def exec_(self):
        self.show()
        self.raise_()
        self.activateWindow()
        
        # Wait for dialog to close
        loop = QEventLoop()
        self.finished = loop.quit
        self.closeEvent = lambda event: loop.quit()
        loop.exec_()
        
        return self.result


def dialog_button_style(secondary=False):
    if secondary:
        return """
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 12px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QPushButton:pressed {
                background-color: #D1D5DB;
            }
        """

    return """
        QPushButton {
            background-color: #2563EB;
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 600;
            font-size: 12px;
            text-align: center;
        }
        QPushButton:hover {
            background-color: #1D4ED8;
        }
        QPushButton:pressed {
            background-color: #1E40AF;
        }
    """


def show_themed_message(parent, title, message, icon_type="info", buttons=None):
    """Show a themed message dialog"""
    dialog = ThemedDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFixedSize(300, 155)
    
    # Title
    title_label = QLabel(title)
    title_label.setStyleSheet("""
        QLabel {
            color: #111827;
            font-size: 15px;
            font-weight: 700;
            padding-bottom: 2px;
        }
    """)
    dialog.content_layout.addWidget(title_label)
    
    # Icon
    icon_label = QLabel()
    if icon_type == "warning":
        icon_label.setText("⚠️")
    elif icon_type == "error":
        icon_label.setText("❌")
    elif icon_type == "success":
        icon_label.setText("✅")
    else:
        icon_label.setText("ℹ️")
    icon_label.setStyleSheet("font-size: 24px; padding-bottom: 10px;")
    dialog.content_layout.addWidget(icon_label)
    icon_label.hide()
    
    # Message
    message_label = QLabel(message)
    message_label.setStyleSheet("""
        QLabel {
            color: #4B5563;
            font-size: 12px;
        }
    """)
    message_label.setWordWrap(True)
    dialog.content_layout.addWidget(message_label, 1)
    
    # Buttons
    if buttons is None:
        buttons = ["OK"]
    
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    
    for btn_text in buttons:
        btn = ModernButton(btn_text)
        btn.setMinimumHeight(30)
        btn.setStyleSheet(dialog_button_style(btn_text in ["Cancel", "No", "Exit"]))
        button_layout.addWidget(btn)
        if btn_text == "OK" or btn_text == "Yes":
            btn.clicked.connect(dialog.accept)
        elif btn_text == "Cancel" or btn_text == "No":
            btn.clicked.connect(dialog.reject)
    
    dialog.content_layout.addLayout(button_layout)
    
    # Center on parent
    if parent:
        dialog.move(parent.frameGeometry().center() - dialog.rect().center())
    
    return dialog.exec_()


class SerialKeyBox(QLineEdit):
    def __init__(self, serial_input, index):
        super().__init__()
        self.serial_input = serial_input
        self.index = index
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignCenter)
        self.setEchoMode(QLineEdit.Password)
        self.setFixedSize(24, 24)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #F3F4F6;
                color: #111827;
                border: 2px solid #888888;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 700;
            }
            QLineEdit:focus {
                background-color: #EAF1FF;
                border-color: #555555;
            }
        """)
        self.textEdited.connect(self._move_after_entry)

    def _move_after_entry(self, text):
        if text and self.index < len(self.serial_input.boxes) - 1:
            self.serial_input.boxes[self.index + 1].setFocus()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Paste):
            self.serial_input.paste_from(self.index)
            return

        if event.key() == Qt.Key_Backspace and not self.text() and self.index > 0:
            previous_box = self.serial_input.boxes[self.index - 1]
            previous_box.clear()
            previous_box.setFocus()
            return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.serial_input.submit()
            return

        super().keyPressEvent(event)


class SerialKeyInput(QWidget):
    SERIAL_LENGTH = 12
    GROUP_SIZE = 4

    def __init__(self, submit_callback=None, parent=None):
        super().__init__(parent)
        self.submit_callback = submit_callback
        self.boxes = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for group_index in range(self.SERIAL_LENGTH // self.GROUP_SIZE):
            group = QWidget()
            group_layout = QHBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(6)

            for _ in range(self.GROUP_SIZE):
                box = SerialKeyBox(self, len(self.boxes))
                self.boxes.append(box)
                group_layout.addWidget(box)

            layout.addWidget(group)

            if group_index < (self.SERIAL_LENGTH // self.GROUP_SIZE) - 1:
                dash = QLabel("-")
                dash.setFixedWidth(3)
                dash.setStyleSheet("QLabel { color: #B0B0B0; font-size: 18px; font-weight: 700; }")
                dash.setAlignment(Qt.AlignCenter)
                layout.addWidget(dash)

    def paste_from(self, start_index=0):
        clipboard_text = QApplication.clipboard().text()
        characters = [ch for ch in clipboard_text.upper() if ch.isalnum()]
        if not characters:
            return

        for offset, character in enumerate(characters):
            index = start_index + offset
            if index >= len(self.boxes):
                break
            self.boxes[index].setText(character)

        next_index = min(start_index + len(characters), len(self.boxes) - 1)
        self.boxes[next_index].setFocus()

    def value(self):
        return "".join(box.text() for box in self.boxes)

    def clear_and_focus(self):
        for box in self.boxes:
            box.clear()
        self.boxes[0].setFocus()

    def submit(self):
        if self.submit_callback:
            self.submit_callback()


class ActivationDialog(ThemedDialog):
    """Serial-key activation dialog shown before the main app opens."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Subscription Required")
        self.setFixedSize(620, 285)
        self.activated = False

        title = QLabel("Subscription Required")
        title.setStyleSheet("""
            QLabel {
                color: #111827;
                font-size: 17px;
                font-weight: 700;
                padding-bottom: 2px;
            }
        """)
        self.content_layout.addWidget(title)

        message = QLabel(
            "You ran out of free usage. Please activate the app, "
            "or purchase a license to continue merging PDFs."
        )
        message.setWordWrap(True)
        message.setStyleSheet("""
            QLabel {
                color: #4B5563;
                font-size: 12px;
                padding-bottom: 6px;
            }
        """)
        self.content_layout.addWidget(message)

        self.key_input = SerialKeyInput(self.try_activate)
        self.content_layout.addWidget(self.key_input)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #D97706; font-size: 12px; padding-top: 2px;")
        self.content_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.purchase_btn = ModernButton("Purchase Licence")
        self.activate_btn = ModernButton("Activate")
        self.exit_btn = ModernButton("Exit")
        self.purchase_btn.setMinimumHeight(30)
        self.activate_btn.setMinimumHeight(30)
        self.exit_btn.setMinimumHeight(30)
        self.purchase_btn.setStyleSheet(dialog_button_style())
        self.activate_btn.setStyleSheet(dialog_button_style())
        self.exit_btn.setStyleSheet(dialog_button_style(True))

        self.purchase_btn.clicked.connect(self.open_purchase_page)
        self.activate_btn.clicked.connect(self.try_activate)
        self.exit_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.purchase_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.exit_btn)
        button_layout.addWidget(self.activate_btn)
        self.content_layout.addLayout(button_layout)
        QTimer.singleShot(0, self.key_input.clear_and_focus)

    def open_purchase_page(self):
        webbrowser.open(PURCHASE_URL)

    def try_activate(self):
        serial_key = self.key_input.value()
        if not serial_key:
            self.status_label.setText("Please enter your serial key.")
            return

        if LicenseManager.activate(serial_key):
            self.activated = True
            self.status_label.setStyleSheet("color: #15803D; font-size: 12px; padding-top: 2px;")
            self.status_label.setText("Activation successful. Continuing...")
            QTimer.singleShot(500, self.accept)
            return

        self.status_label.setStyleSheet("color: #DC2626; font-size: 12px; padding-top: 2px;")
        self.status_label.setText("That serial key is not valid. Please check it and try again.")
        self.key_input.clear_and_focus()

    def exec_(self):
        result = super().exec_()
        return bool(result and self.activated)


class ModernButton(QPushButton):
    """Modern styled button with hover effects"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.default_style = """
            QPushButton {
                background-color: #2A2F4F;
                color: #FFFFFF;
                border: 2px solid #4A4F7F;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #4A4F7F;
                border-color: #6A6F9F;
            }
            QPushButton:pressed {
                background-color: #1A1F3F;
                border-color: #4A4F7F;
            }
        """
        self.setStyleSheet(self.default_style)


class PDFMergerApp(QWidget):
    def __init__(self):
        super().__init__()

        # -------- BASIC WINDOW SETUP (FAST) --------
        self.setWindowTitle("PDF Fusion Pro- v26.1.0")
        self.setFixedSize(1000, 600)

        icon_path = app_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.pdf_files = []
        
        # Initialize trial tracking
        LicenseManager.is_trial_valid()

        # Show window ASAP
        self.show()

        # Build UI AFTER window is visible
        QTimer.singleShot(0, self.init_ui)

    # ---------- UI ----------
    def init_ui(self):
        # Set main window style
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

        # Create gradient background
        background = GradientWidget(self)
        background_layout = QVBoxLayout(background)
        background_layout.setContentsMargins(20, 20, 20, 20)
        background_layout.setSpacing(15)

        # ---------- HEADER ----------
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2A2F4F, stop:1 #1A1F3F);
                border-radius: 12px;
                padding: 5px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setSpacing(5)
        
        # Left side: Title and subtitle
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title = QLabel("PDF Fusion Pro")
        title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: 700;
                padding-bottom: 5px;
            }
        """)
        
        subtitle = QLabel("Built with love for Professionals")
        subtitle.setStyleSheet("""
            QLabel {
                color: #B0B0D0;
                font-size: 16px;
                font-weight: 400;
                font-style: italic;
            }
        """)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addWidget(title_widget)
        
        # Right side: Status badge
        header_layout.addStretch()
        
        self.status_badge = QLabel()
        if LicenseManager.is_activated():
            self.status_badge.setText("Activated")
            self.status_badge.setStyleSheet("""
                QLabel {
                    color: #4CAF50;
                    font-size: 14px;
                    font-weight: 700;
                    padding: 8px 16px;
                    background-color: rgba(76, 175, 80, 20);
                    border: 1px solid rgba(76, 175, 80, 100);
                    border-radius: 6px;
                }
            """)
        else:
            self.status_badge.setText("Free Trial")
            self.status_badge.setStyleSheet("""
                QLabel {
                    color: #FFB74D;
                    font-size: 14px;
                    font-weight: 700;
                    padding: 8px 16px;
                    background-color: rgba(255, 183, 77, 20);
                    border: 1px solid rgba(255, 183, 77, 100);
                    border-radius: 6px;
                }
            """)
        self.status_badge.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.status_badge)
        
        background_layout.addWidget(header_frame)

        # ---------- MAIN CONTENT ----------
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)

        # ---------- LEFT SIDEBAR ----------
        sidebar = QFrame()
        sidebar.setMinimumWidth(200)
        sidebar.setMaximumWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: rgba(42, 47, 79, 180);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 30);
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(12)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)

        # Sidebar title
        sidebar_title = QLabel("Actions")
        sidebar_title.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 25px;
                font-weight: 600;
                padding: 0px;
                border: 0px;
            }
        """)
        sidebar_title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(sidebar_title)

        # Action buttons
        def add_action_btn(text, callback):
            btn = ModernButton(text)
            btn.clicked.connect(callback)
            sidebar_layout.addWidget(btn)
            return btn

        self.btn_add = add_action_btn("Add PDF Files", self.add_pdfs)
        self.btn_up = add_action_btn("Move Up", self.move_up)
        self.btn_down = add_action_btn("Move Down", self.move_down)
        self.btn_remove = add_action_btn("Remove Selected", self.remove_selected)
        self.btn_clear = add_action_btn("Clear All", self.clear_all)

        sidebar_layout.addStretch(1)

        # Merge button (special style)
        self.merge_btn = QPushButton("MERGE")
        self.merge_btn.clicked.connect(self.merge_pdfs)
        self.merge_btn.setMinimumHeight(50)
        self.merge_btn.setCursor(Qt.PointingHandCursor)
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background: #2E8B57;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 10px;
                padding: 12px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: #00A693;
            }
            QPushButton:pressed {
                background: #700A07;
            }
        """)
        sidebar_layout.addWidget(self.merge_btn)

        content_layout.addWidget(sidebar)

        # ---------- RIGHT PANEL (File List) ----------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)

        # File count panel
        count_frame = QFrame()
        count_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(42, 47, 79, 150);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 20);
                padding: 15px;
            }
        """)
        
        count_layout = QHBoxLayout(count_frame)
        self.file_count = QLabel("Files Selected: 0")
        self.file_count.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: 600;
            }
        """)
        count_layout.addWidget(self.file_count)
        count_layout.addStretch(1)
        
        # Add a visual indicator
        self.status_indicator = QLabel("Ready")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        count_layout.addWidget(self.status_indicator)
        
        right_layout.addWidget(count_frame)

        # Table widget - UPDATED FOR CONSISTENT SELECTION
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["No.", "File Name", "Size"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAcceptDrops(True)
        self.table.setDragDropMode(QTableWidget.DropOnly)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 10px;
                gridline-color: rgba(255, 255, 255, 20);
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255, 255, 255, 10);
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #4A4F7F;
                color: #FFFFFF;
            }
            QHeaderView::section {
                background-color: rgba(42, 47, 79, 200);
                color: #FFFFFF;
                padding: 10px;
                border: none;
                font-weight: 600;
                font-size: 14px;
            }
            QTableWidget QScrollBar:vertical {
                background: rgba(42, 47, 79, 100);
                width: 12px;
                border-radius: 6px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 50);
                border-radius: 6px;
                min-height: 30px;
            }
            QTableWidget QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 70);
            }
        """)
        
        # Set column widths
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(2, 100)
        
        right_layout.addWidget(self.table, 1)

        # Enable drag and drop for the table
        self.table.dragEnterEvent = self.table_drag_enter
        self.table.dropEvent = self.table_drop_event

        # Footer
        footer = QLabel("© 2026 - Kay Xam. All rights reserved.")
        footer.setStyleSheet("""
            QLabel {
                color: #8888AA;
                font-size: 12px;
                padding-top: 10px;
                border-top: 1px solid rgba(255, 255, 255, 10);
            }
        """)
        footer.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(footer)

        content_layout.addWidget(right_panel, 1)
        background_layout.addWidget(content_widget, 1)

        # Set the background as main widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(background)

    # ---------- HELPERS ----------
    def update_stats(self):
        count = len(self.pdf_files)
        self.file_count.setText(f"🔴 Files Selected: {count}")
        
        # Update status indicator based on file count
        if count == 0:
            self.status_indicator.setText("Add PDF files")
            self.status_indicator.setStyleSheet("color: #FFB74D; font-size: 14px; font-weight: 500;")
        elif count < 2:
            self.status_indicator.setText("Need 2+ files to merge")
            self.status_indicator.setStyleSheet("color: #FFB74D; font-size: 14px; font-weight: 500;")
        else:
            self.status_indicator.setText("Ready to merge")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: 500;")

    def format_size(self, b):
        for u in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return "?"

    def refresh(self):
        self.table.setRowCount(0)
        for i, f in enumerate(self.pdf_files):
            self.table.insertRow(i)
            
            # Add row number
            num_item = QTableWidgetItem(f"{i + 1}")
            num_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, num_item)
            
            # Add file name
            name_item = QTableWidgetItem(os.path.basename(f))
            self.table.setItem(i, 1, name_item)
            
            # Add file size
            size_item = QTableWidgetItem(self.format_size(os.path.getsize(f)))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, size_item)
        
        self.update_stats()

    def table_drag_enter(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def table_drop_event(self, event):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                files.append(file_path)
        
        if files:
            for f in files:
                if f not in self.pdf_files:
                    self.pdf_files.append(f)
            self.refresh()
            self.status_indicator.setText("Files added via drag-drop")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: 500;")
            QTimer.singleShot(2000, lambda: self.update_stats())

    # ---------- ACTIONS (LAZY IMPORTS) ----------
    def add_pdfs(self):
        from PyQt5.QtWidgets import QFileDialog
        dialog = QFileDialog(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        dialog.setStyleSheet("""
            QFileDialog {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D324F, stop:1 #1E233C);
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QFileDialog QWidget {
                background-color: transparent;
                color: #E0E0E0;
            }
            QListView, QTreeView {
                background-color: rgba(42, 47, 79, 150);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 5px;
            }
            QListView::item, QTreeView::item {
                color: #FFFFFF;
                padding: 5px;
            }
            QListView::item:selected, QTreeView::item:selected {
                background-color: #4A4F7F;
            }
            QPushButton {
                background-color: #2A2F4F;
                color: #FFFFFF;
                border: 2px solid #4A4F7F;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #4A4F7F;
                border-color: #6A6F9F;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        files, _ = dialog.getOpenFileNames()
        if files:
            for f in files:
                if f not in self.pdf_files:
                    self.pdf_files.append(f)
            self.refresh()
            self.status_indicator.setText("Files added")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 14px; font-weight: 500;")

    def move_up(self):
        r = self.table.currentRow()
        if r > 0:
            self.pdf_files[r], self.pdf_files[r - 1] = self.pdf_files[r - 1], self.pdf_files[r]
            self.refresh()
            self.table.selectRow(r - 1)

    def move_down(self):
        r = self.table.currentRow()
        if 0 <= r < len(self.pdf_files) - 1:
            self.pdf_files[r], self.pdf_files[r + 1] = self.pdf_files[r + 1], self.pdf_files[r]
            self.refresh()
            self.table.selectRow(r + 1)

    def remove_selected(self):
        r = self.table.currentRow()
        if r >= 0:
            del self.pdf_files[r]
            self.refresh()
            self.status_indicator.setText("File removed")
            QTimer.singleShot(1500, lambda: self.update_stats())

    def clear_all(self):
        if self.pdf_files:
            result = show_themed_message(self, "Clear All Files", 
                "Are you sure you want to remove all PDF files?", 
                "warning", ["Yes", "No"])
            
            if result:
                self.pdf_files.clear()
                self.refresh()
                self.status_indicator.setText("All files cleared")

    def merge_pdfs(self):
        from PyQt5.QtWidgets import QFileDialog, QProgressDialog
        from PyPDF2 import PdfReader, PdfWriter

        if len(self.pdf_files) < 2:
            show_themed_message(self, "Not Enough Files", 
                "Please add at least two PDF files to merge.", "warning")
            return

        if not LicenseManager.is_activated():
            if not LicenseManager.is_trial_valid():
                show_themed_message(self, "Trial Expired", 
                    "Your free trial has expired. Please purchase a license to continue.", "warning")
                return
            
            activation_dialog = ActivationDialog(self)
            if not activation_dialog.exec_():
                return

        dialog = QFileDialog(self, "Save Merged PDF", "merged_document.pdf", "PDF Files (*.pdf)")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        dialog.setStyleSheet("""
            QFileDialog {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D324F, stop:1 #1E233C);
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            QFileDialog QWidget {
                background-color: transparent;
                color: #E0E0E0;
            }
            QListView, QTreeView {
                background-color: rgba(42, 47, 79, 150);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 5px;
            }
            QListView::item, QTreeView::item {
                color: #FFFFFF;
                padding: 5px;
            }
            QListView::item:selected, QTreeView::item:selected {
                background-color: #4A4F7F;
            }
            QPushButton {
                background-color: #2A2F4F;
                color: #FFFFFF;
                border: 2px solid #4A4F7F;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #4A4F7F;
                border-color: #6A6F9F;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: rgba(42, 47, 79, 150);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        if dialog.exec_():
            path = dialog.selectedFiles()[0]
        else:
            return

        # Create progress dialog
        progress = QProgressDialog("Merging PDF files...", "Cancel", 0, len(self.pdf_files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Processing")
        progress.setStyleSheet("""
            QProgressDialog {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2D324F, stop:1 #1E233C);
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                border: 2px solid #4A4F7F;
                border-radius: 10px;
            }
            QLabel {
                color: #FFFFFF;
            }
            QProgressBar {
                background-color: rgba(42, 47, 79, 150);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 5px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2A2F4F;
                color: #FFFFFF;
                border: 2px solid #4A4F7F;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #4A4F7F;
                border-color: #6A6F9F;
            }
        """)

        writer = PdfWriter()
        
        try:
            for i, pdf in enumerate(self.pdf_files):
                if progress.wasCanceled():
                    show_themed_message(self, "Cancelled", "Merge operation cancelled.", "info")
                    return
                
                progress.setLabelText(f"Processing: {os.path.basename(pdf)}")
                reader = PdfReader(pdf)
                
                for p in reader.pages:
                    writer.add_page(p)
                
                progress.setValue(i + 1)
            
            with open(path, "wb") as f:
                writer.write(f)
            
            # Success message
            show_themed_message(self, "Success", 
                f"✅ PDFs merged successfully!\n\nFile saved as:\n{os.path.basename(path)}", "success")
            
        except Exception as e:
            show_themed_message(self, "Error", f"Failed to merge PDFs:\n{str(e)}", "error")


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    set_windows_app_id()

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    icon_path = app_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Set application style
    app.setStyle("Fusion")

    win = PDFMergerApp()
    sys.exit(app.exec_())
