# Story Board Technical Documentation

This document provides technical details about the Story Board implementation for developers.

## Architecture

The Story Board is implemented using PyQt6's Graphics View Framework, which provides a scene-view architecture for visualizing and interacting with graphical items.

### Key Classes

- **StoryBoardWidget**: Main widget that contains the view, scene, and controls
- **StoryBoardView**: Custom QGraphicsView that handles zooming and navigation
- **StoryBoardScene**: Custom QGraphicsScene that manages character cards and relationships
- **CharacterCard**: Custom QGraphicsItemGroup representing a character
- **RelationshipLine**: Custom QGraphicsLineItem representing a relationship between characters

## Data Flow

1. **Loading a Story**:

   - `StoryBoardWidget.set_story()` is called with a story ID
   - Views for the story are loaded from the database
   - If no views exist, a default view is created

2. **Loading a View**:

   - `StoryBoardWidget.load_view()` is called with a view ID
   - View data is retrieved from the database
   - Character cards are created and positioned according to the layout data
   - Relationship lines are created based on relationships in the database

3. **Saving a View**:
   - `StoryBoardWidget.save_current_view()` is called
   - Layout data is collected from the scene using `StoryBoardScene.get_layout_data()`
   - The layout data is saved to the database

## Database Interaction

The Story Board interacts with the database through several functions in `db_sqlite.py`:

- `get_story_board_views()`: Retrieves all views for a story
- `get_story_board_view()`: Retrieves a specific view
- `create_story_board_view()`: Creates a new view
- `update_story_board_view_layout()`: Updates the layout of a view
- `get_story_characters()`: Retrieves all characters for a story
- `get_story_relationships()`: Retrieves all relationships for a story
- `create_relationship()`: Creates a new relationship
- `get_relationship_types()`: Retrieves standard relationship types
- `get_used_relationship_types()`: Retrieves custom relationship types that have been used

## Layout Data Format

The layout data is stored as a JSON string in the database. The format is:

```json
{
  "characters": {
    "1": {"x": 100, "y": 200},
    "2": {"x": 300, "y": 400},
    ...
  }
}
```

Where the keys in the "characters" object are character IDs, and the values are objects containing x and y coordinates.

## Character Cards

Character cards are implemented as `QGraphicsItemGroup` objects, which group several graphical items:

- Background rectangle (white card)
- Shadow effect
- Red pin at the top
- Photo area
- Character image (if available)
- Character name
- "MC" indicator (if applicable)

## Relationship Lines

Relationship lines are implemented as `QGraphicsLineItem` objects with additional features:

- A text label showing the relationship type
- A semi-transparent background for the label
- Hover effects (thicker line, lighter color, larger font)
- Context menu for editing

The lines connect to the red pins at the top of character cards, creating a visual effect similar to threads on a detective's board.

## Event Handling

- **Moving Character Cards**: When a card is moved, all connected relationship lines are updated
- **Saving Layout**: Changes to the layout are saved automatically after a short delay
- **Hover Events**: Relationship lines respond to hover events to provide visual feedback
- **Context Menus**: Both character cards and relationship lines have context menus for additional actions

## Relationship Dialog

The relationship dialog is a custom dialog that:

1. Retrieves both standard and previously used relationship types
2. Combines them into a single list with previously used types at the top
3. Provides autocomplete functionality for easier selection
4. Handles both existing and custom relationship types

## Performance Considerations

- Character positions are updated efficiently to avoid unnecessary redraws
- Relationship lines are updated only when necessary
- The view is centered and scaled to show all characters without manual adjustment
- Hover effects use lightweight visual changes to maintain performance

## Future Enhancements

- Implement character editing and deletion
- Implement relationship editing and deletion
- Add support for relationship history (changes over time)
- Improve visual representation of different relationship types
- Add support for grouping characters
