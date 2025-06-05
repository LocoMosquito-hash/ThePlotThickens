# Video Support in The Plot Thickens

The Plot Thickens now supports video files in the Gallery! This feature allows you to import and manage video files alongside your images.

## 🎬 **Supported Features**

### **Video Import Methods**

- **Import Button**: Use "Import Image/Video" button to browse and select MP4 files
- **Paste from Clipboard**: Copy a video file path and paste it using Ctrl+V or the paste button
- **Drag & Drop**: _(Future enhancement)_

### **Video Formats**

Currently supported video formats:

- **MP4** (primary format)
- **AVI, MOV, MKV, WMV, FLV, WEBM, M4V** (experimental support)

### **Thumbnail Generation**

- **Animated GIF thumbnails** (preferred) - Shows first 2 seconds of video as animated preview
- **Static PNG thumbnails** (fallback) - Single frame extracted from video
- **Automatic scaling** to max 320x320 pixels while preserving aspect ratio
- **Placeholder thumbnails** if video processing fails

## 🛠️ **Setup Requirements**

### **FFmpeg Installation**

Video support requires FFmpeg for thumbnail generation and metadata extraction.

#### **Windows Installation (Recommended)**

1. Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/
2. Download the **"release essentials"** ZIP file (~70-80 MB)
3. Extract to `C:\ffmpeg\`
4. Add `C:\ffmpeg\bin` to your system PATH:
   - Open **Settings** → **System** → **About** → **Advanced system settings**
   - Click **Environment Variables**
   - Find **Path** in **System variables** → **Edit**
   - Click **New** → Add `C:\ffmpeg\bin`
   - Click **OK** to save

#### **Alternative Paths**

The application automatically checks these locations:

- `ffmpeg` in system PATH
- `C:\ffmpeg\bin\ffmpeg.exe`
- `C:\Program Files\ffmpeg\bin\ffmpeg.exe`
- `C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe`

### **Verification**

Run the test script to verify setup:

```bash
python test_video_support.py
```

## 📁 **How Video Files Are Stored**

### **File Organization**

- **Original videos**: Stored in `/story_folder/images/` (same as images)
- **Thumbnails**: Stored in `/story_folder/thumbnails/` as GIF or PNG files
- **Database**: Videos are stored in the same `images` table as regular images

### **File Naming**

- **Video files**: `vid_YYYYMMDDHHMMSS_XXXXXXXX.mp4`
- **Thumbnails**: `vid_YYYYMMDDHHMMSS_XXXXXXXX.gif` (or `.png`)

Where:

- `YYYYMMDDHHMMSS` = timestamp
- `XXXXXXXX` = random string for uniqueness

## 🎯 **How to Use**

### **Method 1: Import Button**

1. Open The Plot Thickens application
2. Select a story
3. Click **"Import Image/Video"** button
4. Browse and select your MP4 file
5. Wait for thumbnail generation
6. Video appears in gallery with animated thumbnail

### **Method 2: Paste from Clipboard**

1. Copy the path to your video file:
   - In File Explorer, right-click the video → **Copy as path**
   - Or manually copy the full path: `C:\path\to\your\video.mp4`
2. In The Plot Thickens gallery, click **"Paste from Clipboard"** or press **Ctrl+V**
3. Video will be imported automatically

### **Method 3: Character Recognition (Future)**

_Character recognition for videos is planned for future releases_

## 🔧 **Technical Details**

### **Thumbnail Generation Process**

1. **Video Analysis**: Extract metadata (duration, dimensions, fps)
2. **GIF Generation**:
   - Extract first 2 seconds of video
   - Generate color palette for optimal quality
   - Create 15fps animated GIF
   - Scale to fit 320x320 max dimensions
3. **Fallback**: If GIF fails, generate static PNG from video frame
4. **Final Fallback**: If all processing fails, create placeholder thumbnail

### **Quality Settings**

- **GIF Frame Rate**: 15 FPS (good balance of quality vs file size)
- **GIF Duration**: 4 seconds from start of video
- **Max Dimensions**: 320x320 pixels (maintains aspect ratio)
- **Color Optimization**: Custom palette generation for better quality

### **Performance**

- **Thumbnail generation**: ~5-15 seconds depending on video size
- **Storage efficiency**: GIF thumbnails are typically 200KB-2MB
- **Memory usage**: Minimal impact on application performance

## 🚨 **Troubleshooting**

### **"FFmpeg not found" Error**

**Problem**: Video thumbnails not generating
**Solution**:

1. Install FFmpeg (see Setup Requirements above)
2. Verify installation: Open Command Prompt and type `ffmpeg -version`
3. Restart The Plot Thickens application

### **Thumbnail Generation Failed**

**Problem**: Videos import but show placeholder thumbnails
**Possible causes**:

- Corrupted video file
- Unsupported codec within MP4 container
- Very short video duration (< 0.5 seconds)
  **Solution**: Try a different video file or check video integrity

### **Large File Sizes**

**Problem**: Application slows down with many video thumbnails
**Solution**:

- Limit number of videos per story
- Consider using shorter video clips
- Thumbnails are automatically optimized but very long videos may create larger GIFs

### **Import Fails Silently**

**Problem**: Video file doesn't appear in gallery
**Check**:

1. File format is MP4
2. File is not corrupted
3. You have write permissions to the story folder
4. Check the application logs for error messages

## 🔮 **Future Enhancements**

### **Planned Features**

- **Video Player Integration**: Click thumbnail to play video in built-in player
- **Additional Format Support**: WEBM, AVI, MOV with broader compatibility
- **Character Recognition**: AI-based character detection in video frames
- **Video Editing**: Basic trim/crop functionality
- **Drag & Drop**: Direct drag-and-drop video import
- **Batch Processing**: Import multiple videos at once

### **Technical Improvements**

- **Background Processing**: Thumbnail generation without blocking UI
- **Progressive Loading**: Show preview while generating full thumbnail
- **Format Conversion**: Automatic conversion to optimized formats
- **Cloud Processing**: Optional cloud-based video processing

## 📝 **Notes**

- **Database Compatibility**: Videos use the same database structure as images
- **Backwards Compatibility**: Existing image functionality unchanged
- **Storage**: Video files are copied (not moved) to story folders
- **Character Tagging**: Currently not supported for videos (future feature)
- **Scene Association**: Videos can be associated with scenes like images

## 🆘 **Getting Help**

If you encounter issues with video support:

1. **Run the test script**: `python test_video_support.py`
2. **Check FFmpeg installation**: `ffmpeg -version` in Command Prompt
3. **Verify file format**: Ensure video is MP4 format
4. **Check logs**: Look for error messages in the application console
5. **Try a different video**: Test with a known-good MP4 file

For additional support, check the main application documentation or create an issue report with:

- Video file details (format, size, duration)
- Error messages from the test script
- Steps you tried before the issue occurred
