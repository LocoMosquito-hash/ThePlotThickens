# Clipboard Image Viewer

A simple PyQt6 application that allows pasting images from clipboard and displaying them.

## Features

- Paste images directly from clipboard (using Ctrl+V or the "Paste Image" button)
- View images with automatic scaling
- Save images to disk in various formats
- Clear the current image
- Debug clipboard content to identify supported mime types
- Support for file references (when you copy an image file in File Explorer)

## Requirements

- Python 3.6+
- PyQt6

## Installation

1. Make sure you have Python installed on your system
2. Install the required dependencies:

```bash
pip install PyQt6
```

## Usage

1. Run the application:

```bash
python clipboard_image_viewer.py
```

2. Copy an image to your clipboard (e.g., by taking a screenshot or copying an image from another application)
3. In the application, either:
   - Press Ctrl+V
   - Click the "Paste Image" button
4. The image will be displayed in the application
5. You can save the image by clicking the "Save Image" button
6. To clear the current image, click the "Clear" button

### Debugging Clipboard Content

If you're having trouble pasting certain types of images, you can use the debugging functionality:

1. Copy the content you want to analyze to your clipboard
2. Click the "Debug Clipboard" button in the application
3. A detailed report of the clipboard's content will be displayed and saved to `clipboard_debug.log`
4. This information can help identify what mime types are available for handling

## How It Works

The application uses PyQt6's clipboard functionality to access images stored in the system clipboard. When an image is pasted, it's displayed in a scrollable area that automatically scales the image to fit the window while maintaining its aspect ratio.

The debug functionality examines all available mime types in the clipboard and logs detailed information about each format, which can be used to extend support for additional image formats.

## License

This project is open source and available under the MIT License.
