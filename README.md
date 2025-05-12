# The Plot Thickens

A desktop application for managing and visualizing complex narratives across multiple media formats.

## Overview

"The Plot Thickens" is a GUI-based application designed to help you keep track of characters, events, and details across various stories. Whether you're following TV series, movies, visual novels, or games, this tool helps you visualize and organize complex narratives.

## Features

- **Story Management**: Create and organize stories by type (TV Series, Movie, Game, Visual Novel)
- **Character Tracking**: Add and manage characters with detailed attributes
- **Relationship Visualization**: Map out character relationships on an interactive story board
- **Multiple Views**: Save different arrangements of characters for different aspects of a story
- **Visual Interface**: Intuitive drag-and-drop interface for organizing characters

## Getting Started

### Prerequisites

- Python 3.8 or higher
- PyQt6

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/ThePlotThickens.git
   cd ThePlotThickens
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python run.py
   ```

## Usage

### Creating a Story

1. Launch the application
2. Go to File > New Story
3. Enter story details and select a type
4. Click "Create"

### Adding Characters

1. Open a story
2. Navigate to the Story Manager tab
3. Click "Add Character"
4. Fill in character details and click "Save"

### Visualizing Relationships

1. Open a story
2. Navigate to the Story Board tab
3. Right-click on a character card
4. Select "Add Relationship" and choose another character
5. Specify the relationship type

## Documentation

For more detailed information, see the documentation:

- [User Guide](docs/user_guide.md)
- [Story Board](docs/story_board.md)
- [Technical Documentation](docs/technical/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the need to keep track of complex narratives across multiple media
- Built with PyQt6 for a native desktop experience

# The Plot Thickens - Icon System

This document describes the icon system used in The Plot Thickens application.

## Overview

The icon system is built on top of the [Tabler Icons](https://tabler-icons.io/) library, which provides a comprehensive set of high-quality SVG icons. The application supports two different implementations:

1. **pytablericons** (preferred) - Uses Pillow for rendering icons
2. **tabler-qicon** (alternative) - Direct QIcon implementation

If neither of these packages is available, the system falls back to using Qt's built-in standard icons.

## Features

- **Multiple Icon Implementations**: Support for both pytablericons and tabler-qicon packages
- **Consistent Icon Styling**: All icons follow the application's theme (light or dark)
- **Theme-aware**: Icons automatically adjust when the application theme changes
- **Fallback Mechanism**: If no Tabler Icons package is available, the system falls back to Qt's built-in standard icons
- **Icon Caching**: Frequently used icons are cached for performance
- **Centralized Management**: All icons are accessed through a single manager class

## Usage

### Basic Usage

To use an icon in your PyQt6 component, import the icon manager and call the `get_icon` method:

```python
from app.utils.icons import icon_manager

# In your UI setup code:
button = QPushButton()
button.setIcon(icon_manager.get_icon("settings"))
```

### Available Icons

Tabler Icons provides over 5,000 icons. You can browse the available icons at [tabler-icons.io](https://tabler-icons.io/).

When using an icon, convert the name to lowercase and replace hyphens with underscores:

- `arrow-down` → `arrow_down`
- `circle-check` → `circle_check`

### Commonly Used Icons

Some commonly used icons in the application:

- `home` - Home navigation
- `settings` - Application settings
- `edit` - Edit content
- `trash` - Delete items
- `plus` - Add new items
- `check` - Confirm or complete
- `x` - Cancel or close
- `info_circle` - Information
- `alert_triangle` - Warning
- `refresh` - Refresh content
- `sun`/`moon` - Light/dark theme toggle

### Theme-Aware Icons

Icons automatically adjust to the current application theme. The default colors are:

- Dark theme: White icons (#FFFFFF)
- Light theme: Black icons (#000000)

## Implementation Details

The icon system is implemented in the `app/utils/icons` package:

- `icon_manager.py` - The main manager class that provides access to icons
- `__init__.py` - Exposes the icon_manager singleton instance
- `icon_example.py` - An example application showing available icons

The `IconManager` class provides these key methods:

- `get_icon(icon_name)` - Get an icon by name
- `set_theme(theme)` - Set the theme for icons ("dark" or "light")
- `get_all_icon_names()` - Get a list of all available icon names

## Testing the Icon System

You can run the icon example to see available icons and test the theme toggle:

```
python -m app.utils.icons.icon_example
```

## Icon Library Selection

The application will use the available icon libraries in the following priority order:

1. **pytablericons** - If available, this is the preferred option
2. **tabler-qicon** - Used if pytablericons is not available
3. **Qt Standard Icons** - Fallback if neither of the above is available

## Requirements

The icon system requires:

- PyQt6
- At least one of:
  - pytablericons package (preferred)
  - tabler-qicon package (alternative)

If neither package is available, the system will fall back to using Qt's built-in standard icons.
