# Video Conversion Lab

A PyQt6-based GUI application for experimenting with video format conversions and quality settings. Perfect for testing different video formats and comparing their quality and file sizes.

## Features

### Input Methods

- **Drag & Drop**: Simply drag video files into the application window
- **File Browser**: Use the "Browse..." button to select files from the file system
- **Paste Path**: Copy a file path to clipboard and use "Paste Path" button
- **Remembers Last Directory**: The file browser remembers your last used directory

### Supported Formats

- **Input**: MP4, AVI, MOV, MKV, WMV, FLV, WEBM
- **Output**: GIF, WEBP, MP4 (H.264), MP4 (H.265)

### Quality Levels

- **Medium**: Balanced compression for smaller file sizes
- **High**: Better quality with moderate compression
- **Lossless**: Maximum quality with minimal compression

### Real-time Preview

- Grid layout showing original + 4 converted formats
- Auto-looping video playback (muted by default)
- File size display for each format
- Side-by-side comparison

## Prerequisites

### Required Software

1. **Python 3.10+**
2. **FFmpeg** - Must be installed and available in system PATH
   - Windows: Download from https://ffmpeg.org/download.html
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg` (Ubuntu/Debian)

### Python Dependencies

```bash
pip install -r video_conversion_requirements.txt
```

## Installation & Setup

1. **Navigate to the ideas-lab folder**:

   ```bash
   cd ideas-lab
   ```

2. **Install dependencies**:

   ```bash
   pip install -r video_conversion_requirements.txt
   ```

3. **Verify FFmpeg installation**:
   ```bash
   ffmpeg -version
   ```

## Usage

### Starting the Application

```bash
python video_conversion_lab.py
```

### Basic Workflow

1. **Load a video file** using one of these methods:

   - Drag & drop a video file into the window
   - Click "Browse..." to select a file
   - Copy a file path and click "Paste Path"

2. **Select quality level** from the dropdown:

   - Medium, High, or Lossless

3. **Click "Convert All Formats"** to start conversion

4. **View results** in the preview grid:
   - Original video plays in the first cell
   - Converted formats appear as they complete
   - File sizes are displayed below each preview

### Quality Settings Details

The application shows detailed quality settings for each format:

#### GIF Settings

- **Medium**: 10 fps, 480p scale
- **High**: 15 fps, 720p scale
- **Lossless**: 24 fps, original scale

#### WEBP Settings

- **Medium**: Quality 75, default preset
- **High**: Quality 90, photo preset
- **Lossless**: Quality 100, lossless preset

#### MP4 H.264 Settings

- **Medium**: CRF 28, medium preset
- **High**: CRF 20, slow preset
- **Lossless**: CRF 0, veryslow preset

#### MP4 H.265 Settings

- **Medium**: CRF 32, medium preset
- **High**: CRF 24, slow preset
- **Lossless**: CRF 0, veryslow preset

## Technical Details

### Architecture

- **Main Thread**: UI and user interactions
- **Worker Thread**: Video conversion using FFmpeg
- **QMediaPlayer**: Real-time video preview with auto-looping
- **QSettings**: Persistent settings (window geometry, last directory)

### File Management

- Temporary files are created in a system temp directory
- All temp files are automatically cleaned up on application exit
- Original files are never modified

### Error Handling

- FFmpeg availability check on startup
- Individual format conversion error handling
- User-friendly error messages
- Graceful degradation if conversions fail

## Troubleshooting

### Common Issues

1. **"FFmpeg not found" error**:

   - Ensure FFmpeg is installed and in your system PATH
   - Test with `ffmpeg -version` in terminal

2. **Video won't load**:

   - Check if the file format is supported
   - Ensure the file isn't corrupted
   - Try a different video file

3. **Conversion fails**:

   - Check the quality settings info panel for details
   - Some codecs may not be available in your FFmpeg build
   - Try a different quality level

4. **Preview not playing**:
   - Ensure PyQt6 multimedia components are installed
   - Check if the converted file was created successfully

### Performance Notes

- Short videos (< 10 seconds) convert quickly
- Lossless quality takes significantly longer
- H.265 encoding is slower than H.264
- Multiple conversions run sequentially, not in parallel

## Extending the Lab

### Adding New Formats

1. Add format to `formats_to_convert` list in `ConversionWorker`
2. Add conversion logic in `_convert_format()` method
3. Add quality settings in `_get_quality_settings()` method
4. Add preview widget to the UI grid

### Customizing Quality Settings

Edit the settings dictionary in `_get_quality_settings()` method to adjust:

- Bitrates and CRF values
- Encoding presets
- Frame rates and scaling
- Codec-specific parameters

## Use Cases

- **Format Comparison**: Compare file sizes and quality across formats
- **Quality Testing**: Find optimal settings for your use case
- **Codec Evaluation**: Test H.264 vs H.265 performance
- **GIF Optimization**: Find best settings for animated GIFs
- **WEBP Evaluation**: Test WEBP as video alternative

## Future Enhancements

Potential improvements for future versions:

- Batch processing multiple files
- Custom quality parameter input
- Export settings profiles
- Performance benchmarking
- Audio codec options
- Subtitle handling
- Frame extraction tools
