# Character Completer Module

This module provides a centralized implementation of character tagging and autocompletion for "The Plot Thickens" application. It replaces the multiple duplicate implementations of `CharacterTagCompleter` with a single, reusable component.

## Features

- **Unified Character Tagging**: Consistent tagging behavior across all text components
- **Flexible Widget Support**: Works with both `QTextEdit` and `QLineEdit` widgets
- **Trigger Options**: Can be triggered by typing '@' or a configurable keyboard shortcut
- **Customizable Styling**: Default styling with option for custom appearance
- **Smart Positioning**: Auto-positions the suggestion popup based on cursor location and screen boundaries
- **Keyboard Navigation**: Arrow keys, Enter, Tab, and Escape key support
- **Utility Functions**: Conversion between @mentions and [char:ID] format

## Module Contents

- `CharacterCompleter`: Main class for character tag autocompletion
- `convert_mentions_to_char_refs`: Convert @mentions to [char:ID] format
- `convert_char_refs_to_mentions`: Convert [char:ID] to @mentions
- `extract_character_ids_from_text`: Extract character IDs from text containing [char:ID] references

## Installation

The module is part of the application and doesn't require separate installation.

## Basic Usage

```python
from app.utils.character_completer import CharacterCompleter

# Create a character completer
self.completer = CharacterCompleter(parent_widget)

# Set the character data
self.completer.set_characters(character_list)

# Connect to handle selection (optional)
self.completer.character_selected.connect(self.on_character_selected)

# Attach to a text widget
self.completer.attach_to_widget(
    self.text_edit,  # can be QTextEdit or QLineEdit
    add_shortcut=True,  # enable Ctrl+Space shortcut
    shortcut_key="Ctrl+Space",  # customize shortcut if needed
    at_trigger=True  # enable @ character triggering
)
```

## Character Data Format

The character data should be a list of dictionaries, where each dictionary represents a character and must contain at least `id` and `name` keys:

```python
characters = [
    {"id": 1, "name": "Sherlock Holmes"},
    {"id": 2, "name": "John Watson"},
    # more characters...
]
```

## Customization Options

### Custom Styling

```python
# Apply custom styling to the completer popup
completer.set_custom_style("""
    QListWidget {
        background-color: #2D2D30;
        color: #F0F0F0;
        border: 1px solid #3F3F46;
        border-radius: 3px;
        font-size: 14px;
    }
    QListWidget::item {
        padding: 5px;
    }
    QListWidget::item:selected {
        background-color: #007ACC;
    }
""")
```

### Keyboard Shortcut

```python
# Use a different keyboard shortcut to show suggestions
completer.attach_to_widget(
    text_widget,
    add_shortcut=True,
    shortcut_key="Alt+Space"  # Change to Alt+Space
)
```

### Disable @ Triggering

```python
# Only allow showing suggestions via keyboard shortcut
completer.attach_to_widget(
    text_widget,
    add_shortcut=True,
    at_trigger=False  # Disable @ triggering
)
```

## Handling Character Selection

```python
def on_character_selected(self, character_name):
    """Handle when a character is selected from the suggestions."""
    print(f"Selected character: {character_name}")
    # Add any custom logic here
```

## Working with Character References

```python
from app.utils.character_completer import (
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    extract_character_ids_from_text
)

# Convert @mentions to [char:ID] format
text = "Hello @Sherlock Holmes and @John Watson!"
converted = convert_mentions_to_char_refs(text, characters)
# Result: "Hello [char:1] and [char:2]!"

# Convert [char:ID] back to @mentions
text = "Hello [char:1] and [char:2]!"
converted = convert_char_refs_to_mentions(text, characters)
# Result: "Hello @Sherlock Holmes and @John Watson!"

# Extract character IDs from text
text = "Hello [char:1] and [char:2]!"
ids = extract_character_ids_from_text(text)
# Result: [1, 2]
```

## Example

See the `character_completer_example.py` file for a complete working example of the `CharacterCompleter` in action.

## Migration

For guidance on migrating existing `CharacterTagCompleter` instances to the new centralized implementation, see the `character_completer_migration.md` file.

## Best Practices

- Create a single instance of `CharacterCompleter` for each text widget
- Update character data with `set_characters()` whenever characters change
- Use the utility functions to standardize character reference handling
- Connect to the `character_selected` signal if you need custom behavior beyond inserting the tag

## Troubleshooting

- If suggestions don't appear when typing '@', check that `at_trigger=True` is set
- If the keyboard shortcut doesn't work, verify the shortcut key is valid and `add_shortcut=True` is set
- If character selection doesn't insert the tag, check that the widget is properly attached
- If styling looks incorrect, try using `set_custom_style()` to customize the appearance
