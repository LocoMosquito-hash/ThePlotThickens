# QuickEventsManager Documentation

The `QuickEventsManager` class provides a centralized way to handle Quick Events operations in "The Plot Thickens" application. It eliminates duplicate code and brings consistency to character references within quick events.

## Features

- Create, read, update, and delete quick events
- Process character tags and references automatically
- Associate quick events with scenes and images
- Consistent character reference handling
- Proper error handling and type hints

## Usage

### Basic Setup

```python
from app.utils.quick_events_manager import QuickEventsManager

# Create an instance with your database connection
manager = QuickEventsManager(db_conn)
```

### Creating Quick Events

```python
# Create a new quick event with character references
text = "@John Doe met with @Mary Smith at the park"
character_id = 1  # Owner character ID
sequence_number = 0  # Optional sequence number

# The manager automatically handles:
# 1. Converting @mentions to [char:ID] format
# 2. Processing character tags
# 3. Creating character associations
quick_event_id = manager.create_quick_event(text, character_id, sequence_number)
```

### Reading Quick Events

```python
# Get a single quick event
quick_event = manager.get_quick_event(quick_event_id)

# Get all quick events for a character (both owned and tagged)
character_events = manager.get_character_quick_events(character_id)

# Get tagged characters for a quick event
tagged_characters = manager.get_quick_event_tagged_characters(quick_event_id)

# Format quick event text for display (convert [char:ID] to @mentions)
formatted_text = manager.format_quick_event_text(quick_event['text'], tagged_characters)
```

### Updating Quick Events

```python
# Update a quick event
text = "@John Doe met with @Mary Smith and @Robert Johnson at the park"
success = manager.update_quick_event(quick_event_id, text)

# Or just update the sequence number
success = manager.update_quick_event(quick_event_id, sequence_number=5)
```

### Managing Associations

```python
# Associate with a scene
success = manager.associate_quick_event_with_scene(quick_event_id, scene_event_id)

# Remove from a scene
success = manager.remove_quick_event_from_scene(quick_event_id, scene_event_id)

# Get quick events for a scene
scene_events = manager.get_scene_quick_events(scene_event_id)

# Get quick events for an image
image_events = manager.get_image_quick_events(image_id)
```

### Deleting Quick Events

```python
success = manager.delete_quick_event(quick_event_id)
```

## Migration Examples

### Example 1: Character Dialog Quick Events Tab

Before:

```python
def add_quick_event(self):
    """Add a new quick event."""
    # Get text from dialog
    text = dialog.get_text()

    # Create the quick event
    quick_event_id = create_quick_event(
        self.db_conn,
        text,
        self.character_id,
        sequence_number
    )

    # Reload the events
    self.load_quick_events()
```

After:

```python
def add_quick_event(self):
    """Add a new quick event."""
    # Get text from dialog
    text = dialog.get_text()

    # Create the quick event using the manager
    manager = QuickEventsManager(self.db_conn)
    quick_event_id = manager.create_quick_event(
        text,
        self.character_id,
        sequence_number
    )

    # Reload the events
    self.load_quick_events()
```

### Example 2: Displaying Quick Events

Before:

```python
# Get the quick event
quick_event = get_quick_event(self.db_conn, event_id)

# Get tagged characters
tagged_chars = get_quick_event_tagged_characters(self.db_conn, event_id)

# Format the text for display
display_text = format_character_references(quick_event['text'], tagged_chars)
```

After:

```python
# Use the manager for all operations
manager = QuickEventsManager(self.db_conn)

# Get the quick event
quick_event = manager.get_quick_event(event_id)

# Get tagged characters
tagged_chars = manager.get_quick_event_tagged_characters(event_id)

# Format the text for display
display_text = manager.format_quick_event_text(quick_event['text'], tagged_chars)
```

## Best Practices

1. **Create a single manager instance** for related operations to reduce database connections
2. **Use the manager's formatting method** instead of directly calling the character reference functions
3. **Let the manager handle character tag processing** rather than doing it manually
4. **Check return values** for error conditions
5. **Use the proper sequence numbers** to maintain ordering

## Error Handling

The `QuickEventsManager` handles most common errors internally and provides meaningful return values:

- For retrieval methods, an empty dictionary or list is returned if nothing is found
- For update/delete methods, a boolean is returned indicating success
- For creation methods, the new ID is returned, or an exception is raised for critical errors

## Performance Considerations

- The manager efficiently handles database operations
- Character reference processing is optimized for speed
- Consider batching operations when working with many quick events
