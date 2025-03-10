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
