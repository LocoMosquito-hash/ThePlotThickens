# Character References Migration Guide

This guide provides a step-by-step approach to migrate all character reference functionality to the new centralized `character_references.py` module.

## Overview

We're replacing multiple duplicate implementations of character reference conversion with a centralized utility module. The key benefits are:

- Consistent handling of character references across the application
- Single place to fix bugs or improve character reference handling
- Clear separation between UI components and utility functions
- Better type hints and documentation

## Migration Steps

### 1. Import the new utility functions

Replace the old imports with:

```python
from app.utils.character_references import (
    convert_mentions_to_char_refs,
    convert_char_refs_to_mentions,
    extract_character_ids,
    find_mentioned_characters,
    process_char_refs_from_db,
    process_quick_event_references
)
```

### 2. Replace `character_completer.py` functions

The existing utility functions in `app/utils/character_completer.py` should be replaced:

| Old Function                    | New Function                    |
| ------------------------------- | ------------------------------- |
| `convert_mentions_to_char_refs` | `convert_mentions_to_char_refs` |
| `convert_char_refs_to_mentions` | `convert_char_refs_to_mentions` |

### 3. Replace database functions in `db_sqlite.py`

| Old Function                         | New Function                                                 |
| ------------------------------------ | ------------------------------------------------------------ |
| `process_character_references`       | `process_quick_event_references`                             |
| `process_quick_event_character_tags` | Use `QuickEventsManager._process_quick_event_character_tags` |

### 4. Replace Timeline Widget functions

In `app/views/timeline_widget.py` and `app/views/timeline_widget_backup.py`:

| Old Function                     | New Function                    |
| -------------------------------- | ------------------------------- |
| `format_character_references`    | `convert_char_refs_to_mentions` |
| `convert_mentions_to_references` | `convert_mentions_to_char_refs` |

### 5. Update UI Components

#### Character Dialog (`app/views/character_dialog.py`)

```python
# Replace
self.initial_text = convert_char_refs_to_mentions(text, self.characters)

# With
from app.utils.character_references import convert_char_refs_to_mentions
self.initial_text = convert_char_refs_to_mentions(text, self.characters)
```

And:

```python
# Replace
return convert_mentions_to_char_refs(display_text, self.characters)

# With
from app.utils.character_references import convert_mentions_to_char_refs
return convert_mentions_to_char_refs(display_text, self.characters)
```

#### Gallery Widget (`app/views/gallery_widget.py`)

Replace custom implementations of `format_display_text` and `convert_mentions_to_char_refs` with the centralized functions.

#### Main Window (`app/views/main_window.py`)

Update the QuickEventDialog to use the new functions.

## Implementation Testing Checklist

After each component is updated, verify that:

- [x] Quick event creation with @mentions works correctly
- [x] Quick event display shows @mentions instead of [char:ID] references
- [x] Editing quick events preserves character references
- [x] Tagged characters are properly associated with quick events
- [x] Timeline events with character references display correctly

## Rollback Plan

In case of issues:

1. Keep the old implementation commented out with a TODO remark
2. Add a flag parameter to use the new implementation vs the old one
3. If critical issues occur, revert to the old implementation

## Migration Sequence

For a smooth transition, follow this sequence:

1. Replace utility functions in `character_completer.py`
2. Update database functions in `db_sqlite.py`
3. Create a `QuickEventsManager` instance for testing
4. Update `timeline_widget.py` functions
5. Update UI components one by one, testing each after update

## Using QuickEventsManager

The new `QuickEventsManager` class handles quick event operations in a centralized way. Here's how to use it:

```python
from app.utils.quick_events_manager import QuickEventsManager

# Create a manager instance
manager = QuickEventsManager(db_conn)

# Create a quick event
quick_event_id = manager.create_quick_event('@John Doe met with @Mary Smith', character_id)

# Get a quick event
quick_event = manager.get_quick_event(quick_event_id)

# Format for display
characters = manager.get_quick_event_tagged_characters(quick_event_id)
formatted_text = manager.format_quick_event_text(quick_event['text'], characters)

# Update a quick event
success = manager.update_quick_event(quick_event_id, '@John Doe met with @Mary Smith and @Robert Johnson')
```

## Common Errors and Solutions

### Missing characters in @mentions conversion

**Problem**: Character names aren't being converted to @mentions

**Solution**: Ensure the characters list contains all necessary characters with proper IDs and names.

### Character references in HTML content

**Problem**: Character references embedded in HTML content might be processed incorrectly

**Solution**: Process only the text content, not any HTML tags.

### References with special characters

**Problem**: Character names with special characters might not be processed correctly

**Solution**: Use the improved regex patterns in the new utility functions that handle special characters.

## Summary

The migration to centralized character reference handling brings more consistency and maintainability to the codebase. By following this guide, we can ensure a smooth transition with minimal disruption to the application's functionality.
