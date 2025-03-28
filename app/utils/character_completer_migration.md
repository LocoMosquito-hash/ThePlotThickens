# CharacterCompleter Migration Guide

This guide explains how to migrate from the current multiple instances of `CharacterTagCompleter` to the new centralized `CharacterCompleter` implementation.

## Overview

The new `CharacterCompleter` class in `app/utils/character_completer.py` provides a centralized implementation of character tag autocompletion that can be used across the application. It includes several improvements:

1. Unified behavior across different contexts
2. Support for both QTextEdit and QLineEdit widgets
3. Optional keyboard shortcut (Ctrl+Space) to show all character suggestions
4. Customizable styling
5. Better positioning and screen boundary awareness
6. Utility functions for handling character references

## Migration Steps

Follow these steps to migrate an existing `CharacterTagCompleter` usage to the new centralized implementation:

### 1. Update imports

Replace:

```python
# No import (or local class definition)
```

With:

```python
from app.utils.character_completer import CharacterCompleter
```

If you're using character reference conversion functions, also import them:

```python
from app.utils.character_completer import (
    CharacterCompleter,
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    extract_character_ids_from_text
)
```

### 2. Replace class instantiation

Replace:

```python
self.tag_completer = CharacterTagCompleter(self)
self.tag_completer.set_characters(self.characters)
self.tag_completer.character_selected.connect(self.insert_character_tag)
self.tag_completer.hide()

# Optional: Install event filter
self.text_edit.installEventFilter(self)

# Optional: Connect to textChanged
self.text_edit.textChanged.connect(self.check_for_character_tag)
```

With:

```python
self.tag_completer = CharacterCompleter(self)
self.tag_completer.set_characters(self.characters)
self.tag_completer.character_selected.connect(self.on_character_selected)
self.tag_completer.attach_to_widget(
    self.text_edit,  # or self.line_edit
    add_shortcut=True,  # Use False to not add Ctrl+Space shortcut
    shortcut_key="Ctrl+Space",  # Customize shortcut if needed
    at_trigger=True  # Set to False to disable @ triggering
)
```

### 3. Update character selection handler

**IMPORTANT**: The new `CharacterCompleter` class emits a signal when a character is selected, but does not automatically insert the tag. You must explicitly call `insert_character_tag` in your signal handler:

```python
def on_character_selected(self, character_name):
    """Handle character selection."""
    # Call the insert_character_tag method to actually insert the tag
    self.tag_completer.insert_character_tag(character_name)

    # Any additional custom logic
    print(f"Character '{character_name}' selected")
```

### 4. Remove redundant methods

The following methods are now handled by the `CharacterCompleter` class and can be removed:

- `check_for_character_tag`
- `check_for_character_tag_line_edit` (if it exists)
- `insert_character_tag` (unless you have custom logic beyond inserting the tag)

Replace any calls to these methods with the corresponding methods in `CharacterCompleter`.

### 5. Update event filter overrides (if present)

If you have custom `eventFilter` overrides that handle Tab key navigation for the completer, you can remove them as the new `CharacterCompleter` handles this internally.

### 6. Replace character reference utilities

Replace any custom code for converting between `@mentions` and `[char:ID]` references with the utility functions from the `character_completer` module:

- `convert_mentions_to_char_refs`
- `convert_char_refs_to_mentions`
- `extract_character_ids_from_text`

### 7. Custom styling (optional)

If you have custom styling for the completer, you can either:

- Use the default styling provided by `CharacterCompleter`
- Apply custom styling using `set_custom_style`:

```python
self.tag_completer.set_custom_style("""
    QListWidget {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #333333;
        border-radius: 5px;
        font-size: 14px;
    }
    /* Add more custom styles here */
""")
```

## Example

Here's an example of a complete migration:

### Before:

```python
class ExampleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize UI
        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self.check_for_character_tag)

        # Create character tag completer
        self.tag_completer = CharacterTagCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.insert_character_tag)
        self.tag_completer.hide()

        # Install event filter
        self.text_edit.installEventFilter(self)

    def check_for_character_tag(self):
        """Check if the user is typing a character tag and provide suggestions."""
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()

        # Find the current word being typed
        pos = cursor.position()
        start = max(0, pos - 1)

        # Check for @ tag
        # ... (more code here)

    def insert_character_tag(self, character_name):
        """Insert a character tag at the current cursor position."""
        cursor = self.text_edit.textCursor()
        text = self.text_edit.toPlainText()
        pos = cursor.position()

        # Find the @ that started this tag
        # ... (more code here)
```

### After:

```python
from app.utils.character_completer import CharacterCompleter

class ExampleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize UI
        self.text_edit = QTextEdit()

        # Create character tag completer
        self.tag_completer = CharacterCompleter(self)
        self.tag_completer.set_characters(self.characters)
        self.tag_completer.character_selected.connect(self.on_character_selected)
        self.tag_completer.attach_to_widget(
            self.text_edit,
            add_shortcut=True,
            shortcut_key="Ctrl+Space",
            at_trigger=True
        )

    def on_character_selected(self, character_name):
        """Handle character selection."""
        # This call is required to insert the tag in the text widget
        self.tag_completer.insert_character_tag(character_name)

        # Any additional custom logic
        print(f"Character '{character_name}' selected")
```

## Testing After Migration

After migrating to the new `CharacterCompleter`, test the following functionality:

1. Typing `@` followed by characters to trigger filtered suggestions
2. Pressing Ctrl+Space to show all suggestions
3. Navigating suggestions with arrow keys and selecting with Enter/Tab
4. Character tag insertion and formatting
5. Any custom behavior that depends on character tag completion

## Note on Multiple Instances

The new design allows you to use different instances of `CharacterCompleter` for different widgets while maintaining consistent behavior. You can customize each instance separately if needed.

## Troubleshooting

If you encounter any issues during migration:

1. Check that the `attach_to_widget` method is being called with the correct widget
2. Verify that `set_characters` is being called with the correct character data
3. Make sure your character selection handler calls `insert_character_tag`
4. Ensure any custom event handling doesn't conflict with the completer's internal handling
5. Check that the signal connections are properly set up

For complex use cases, refer to the `character_completer_example.py` for a complete working example.
