"""
Base window class for consistent UI across the application
"""
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from config.design_system import Theme, Typography, Spacing, Layout
from ..styles.ui_helpers import load_stylesheet, apply_consistent_margins, apply_consistent_spacing


class BaseWindow(QMainWindow):
    """
    Base window class that provides consistent styling and behavior
    for all main windows in the application.
    """
    
    # Signals
    window_closed = Signal()
    
    def __init__(self, title="DjAlfin", width=800, height=600, parent=None):
        super().__init__(parent)
        self.setup_window(title, width, height)
        self.setup_ui()
        self.apply_theme()
        
    def setup_window(self, title, width, height):
        """Configure basic window properties"""
        self.setWindowTitle(title)
        self.resize(width, height)
        self.setMinimumSize(600, 400)
        
        # Set window flags for consistent behavior
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint
        )
        
    def setup_ui(self):
        """Setup the base UI structure"""
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout with consistent margins and spacing
        self.main_layout = QVBoxLayout(self.central_widget)
        apply_consistent_margins(self.main_layout, Spacing.MD)
        apply_consistent_spacing(self.main_layout, Spacing.MD)
        
        # Header area (optional)
        self.header_widget = None
        
        # Content area
        self.content_layout = QVBoxLayout()
        apply_consistent_spacing(self.content_layout, Spacing.SM)
        self.main_layout.addLayout(self.content_layout)
        
        # Footer area (optional)
        self.footer_widget = None
        
    def apply_theme(self):
        """Apply the global theme to this window"""
        stylesheet = load_stylesheet("main_window.qss")
        if stylesheet:
            self.setStyleSheet(stylesheet)
        else:
            # Fallback inline styles using design system
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-color: {Theme.BACKGROUND};
                    color: {Theme.TEXT_PRIMARY};
                    font-family: {Typography.FONT_FAMILY};
                    font-size: {Typography.BODY}px;
                }}
            """)
            
    def add_header(self, title, subtitle=None, show_logo=False):
        """Add a consistent header to the window"""
        if self.header_widget:
            self.main_layout.removeWidget(self.header_widget)
            self.header_widget.deleteLater()
            
        self.header_widget = self.create_header(title, subtitle, show_logo)
        self.main_layout.insertWidget(0, self.header_widget)
        
    def create_header(self, title, subtitle=None, show_logo=False):
        """Create a header widget with consistent styling"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(Layout.HEADER_HEIGHT)
        
        layout = QHBoxLayout(header)
        apply_consistent_margins(layout, Spacing.MD)
        
        # Logo area (if requested)
        if show_logo:
            logo_label = QLabel("🎵")  # Placeholder - replace with actual logo
            logo_label.setObjectName("logo")
            layout.addWidget(logo_label)
            
        # Title area
        title_container = QVBoxLayout()
        title_container.setSpacing(Spacing.XS)
        
        title_label = QLabel(title)
        title_label.setObjectName("headerTitle")
        title_label.setFont(QFont(Typography.FONT_FAMILY, Typography.H4, Typography.BOLD))
        title_container.addWidget(title_label)
        
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("headerSubtitle")
            subtitle_label.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY, Typography.REGULAR))
            title_container.addWidget(subtitle_label)
            
        layout.addLayout(title_container)
        layout.addStretch()
        
        return header
        
    def add_footer(self, widget):
        """Add a footer widget to the window"""
        if self.footer_widget:
            self.main_layout.removeWidget(self.footer_widget)
            self.footer_widget.deleteLater()
            
        self.footer_widget = widget
        self.main_layout.addWidget(self.footer_widget)
        
    def set_loading_state(self, loading=True):
        """Set the window to a loading state"""
        self.setEnabled(not loading)
        if loading:
            self.setCursor(Qt.CursorShape.WaitCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
    def show_error(self, message, title="Error"):
        """Show an error message using consistent styling"""
        from PySide6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply consistent styling to message box
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY};
            }}
            QMessageBox QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {Theme.PRIMARY_DARK};
            }}
        """)
        
        return msg_box.exec()
        
    def show_success(self, message, title="Success"):
        """Show a success message using consistent styling"""
        from PySide6.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Apply success color theming
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY};
            }}
            QMessageBox QPushButton {{
                background-color: {Theme.SUCCESS};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #388E3C;
            }}
        """)
        
        return msg_box.exec()
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.window_closed.emit()
        super().closeEvent(event)