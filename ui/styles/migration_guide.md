# Migration Guide: Visual Consistency System

This guide explains how to migrate existing UI components to use the new visual consistency system.

## Quick Start

### 1. Update Imports

Replace old imports:
```python
# Old way
from PyQt5.QtWidgets import QMainWindow, QDialog
from ui.theme import COLORS, FONTS

# New way
from ui.base.base_window import BaseWindow
from ui.base.base_dialog import BaseDialog
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.styles.ui_helpers import create_header_label, create_form_row
from config.design_system import Theme, Typography, Spacing
```

### 2. Inherit from Base Classes

Replace old class definitions:
```python
# Old way
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Window")
        self.setFixedSize(800, 600)
        # Custom setup...

# New way
class MyWindow(BaseWindow):
    def __init__(self):
        super().__init__("My Window", 800, 600)
        self.setup_content()
        
    def setup_content(self):
        # Add header
        self.add_header("My Window", "Window description")
        # Add content to self.content_layout
```

### 3. Use Design System Constants

Replace magic numbers and hard-coded colors:
```python
# Old way
layout.setContentsMargins(16, 16, 16, 16)
layout.setSpacing(8)
button.setStyleSheet("background-color: #2196F3; color: white;")

# New way
apply_consistent_margins(layout, Spacing.MD)
apply_consistent_spacing(layout, Spacing.SM)
button = PrimaryButton("Click me")
```

## Migration Checklist

### For Windows (QMainWindow)

- [ ] Inherit from `BaseWindow` instead of `QMainWindow`
- [ ] Remove manual window setup (title, size, etc.) from `__init__`
- [ ] Pass window parameters to `super().__init__()`
- [ ] Use `self.content_layout` for main content
- [ ] Replace custom headers with `self.add_header()`
- [ ] Use `self.show_error()` and `self.show_success()` for messages

### For Dialogs (QDialog)

- [ ] Inherit from `BaseDialog` instead of `QDialog`
- [ ] Remove manual dialog setup from `__init__`
- [ ] Pass dialog parameters to `super().__init__()`
- [ ] Use `self.content_layout` for main content
- [ ] Replace custom headers with `self.add_header()`
- [ ] Use consistent button creation methods
- [ ] Override button text with `self.set_button_text()`

### For Buttons

- [ ] Replace `QPushButton` with appropriate button class:
  - `PrimaryButton` for main actions
  - `SecondaryButton` for secondary actions
  - `DangerButton` for destructive actions
  - `SuccessButton` for positive actions
  - `TextButton` for subtle actions
  - `IconButton` for icon-only buttons
  - `ToggleButton` for toggle states

### For Layouts

- [ ] Use `apply_consistent_margins()` instead of `setContentsMargins()`
- [ ] Use `apply_consistent_spacing()` instead of `setSpacing()`
- [ ] Use `create_form_row()` for form layouts
- [ ] Use `create_button_row()` for button groups
- [ ] Use `create_card_layout()` for grouped content

### For Styling

- [ ] Remove inline stylesheets where possible
- [ ] Use design system constants (`Theme.*`, `Typography.*`, `Spacing.*`)
- [ ] Apply object names for QSS targeting
- [ ] Use helper functions for common styling patterns

## Example Migration

### Before (Old Style)
```python
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Application Settings")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Form
        form = QFormLayout()
        self.name_edit = QLineEdit()
        form.addRow("Name:", self.name_edit)
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        ok_btn = QPushButton("OK")
        ok_btn.setStyleSheet("background-color: blue; color: white;")
        
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
```

### After (New Style)
```python
class SettingsDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__("Settings", 400, 300, parent)
        self.setup_content()
        
    def setup_content(self):
        # Header
        self.add_header("Application Settings", "Configure your preferences")
        
        # Form
        self.name_edit = QLineEdit()
        name_row = create_form_row("Name:", self.name_edit, required=True)
        self.content_layout.addLayout(name_row)
        
        # Buttons are automatically created by BaseDialog
        # Just customize the text if needed
        self.set_button_text("Save", "Cancel")
```

## Common Patterns

### Creating Cards/Panels
```python
# Old way
panel = QFrame()
panel.setStyleSheet("background: white; border: 1px solid gray;")
layout = QVBoxLayout(panel)

# New way
panel, layout = create_card_layout("Panel Title")
```

### Form Layouts
```python
# Old way
form = QFormLayout()
form.addRow("Label:", widget)

# New way
row = create_form_row("Label:", widget, required=True)
layout.addLayout(row)
```

### Button Groups
```python
# Old way
button_layout = QHBoxLayout()
button_layout.addStretch()
btn1 = QPushButton("Button 1")
btn2 = QPushButton("Button 2")
button_layout.addWidget(btn1)
button_layout.addWidget(btn2)

# New way
btn1 = SecondaryButton("Button 1")
btn2 = PrimaryButton("Button 2")
button_row = create_button_row(btn1, btn2, alignment="right")
```

### Information Boxes
```python
# Old way
info_label = QLabel("Important information")
info_label.setStyleSheet("background: lightblue; padding: 10px;")

# New way
info_box = create_info_box("Important information", "info")
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all new modules are properly imported
2. **Missing Layouts**: Check that you're adding content to the correct layout (`self.content_layout`)
3. **Styling Issues**: Ensure QSS files are being loaded correctly
4. **Button Behavior**: Remember to reconnect signals if overriding default button behavior

### Testing Migration

1. Run the application and check visual consistency
2. Test all interactive elements (buttons, inputs, etc.)
3. Verify that dialogs and windows behave correctly
4. Check that themes apply properly
5. Test on different screen sizes if applicable

## Best Practices

1. **Gradual Migration**: Migrate one component at a time
2. **Test Thoroughly**: Test each migrated component before moving to the next
3. **Consistent Naming**: Use consistent object names for QSS targeting
4. **Documentation**: Update any component documentation to reflect new patterns
5. **Code Review**: Have migrations reviewed to ensure consistency

## Resources

- Design System Constants: `config/design_system.py`
- Base Classes: `ui/base/`
- Components: `ui/components/`
- Helpers: `ui/styles/ui_helpers.py`
- Main Stylesheet: `ui/styles/main_style.qss`