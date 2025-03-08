# The Plot Thickens

A GUI-based application designed to manage and map out complex narratives across multiple media formats.

## Features

- **Story Management**: Create, edit, and organize your stories
- **Character Visualization**: Map out character relationships and interactions on an interactive story board
- **Customizable Folder Structure**: Configure where your story data is stored
- **Media Integration**: Support for various media formats (visual novels, TV series, movies, games)

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/ThePlotThickens.git
   cd ThePlotThickens
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application:

```
python run.py
```

## Getting Started

1. Launch the application
2. Go to Settings → Preferences to set your User Folder
3. Create a new story in the Story Manager tab
4. Fill in the story details and save
5. Switch to the Story Board tab to start mapping out your narrative

## Folder Structure

The application uses the following folder structure:

- `[USER FOLDER]` - The main folder you select in Settings
  - `Stories/` - Contains all your stories
    - `images/` - Shared images across stories
    - `Story_Name_ID/` - Individual story folder (named with story title and ID)
      - `images/` - Images specific to this story

## Requirements

- Python 3.8 or higher
- PyQt6
- SQLite (included with Python)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Project Structure

- `app/` - Main application code
  - `models/` - Data models
  - `views/` - UI components
  - `utils/` - Utility functions
- `project-resources/` - Project documentation and resources
- `ideas-lab/` - Contains proof-of-concept applications and experimental features
- `venv/` - Python virtual environment (not included in repository)
- `run.py` - Script to run the application

## Setup

### Setting up the Virtual Environment

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:

   - Windows (PowerShell):
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (Command Prompt):
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Development

This project is under active development. Key features include:

- Story management with customizable metadata
- Character relationship visualization
- Configurable data storage location
- Dark theme UI
