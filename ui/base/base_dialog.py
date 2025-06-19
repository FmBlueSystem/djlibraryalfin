"""
Base dialog class for consistent UI across the application
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from config.design_system import Theme, Typography, Spacing, Layout
from ..styles.ui_helpers import apply_consistent_margins, apply_consistent_spacing, create_separator


class BaseDialog(QDialog):
    """
    Base dialog class that provides consistent styling and behavior
    for all dialogs in the application.
    """
    
    # Signals
    accepted = Signal()
    rejected = Signal()
    
    def __init__(self, title="Dialog", width=400, height=300, parent=None):
        super().__init__(parent)
        self.setup_dialog(title, width, height)
        self.setup_ui()
        self.apply_theme()
        
    def setup_dialog(self, title, width, height):
        """Configure basic dialog properties"""
        self.setWindowTitle(title)
        self.setFixedSize(width, height)
        self.setModal(True)
        
        # Set window flags for consistent behavior
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowTitleHint
        )
        
    def setup_ui(self):
        """Setup the base UI structure"""
        # Main layout
        self.layout = QVBoxLayout(self)
        apply_consistent_margins(self.layout, Spacing.LG)
        apply_consistent_spacing(self.layout, Spacing.MD)
        
        # Header area (optional)
        self.header_layout = QVBoxLayout()
        apply_consistent_spacing(self.header_layout, Spacing.SM)
        self.layout.addLayout(self.header_layout)
        
        # Content area
        self.content_layout = QVBoxLayout()
        apply_consistent_spacing(self.content_layout, Spacing.SM)
        self.layout.addLayout(self.content_layout)
        
        # Add stretch to push buttons to bottom
        self.layout.addStretch()
        
        # Separator before buttons
        separator = create_separator()
        self.layout.addWidget(separator)
        
        # Button area
        self.setup_buttons()
        
    def setup_buttons(self):
        """Setup the standard dialog buttons"""
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        
        # Create standard buttons
        self.cancel_button = self.create_button("Cancelar", "secondary")
        self.ok_button = self.create_button("Aceptar", "primary")
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept)
        
        # Add buttons to layout
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.ok_button)
        
        self.layout.addLayout(self.button_layout)
        
    def create_button(self, text, style_type="primary"):
        """Create a consistently styled button"""
        button = QPushButton(text)
        button.setObjectName(f"{style_type}Button")
        button.setMinimumSize(80, Layout.BUTTON_HEIGHT)
        button.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY, Typography.MEDIUM))
        return button
        
    def apply_theme(self):
        """Apply the global theme to this dialog"""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT_PRIMARY};
                font-family: {Typography.FONT_FAMILY};
                font-size: {Typography.BODY}px;
            }}
            
            QPushButton {{
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
                min-height: {Layout.BUTTON_HEIGHT - (Spacing.SM * 2)}px;
            }}
            
            QPushButton#primaryButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {Theme.PRIMARY_DARK};
            }}
            
            QPushButton#primaryButton:pressed {{
                background-color: {Theme.PRIMARY_VARIANT};
            }}
            
            QPushButton#secondaryButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: 2px solid {Theme.PRIMARY};
            }}
            
            QPushButton#secondaryButton:hover {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
            
            QPushButton#secondaryButton:pressed {{
                background-color: {Theme.SELECTION};
            }}
            
            QPushButton#dangerButton {{
                background-color: {Theme.ERROR};
                color: {Theme.TEXT_ON_PRIMARY};
            }}
            
            QPushButton#dangerButton:hover {{
                background-color: #D32F2F;
            }}
            
            QLabel#dialogTitle {{
                font-size: {Typography.H5}px;
                font-weight: {Typography.SEMI_BOLD};
                color: {Theme.TEXT_PRIMARY};
                margin-bottom: {Spacing.XS}px;
            }}
            
            QLabel#dialogSubtitle {{
                font-size: {Typography.BODY}px;
                font-weight: {Typography.REGULAR};
                color: {Theme.TEXT_SECONDARY};
            }}
            
            QFrame[objectName="separator"] {{
                background-color: {Theme.DIVIDER};
                max-height: 1px;
                margin: {Spacing.SM}px 0px;
            }}
        """)
        
    def add_header(self, title, subtitle=None):
        """Add a header with title and optional subtitle"""
        title_label = QLabel(title)
        title_label.setObjectName("dialogTitle")
        self.header_layout.addWidget(title_label)
        
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("dialogSubtitle")
            subtitle_label.setWordWrap(True)
            self.header_layout.addWidget(subtitle_label)
            
    def add_custom_button(self, text, callback, style_type="secondary"):
        """Add a custom button to the button layout"""
        button = self.create_button(text, style_type)
        button.clicked.connect(callback)
        
        # Insert before the standard buttons
        self.button_layout.insertWidget(self.button_layout.count() - 2, button)
        return button
        
    def set_button_text(self, ok_text="Aceptar", cancel_text="Cancelar"):
        """Customize the text of standard buttons"""
        self.ok_button.setText(ok_text)
        self.cancel_button.setText(cancel_text)
        
    def hide_cancel_button(self):
        """Hide the cancel button for info dialogs"""
        self.cancel_button.hide()
        
    def set_danger_mode(self):
        """Set the OK button to danger style for destructive actions"""
        self.ok_button.setObjectName("dangerButton")
        self.apply_theme()  # Reapply theme to update button style
        
    def accept(self):
        """Override accept to emit custom signal"""
        self.accepted.emit()
        super().accept()
        
    def reject(self):
        """Override reject to emit custom signal"""
        self.rejected.emit()
        super().reject()


class ConfirmDialog(BaseDialog):
    """Pre-configured confirmation dialog"""
    
    def __init__(self, message, title="Confirmar", parent=None):
        super().__init__(title, 350, 150, parent)
        self.add_header(title, message)
        self.set_button_text("Confirmar", "Cancelar")


class InfoDialog(BaseDialog):
    """Pre-configured information dialog"""
    
    def __init__(self, message, title="Información", parent=None):
        super().__init__(title, 350, 150, parent)
        self.add_header(title, message)
        self.hide_cancel_button()
        self.set_button_text("Entendido")


class ErrorDialog(BaseDialog):
    """Pre-configured error dialog"""
    
    def __init__(self, message, title="Error", parent=None):
        super().__init__(title, 400, 200, parent)
        self.add_header(title, message)
        self.hide_cancel_button()
        self.set_button_text("Cerrar")
        
        # Apply error styling
        self.setStyleSheet(self.styleSheet() + f"""
            QLabel#dialogTitle {{
                color: {Theme.ERROR};
            }}
        """)