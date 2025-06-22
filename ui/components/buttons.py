"""
Consistent button components for the application
"""
from PySide6.QtWidgets import QPushButton, QHBoxLayout, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from config.design_system import Theme, Typography, Spacing, Layout


class BaseButton(QPushButton):
    """Base button class with consistent styling"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, parent)
        self.setup_button()
        if icon:
            self.setIcon(icon)
            
    def setup_button(self):
        """Setup base button properties"""
        self.setMinimumHeight(Layout.BUTTON_HEIGHT)
        self.setMinimumWidth(80)
        self.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY, Typography.MEDIUM))
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PrimaryButton(BaseButton):
    """Primary action button (most important actions)"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, icon, parent)
        self.setObjectName("primaryButton")
        self.setStyleSheet(f"""
            QPushButton#primaryButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {Theme.PRIMARY_DARK};
            }}
            
            QPushButton#primaryButton:pressed {{
                background-color: {Theme.PRIMARY_VARIANT};
            }}
            
            QPushButton#primaryButton:disabled {{
                background-color: {Theme.TEXT_DISABLED};
                color: {Theme.TEXT_SECONDARY};
            }}
        """)


class SecondaryButton(BaseButton):
    """Secondary action button (less important actions)"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, icon, parent)
        self.setObjectName("secondaryButton")
        self.setStyleSheet(f"""
            QPushButton#secondaryButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: 2px solid {Theme.PRIMARY};
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
            }}
            
            QPushButton#secondaryButton:hover {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
            
            QPushButton#secondaryButton:pressed {{
                background-color: {Theme.SELECTION};
            }}
            
            QPushButton#secondaryButton:disabled {{
                border-color: {Theme.TEXT_DISABLED};
                color: {Theme.TEXT_DISABLED};
            }}
        """)


class DangerButton(BaseButton):
    """Danger button for destructive actions"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, icon, parent)
        self.setObjectName("dangerButton")
        self.setStyleSheet(f"""
            QPushButton#dangerButton {{
                background-color: {Theme.ERROR};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
            }}
            
            QPushButton#dangerButton:hover {{
                background-color: #D32F2F;
            }}
            
            QPushButton#dangerButton:pressed {{
                background-color: #B71C1C;
            }}
            
            QPushButton#dangerButton:disabled {{
                background-color: {Theme.TEXT_DISABLED};
                color: {Theme.TEXT_SECONDARY};
            }}
        """)


class SuccessButton(BaseButton):
    """Success button for positive actions"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, icon, parent)
        self.setObjectName("successButton")
        self.setStyleSheet(f"""
            QPushButton#successButton {{
                background-color: {Theme.SUCCESS};
                color: {Theme.TEXT_ON_PRIMARY};
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
            }}
            
            QPushButton#successButton:hover {{
                background-color: #388E3C;
            }}
            
            QPushButton#successButton:pressed {{
                background-color: #1B5E20;
            }}
            
            QPushButton#successButton:disabled {{
                background-color: {Theme.TEXT_DISABLED};
                color: {Theme.TEXT_SECONDARY};
            }}
        """)


class TextButton(BaseButton):
    """Text-only button for subtle actions"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, icon, parent)
        self.setObjectName("textButton")
        self.setStyleSheet(f"""
            QPushButton#textButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
            }}
            
            QPushButton#textButton:hover {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
            
            QPushButton#textButton:pressed {{
                background-color: {Theme.SELECTION};
            }}
            
            QPushButton#textButton:disabled {{
                color: {Theme.TEXT_DISABLED};
            }}
        """)


class IconButton(BaseButton):
    """Icon-only button for compact interfaces"""
    
    def __init__(self, icon, tooltip="", parent=None):
        super().__init__("", icon, parent)
        self.setObjectName("iconButton")
        self.setFixedSize(Layout.BUTTON_HEIGHT, Layout.BUTTON_HEIGHT)
        if tooltip:
            self.setToolTip(tooltip)
        self.setStyleSheet(f"""
            QPushButton#iconButton {{
                background-color: transparent;
                border: none;
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.XS}px;
            }}
            
            QPushButton#iconButton:hover {{
                background-color: {Theme.PRIMARY_LIGHT};
            }}
            
            QPushButton#iconButton:pressed {{
                background-color: {Theme.SELECTION};
            }}
            
            QPushButton#iconButton:disabled {{
                background-color: transparent;
            }}
        """)


class ToggleButton(BaseButton):
    """Toggle button that can be checked/unchecked"""
    
    def __init__(self, text="", icon=None, parent=None):
        super().__init__(text, icon, parent)
        self.setCheckable(True)
        self.setObjectName("toggleButton")
        self.setStyleSheet(f"""
            QPushButton#toggleButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: 2px solid {Theme.BORDER};
                border-radius: {Layout.BORDER_RADIUS_SM}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: {Typography.MEDIUM};
            }}
            
            QPushButton#toggleButton:hover {{
                border-color: {Theme.PRIMARY};
                color: {Theme.PRIMARY};
            }}
            
            QPushButton#toggleButton:checked {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_ON_PRIMARY};
                border-color: {Theme.PRIMARY};
            }}
            
            QPushButton#toggleButton:checked:hover {{
                background-color: {Theme.PRIMARY_DARK};
            }}
        """)


class ButtonGroup(QWidget):
    """Container for grouping related buttons"""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self) if orientation == Qt.Orientation.Horizontal else QVBoxLayout(self)
        self.layout.setSpacing(Spacing.SM)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
    def add_button(self, button):
        """Add a button to the group"""
        self.layout.addWidget(button)
        
    def add_stretch(self):
        """Add stretch to push buttons apart"""
        self.layout.addStretch()


# Convenience functions for common button combinations
def create_ok_cancel_buttons(ok_text="Aceptar", cancel_text="Cancelar"):
    """Create standard OK/Cancel button pair"""
    group = ButtonGroup()
    group.add_stretch()
    
    cancel_btn = SecondaryButton(cancel_text)
    ok_btn = PrimaryButton(ok_text)
    
    group.add_button(cancel_btn)
    group.add_button(ok_btn)
    
    return group, ok_btn, cancel_btn


def create_yes_no_buttons(yes_text="Sí", no_text="No"):
    """Create Yes/No button pair"""
    group = ButtonGroup()
    group.add_stretch()
    
    no_btn = SecondaryButton(no_text)
    yes_btn = PrimaryButton(yes_text)
    
    group.add_button(no_btn)
    group.add_button(yes_btn)
    
    return group, yes_btn, no_btn


def create_save_cancel_buttons(save_text="Guardar", cancel_text="Cancelar"):
    """Create Save/Cancel button pair"""
    group = ButtonGroup()
    group.add_stretch()
    
    cancel_btn = SecondaryButton(cancel_text)
    save_btn = SuccessButton(save_text)
    
    group.add_button(cancel_btn)
    group.add_button(save_btn)
    
    return group, save_btn, cancel_btn