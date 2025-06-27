# Window Selector - Experimental Tool

A PyQt6-based experimental application for listing and interacting with visible windows on Windows 11.

## Purpose

This tool is designed to explore window capture capabilities, including:

- Enumerating visible windows
- Capturing window properties
- **Screenshots of client areas** (new!)
- Future extensions for sending keystrokes and other window interactions

## Features

- **Window Enumeration**: Lists all visible windows with their titles and associated process names
- **Real-time Refresh**: Manual refresh button to update the window list
- **Detailed Properties**: Extended window information including position, size, state, and technical details
- **Client Area Screenshots**: Capture screenshots of the content area (excluding title bars and borders)
- **Tabbed Interface**: Organized workflow with dedicated tabs for different functions
- **Smart Error Handling**: Comprehensive error messages and state validation

## Requirements

- Windows 11 (Windows-specific implementation)
- Python 3.8+
- PyQt6
- pywin32
- psutil
- Pillow (PIL)

## Installation

1. Navigate to the window-selector directory:

   ```powershell
   cd ideas-lab\window-selector
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

Run the application using:

```powershell
python run.py
```

Or directly:

```powershell
python main.py
```

## Current Functionality

### Window Properties Tab (Main)

- **Select Window Button**: Navigate to window picker
- **Detailed Information Display**: Shows comprehensive window properties including:
  - Basic info: Title, process name, process ID, window handle
  - Position & Size: Window bounds and client area dimensions
  - Window State: Visibility, minimized status, enabled state
  - Technical Info: Window class name

### Window Picker Tab

- **Window List**: Displays visible windows in a two-column table
  - Column 1: Window Title
  - Column 2: Process Name (executable)
- **Auto-refresh**: Updates automatically when navigating to this tab
- **Double-click Selection**: Choose windows and return to Properties tab

### Screenshots Tab (New!)

- **Client Area Capture**: Screenshots only the content area (no title bars/borders)
- **Smart State Validation**: Checks for window existence, visibility, and minimized state
- **Scaled Display**: Images scale to fit while maintaining aspect ratio
- **Comprehensive Error Handling**: Detailed error messages for various failure scenarios
- **Status Updates**: Real-time feedback during capture process

## Workflow

1. **Start** on the "Window Properties" tab
2. **Click "Select Window..."** → switches to "Window Picker" tab
3. **Double-click any window** → returns to "Window Properties" with detailed info
4. **Navigate to "Screenshots" tab** → capture client area screenshots of selected window

## Advanced Features

- **Client Area Focus**: Screenshots capture only the window content, excluding decorations
- **State Management**: Automatic updates across tabs when windows are selected
- **Error Recovery**: Graceful handling of window state changes and access issues

## Future Extensions

This foundation supports experimenting with:

- Window positioning and manipulation
- Sending keystrokes to selected windows
- Advanced screenshot options
- Window interaction automation

## Architecture

- `main.py`: Core application with tabbed interface and window interaction logic
- `run.py`: Simple execution script
- `requirements.txt`: Project dependencies including new image processing requirements

The code uses proper type hints, comprehensive error handling, and follows PyQt6 best practices for maintainable, extensible development.
