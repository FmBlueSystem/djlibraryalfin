"""
UI helper utilities for consistent styling and layout
"""
import os
from PySide6.QtCore import QFile, QTextStream
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont

from config.design_system import Theme, Typography, Spacing, Layout


def load_stylesheet(filename):
    """Load a stylesheet from the styles directory"""
    file_path = os.path.join(
        os.path.dirname(__file__), 
        filename
    )
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    # Fallback to Qt resource system if file doesn't exist
    file = QFile(f":/styles/{filename}")
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        return stream.readAll()
    
    return ""


def apply_consistent_margins(layout, margin=Spacing.MD):
    """Apply consistent margins to a layout"""
    if isinstance(margin, int):
        layout.setContentsMargins(margin, margin, margin, margin)
    elif isinstance(margin, (list, tuple)) and len(margin) == 4:
        layout.setContentsMargins(*margin)
    else:
        layout.setContentsMargins(margin, margin, margin, margin)


def apply_consistent_spacing(layout, spacing=Spacing.MD):
    """Apply consistent spacing to a layout"""
    layout.setSpacing(spacing)


def create_separator(orientation="horizontal"):
    """Create a visual separator line"""
    line = QFrame()
    line.setObjectName("separator")
    
    if orientation.lower() == "horizontal":
        line.setFrameShape(QFrame.Shape.HLine)
        line.setMaximumHeight(1)
    else:
        line.setFrameShape(QFrame.Shape.VLine)
        line.setMaximumWidth(1)
    
    line.setFrameShadow(QFrame.Shadow.Plain)
    line.setStyleSheet(f"background-color: {Theme.DIVIDER};")
    
    return line


def create_header_label(text, level=1):
    """Create a consistently styled header label"""
    label = QLabel(text)
    
    # Map header levels to font sizes and object names
    header_config = {
        1: (Typography.H1, "h1Header"),
        2: (Typography.H2, "h2Header"),
        3: (Typography.H3, "h3Header"),
        4: (Typography.H4, "h4Header"),
        5: (Typography.H5, "h5Header"),
        6: (Typography.H6, "h6Header"),
    }
    
    if level in header_config:
        font_size, object_name = header_config[level]
        label.setObjectName(object_name)
        label.setFont(QFont(Typography.FONT_FAMILY, font_size, Typography.SEMI_BOLD))
    else:
        # Default to H3 for invalid levels
        label.setObjectName("h3Header")
        label.setFont(QFont(Typography.FONT_FAMILY, Typography.H3, Typography.SEMI_BOLD))
    
    return label


def create_section_title(text):
    """Create a section title label"""
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    label.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY_SMALL, Typography.SEMI_BOLD))
    return label


def create_value_label(text, monospace=True):
    """Create a value display label with consistent styling"""
    label = QLabel(text)
    label.setObjectName("valueLabel")
    
    if monospace:
        label.setFont(QFont(Typography.MONO_FAMILY, Typography.BODY, Typography.SEMI_BOLD))
    else:
        label.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY, Typography.SEMI_BOLD))
    
    return label


def create_card_layout(title=None, content_layout=None):
    """Create a card-style container with optional title"""
    card = QFrame()
    card.setObjectName("card")
    card.setStyleSheet(f"""
        QFrame#card {{
            background-color: {Theme.SURFACE};
            border: 1px solid {Theme.BORDER};
            border-radius: {Layout.BORDER_RADIUS_MD}px;
            padding: {Spacing.MD}px;
        }}
    """)
    
    layout = QVBoxLayout(card)
    apply_consistent_margins(layout, Spacing.MD)
    apply_consistent_spacing(layout, Spacing.SM)
    
    if title:
        title_label = create_section_title(title)
        layout.addWidget(title_label)
        
        # Add separator after title
        separator = create_separator()
        layout.addWidget(separator)
    
    if content_layout:
        layout.addLayout(content_layout)
    
    return card, layout


def create_form_row(label_text, widget, required=False):
    """Create a form row with label and widget"""
    row_layout = QHBoxLayout()
    apply_consistent_spacing(row_layout, Spacing.SM)
    
    # Create label
    label = QLabel(label_text)
    if required:
        label.setText(f"{label_text} *")
        label.setStyleSheet(f"color: {Theme.ERROR};")
    
    label.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY, Typography.MEDIUM))
    label.setMinimumWidth(120)  # Consistent label width
    
    row_layout.addWidget(label)
    row_layout.addWidget(widget, 1)  # Widget takes remaining space
    
    return row_layout


def create_button_row(*buttons, alignment="right"):
    """Create a row of buttons with consistent spacing"""
    row_layout = QHBoxLayout()
    apply_consistent_spacing(row_layout, Spacing.SM)
    
    if alignment == "left":
        for button in buttons:
            row_layout.addWidget(button)
        row_layout.addStretch()
    elif alignment == "center":
        row_layout.addStretch()
        for button in buttons:
            row_layout.addWidget(button)
        row_layout.addStretch()
    else:  # right alignment (default)
        row_layout.addStretch()
        for button in buttons:
            row_layout.addWidget(button)
    
    return row_layout


def apply_card_style(widget, padding=Spacing.MD):
    """Apply card styling to any widget"""
    widget.setStyleSheet(f"""
        background-color: {Theme.SURFACE};
        border: 1px solid {Theme.BORDER};
        border-radius: {Layout.BORDER_RADIUS_MD}px;
        padding: {padding}px;
    """)


def apply_panel_style(widget, padding=Spacing.MD):
    """Apply panel styling to any widget"""
    widget.setStyleSheet(f"""
        background-color: {Theme.BACKGROUND};
        border: 1px solid {Theme.BORDER};
        border-radius: {Layout.BORDER_RADIUS_SM}px;
        padding: {padding}px;
    """)


def create_info_box(message, info_type="info"):
    """Create an information box with appropriate styling"""
    box = QFrame()
    box.setObjectName("infoBox")
    
    # Color mapping for different info types
    colors = {
        "info": Theme.INFO,
        "success": Theme.SUCCESS,
        "warning": Theme.WARNING,
        "error": Theme.ERROR,
    }
    
    color = colors.get(info_type, Theme.INFO)
    
    box.setStyleSheet(f"""
        QFrame#infoBox {{
            background-color: {color}22;  /* 22 = ~13% alpha in hex */
            border: 1px solid {color};
            border-radius: {Layout.BORDER_RADIUS_SM}px;
            padding: {Spacing.SM}px {Spacing.MD}px;
        }}
    """)
    
    layout = QHBoxLayout(box)
    apply_consistent_margins(layout, Spacing.SM)
    
    # Add icon or indicator
    icon_label = QLabel("ℹ️" if info_type == "info" else 
                       "✅" if info_type == "success" else
                       "⚠️" if info_type == "warning" else "❌")
    layout.addWidget(icon_label)
    
    # Add message
    message_label = QLabel(message)
    message_label.setWordWrap(True)
    message_label.setStyleSheet(f"color: {color}; background-color: transparent;")
    layout.addWidget(message_label, 1)
    
    return box


def set_font_size(widget, size):
    """Set font size while preserving other font properties"""
    font = widget.font()
    font.setPointSize(size)
    widget.setFont(font)


def set_font_weight(widget, weight):
    """Set font weight while preserving other font properties"""
    font = widget.font()
    font.setWeight(weight)
    widget.setFont(font)


def create_loading_overlay(parent_widget, message="Cargando..."):
    """Create a loading overlay for a widget"""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PySide6.QtCore import Qt
    
    overlay = QWidget(parent_widget)
    overlay.setStyleSheet(f"""
        background-color: rgba(255, 255, 255, 200);
        border-radius: {Layout.BORDER_RADIUS_SM}px;
    """)
    
    layout = QVBoxLayout(overlay)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Add loading message
    label = QLabel(message)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setFont(QFont(Typography.FONT_FAMILY, Typography.BODY, Typography.MEDIUM))
    layout.addWidget(label)
    
    # Position overlay to cover parent
    overlay.setGeometry(parent_widget.rect())
    overlay.show()
    
    return overlay


def remove_loading_overlay(overlay):
    """Remove a loading overlay"""
    if overlay:
        overlay.hide()
        overlay.deleteLater()


# Color utility functions
def lighten_color(hex_color, factor=0.1):
    """Lighten a hex color by a given factor"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Lighten each component
    rgb = tuple(min(255, int(c + (255 - c) * factor)) for c in rgb)
    
    # Convert back to hex
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def darken_color(hex_color, factor=0.1):
    """Darken a hex color by a given factor"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Darken each component
    rgb = tuple(max(0, int(c * (1 - factor))) for c in rgb)
    
    # Convert back to hex
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"