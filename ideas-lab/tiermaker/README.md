# Tier Maker - The Plot Thickens

A standalone tier ranking application for characters from your stories, inspired by TierMaker.com.

## Features

- **Template System**: Create reusable tier templates with custom tier names and colors
- **Character Ranking**: Drag and drop characters into different tiers
- **Filtering**: Filter characters by gender and love interest rating
- **Story Integration**: Works with characters from your existing stories in the main database
- **Dark Theme**: Modern dark UI with smooth drag-drop interactions

## Getting Started

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install -r requirements.txt
```

### Running the Application

From the `ideas-lab/tiermaker` directory, run:

```bash
python run.py
```

## How to Use

### 1. Create or Load a Template

- **New Template**: Click "New Template" to create a custom tier template

  - Set a unique template name
  - Customize tier names (S, A, B, C, D by default)
  - Choose colors for each tier
  - Save the template for reuse

- **Load Template**: Click "Load Template" to use an existing template

### 2. Select Characters

- Choose a story from the dropdown
- Apply filters:
  - **Gender**: Filter by specific gender or show all
  - **Min Love Interest**: Set minimum love interest rating (0-10)
- Click "Load Items" to populate the character grid

### 3. Rank Characters

- Drag characters from the bottom grid into the tier rows
- Characters can be reordered within tiers
- Use the "Reset" button to clear all rankings and start over

### 4. Template Settings

- Click the gear icon (⚙) next to any tier for future customization options
- Currently shows a placeholder message

## File Structure

```
tiermaker/
├── models/           # Data models
├── utils/            # Database and utility functions
├── widgets/          # UI components
├── main.py          # Main application window
├── run.py           # Launcher script
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Database

The application uses the same SQLite database as the main Plot Thickens app. It creates two new tables:

- `tier_templates`: Stores template metadata
- `tier_template_tiers`: Stores individual tier configurations

## Future Enhancements

- Save/load tier rankings
- Export tier lists as images
- Support for other item types (images, videos, etc.)
- Template sharing and import/export
- Advanced tier customization options

## Technical Notes

- Built with PyQt6 for the GUI
- Uses drag-drop functionality for intuitive ranking
- Modular architecture for easy extension
- Type hints throughout for better IDE support
- Follows SOLID principles and clean code practices
