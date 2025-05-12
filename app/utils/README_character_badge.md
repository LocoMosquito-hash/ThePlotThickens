# Character Badge System

The Character Badge system provides a standardized way to display character information throughout The Plot Thickens application.

## Overview

Character badges offer a visually consistent way to represent characters across different parts of the application. They can be customized in size, style, and content to fit various use cases.

## Features

- Display character avatar or auto-generated initials
- Show character name
- Indicate main character status
- Add custom status icons with tooltips
- Interactive with click events
- Customize appearance with different sizes and styles
- Consistent coloring based on character name

## Usage

### Basic Usage

```python
from app.utils import create_character_badge, CharacterBadge

# Create a badge with default settings (medium size, outlined style)
badge = create_character_badge(
    character_id=1,
    character_data=character_dict
)

# Add the badge to your layout
layout.addWidget(badge)

# Connect to click events
badge.clicked.connect(lambda char_id: handle_character_click(char_id))
```

### Size Options

Choose from predefined sizes based on your needs:

```python
# Tiny badge (24x24) - Just the avatar
tiny_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    size=CharacterBadge.SIZE_TINY
)

# Small badge (32x32) - Avatar with minimal text
small_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    size=CharacterBadge.SIZE_SMALL
)

# Medium badge (48x48) - Default
medium_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    size=CharacterBadge.SIZE_MEDIUM
)

# Large badge (64x64) - Avatar with name and basic icons
large_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    size=CharacterBadge.SIZE_LARGE
)

# Extra large badge (96x96) - Full featured
xlarge_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    size=CharacterBadge.SIZE_XLARGE
)
```

### Style Options

Choose from different visual styles:

```python
# Flat style - No borders, transparent background
flat_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    style=CharacterBadge.STYLE_FLAT
)

# Outlined style - Thin border, transparent background (default)
outlined_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    style=CharacterBadge.STYLE_OUTLINED
)

# Filled style - Background fill with border
filled_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    style=CharacterBadge.STYLE_FILLED
)

# Shadowed style - With drop shadow for depth
shadowed_badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    style=CharacterBadge.STYLE_SHADOWED
)
```

### Adding Status Icons

Add custom status icons to convey additional information:

```python
# Create a badge
badge = create_character_badge(
    character_id=1,
    character_data=character_dict,
    size=CharacterBadge.SIZE_LARGE
)

# Add a status icon for a deceased character
badge.add_status_icon(
    icon_name="ghost",
    tooltip="Deceased Character",
    color="#777777"  # Grey color
)

# Add a status icon for an archived character
badge.add_status_icon(
    icon_name="archive",
    tooltip="Archived Character",
    color="#555555"
)

# Add an icon with a click handler
def on_edit_clicked(character_id, icon_name):
    print(f"Edit clicked for character {character_id}")
    open_character_editor(character_id)

badge.add_status_icon(
    icon_name="edit",
    tooltip="Edit Character",
    color="#0000FF",
    on_click=on_edit_clicked
)
```

### Dynamic Updates

Update badge content when character data changes:

```python
# Create a badge
badge = create_character_badge(
    character_id=1,
    character_data=character_dict
)

# Later, update the badge with new data
character_dict["name"] = "New Name"
character_dict["is_main_character"] = True
badge.update_from_data(character_dict)
```

### Example Use Cases

1. **Character Lists**: Use small badges to create compact character lists
2. **Character Selection**: Use medium badges for character selection dropdowns
3. **Story Board**: Use large badges for character cards on the story board
4. **Character References**: Use tiny badges for inline character references in text
5. **Timeline/Events**: Use badges to indicate character involvement in events

## Integration with Tabler Icons

The badge system integrates with the application's Tabler icon system. Any icon available through the icon manager can be used as a status icon.

## Performance Considerations

For lists with many characters, consider using smaller badge sizes and fewer status icons to improve performance. The badge system uses caching for colors and icons to minimize resource usage.

## Example Application

See `app/utils/character_badge_example.py` for a comprehensive demonstration of badge capabilities.
