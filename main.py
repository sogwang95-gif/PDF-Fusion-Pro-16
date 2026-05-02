import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPainter


class GradientWidget(QWidget):
    """Widget with gradient background"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_color = QColor(45, 50, 80)
        self.end_color = QColor(30, 35, 60)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, self.start_color)
        gradient.setColorAt(1, self.end_color)
        painter.fillRect(self.rect(), gradient)


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
        self.setMinimumSize(1000, 600)

        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.pdf_files = []

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
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(5)
        
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
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
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

    # ---------- ACTIONS (LAZY IMPORTS) ----------
    def add_pdfs(self):
        from PyQt5.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
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
            reply = QMessageBox.question(self, "Clear All Files", 
                "Are you sure you want to remove all PDF files?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.pdf_files.clear()
                self.refresh()
                self.status_indicator.setText("All files cleared")

    def merge_pdfs(self):
        from PyQt5.QtWidgets import QFileDialog, QProgressDialog
        from PyPDF2 import PdfReader, PdfWriter

        if len(self.pdf_files) < 2:
            QMessageBox.warning(self, "Not Enough Files", 
                "Please add at least two PDF files to merge.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", 
            "merged_document.pdf", "PDF Files (*.pdf)")
        
        if not path:
            return

        # Create progress dialog
        progress = QProgressDialog("Merging PDF files...", "Cancel", 0, len(self.pdf_files), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Processing")

        writer = PdfWriter()
        
        try:
            for i, pdf in enumerate(self.pdf_files):
                if progress.wasCanceled():
                    QMessageBox.information(self, "Cancelled", "Merge operation cancelled.")
                    return
                
                progress.setLabelText(f"Processing: {os.path.basename(pdf)}")
                reader = PdfReader(pdf)
                
                for p in reader.pages:
                    writer.add_page(p)
                
                progress.setValue(i + 1)
            
            with open(path, "wb") as f:
                writer.write(f)
            
            # Success message
            QMessageBox.information(self, "Success", 
                f"✅ PDFs merged successfully!\n\nFile saved as:\n{os.path.basename(path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to merge PDFs:\n{str(e)}")


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    
    # Set application style
    app.setStyle("Fusion")
    
    win = PDFMergerApp()
    sys.exit(app.exec_())