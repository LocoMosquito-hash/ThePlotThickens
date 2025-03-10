# Story Board Documentation

## Overview

The Story Board is a visual representation of characters and their relationships, designed to resemble a detective's investigation board. It allows you to:

- Visualize characters as cards with images and basic information
- Create and manage relationships between characters
- Organize characters spatially to represent story dynamics
- Save multiple views of the same story with different layouts

## Character Cards

Character cards represent individual characters in your story. Each card includes:

- Character name
- Character image (if available)
- "MC" indicator for main characters
- A red pin at the top for attaching relationship threads

### Interacting with Character Cards

- **Move**: Click and drag a card to reposition it on the board
- **Select**: Click on a card to select it
- **Context Menu**: Right-click on a card to access additional options:
  - Edit Character (not yet implemented)
  - Delete Character (not yet implemented)
  - Add Relationship: Create a relationship to another character

## Character Relationships

Relationships represent connections between characters. They are visualized as threads connecting the red pins on character cards.

### Creating Relationships

1. Right-click on a character card
2. Select "Add Relationship" from the context menu
3. Choose the target character from the submenu
4. In the dialog that appears:
   - Select an existing relationship type from the dropdown
   - Or type a new relationship type
   - The dropdown features autocomplete and shows previously used types first

### Relationship Features

- **Visual Representation**: Relationships appear as threads connecting character pins
- **Labels**: Each relationship displays its type (e.g., "Roomie") on the thread
- **Hover Effects**: When you hover over a relationship:
  - The thread becomes thicker
  - The color becomes lighter
  - The label becomes more prominent
  - The relationship is brought to the front

### Managing Relationships

- **Context Menu**: Right-click on a relationship thread to:
  - Edit Relationship (not yet implemented)
  - Change Color: Select a new color for the relationship
  - Change Width: Adjust the thickness of the thread
  - Delete Relationship (not yet implemented)

### Bidirectional Relationships

When creating a relationship, you may be prompted to create an inverse relationship:

- If you set Character A as "Father" of Character B, you'll be asked if Character B is "Son" or "Daughter" of Character A
- This helps maintain logical consistency in your character relationships
- You can accept or decline the suggested inverse relationship

## Views

The Story Board supports multiple views of the same story, allowing different arrangements of characters.

### Managing Views

- **View Selector**: Use the dropdown at the top to switch between views
- **New View**: Create a new arrangement of characters
- **Save View**: Save the current arrangement of characters
- **Reset Positions**: Arrange characters in a grid layout
- **Position Cards**: Restore character positions from the saved layout

## Navigation

- **Zoom In/Out**: Use the buttons to adjust the zoom level
- **Reset Zoom**: Return to the default zoom level
- **Center View**: The view automatically centers on the characters

## Tips for Effective Use

1. **Organize Spatially**: Position characters to represent their relationships in the story
2. **Use Consistent Relationship Types**: The autocomplete feature helps maintain consistency
3. **Create Multiple Views**: Use different views to represent different aspects of your story
4. **Save Frequently**: Use the "Save View" button to preserve your work
5. **Use Hover**: Hover over relationships to highlight them when the board becomes complex

## Technical Notes

- Character positions are saved per view
- Relationship types are stored globally and can be reused across stories
- Custom relationship types are remembered for future use
- The Story Board automatically adjusts to show all characters
