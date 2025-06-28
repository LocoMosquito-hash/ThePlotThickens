# Global Hotkey Feature - Background Screenshot Capture

## Overview

The Window Selector now supports **global hotkey monitoring** that allows you to capture screenshots while playing games or using other applications without switching windows. This feature uses the **INSERT key** as a global trigger.

## Key Features

### ✅ **Background Operation**

- **No window switching required** - Stay in your game/application
- **Global INSERT key monitoring** - Works system-wide
- **Automatic target detection** - Only triggers when target window is active
- **Non-disruptive workflow** - Seamless screenshot capture

### ✅ **Full Renpy Integration**

- **Automatic dialogue hiding** - Sends 'H' key if checkbox enabled
- **Smart timing** - Optimized delays for responsive operation
- **Clean screenshots** - Dialogue hidden/restored automatically

### ✅ **Production-Ready**

- **Error handling** - Graceful fallbacks and user feedback
- **Status monitoring** - Real-time feedback on hotkey status
- **Easy controls** - Start/stop monitoring with buttons

## User Workflow

### **Setup Phase:**

1. **Launch Window Selector**
2. **Navigate to Window Properties tab**
3. **Select target window** (your game/application)
4. **Go to Screenshots tab**
5. **Enable Renpy checkbox** if using with visual novels
6. **Click "🚀 Start Global Monitoring"**

### **Usage Phase:**

1. **Switch to your game/application**
2. **Play normally** - Window Selector runs in background
3. **Press INSERT key** when you want a screenshot
4. **Screenshot captured automatically** with dialogue hidden (if enabled)
5. **Continue playing** - No interruption to workflow

### **Cleanup:**

- **Click "⏹️ Stop Monitoring"** when done
- Or simply close Window Selector

## Technical Implementation

### **Libraries Used:**

- **`global-hotkeys`** - System-wide hotkey monitoring
- **`win32gui`** - Active window detection
- **Existing automation** - Renpy dialogue hiding system

### **Architecture:**

```
GlobalHotkeyMonitor (QThread)
├── INSERT key detection (global)
├── Active window checking
├── Signal emission to UI
└── Background thread safety

ScreenshotTab (Main UI)
├── Hotkey control buttons
├── Target window selection
├── Screenshot capture integration
└── Status feedback system
```

### **Safety Features:**

- **Target window validation** - Only captures when intended window is active
- **Graceful degradation** - Works without package if not installed
- **Thread safety** - Background monitoring doesn't block UI
- **Error recovery** - Automatic cleanup on failures

## Usage Examples

### **Gaming Workflow:**

```
1. Select game window in Window Selector
2. Start global monitoring
3. Alt+Tab to game
4. Play game normally
5. Press INSERT when you want screenshot
6. Screenshot captured in background
7. Continue playing
```

### **Renpy Visual Novel Workflow:**

```
1. Select Renpy game window
2. Enable "Hide Renpy text" checkbox
3. Start global monitoring
4. Alt+Tab to game
5. Read dialogue normally
6. Press INSERT for clean screenshot
   → H key sent (hides dialogue)
   → Screenshot captured
   → H key sent (restores dialogue)
7. Continue reading
```

## Requirements

### **Dependencies:**

```
global-hotkeys>=0.1.7  # Global hotkey monitoring
pywin32>=306          # Windows API access
PyQt6>=6.5.0          # GUI framework
```

### **System Requirements:**

- **Windows 10/11** (global-hotkeys is Windows-specific)
- **Python 3.8+**
- **Admin privileges** recommended for maximum compatibility

## Error Handling

### **Common Issues & Solutions:**

**"Global hotkeys not available"**

- Install requirements: `pip install global-hotkeys`

**"No window selected for hotkey capture"**

- Select target window in Window Properties tab first

**"INSERT pressed but target window not active"**

- Normal behavior - only captures when target window has focus

**Hotkey not responding:**

- Stop and restart monitoring
- Check if another application is blocking INSERT key
- Verify target window is still valid

## Integration with Main Application

This feature is designed to be **easily portable** to the main Plot Thickens application:

### **Integration Steps:**

1. **Copy dependencies** to main requirements.txt
2. **Import GlobalHotkeyMonitor class**
3. **Add hotkey controls** to gallery or main interface
4. **Connect to existing screenshot functionality**
5. **Integrate with character tagging workflow**

### **Potential Enhancements:**

- **Configurable hotkeys** (not just INSERT)
- **Multiple target windows**
- **Hotkey combinations** (Ctrl+INSERT, etc.)
- **Screenshot annotations** with character data
- **Batch capture modes**

## Performance Impact

### **Resource Usage:**

- **Minimal CPU overhead** - Event-driven architecture
- **Low memory footprint** - Single background thread
- **No polling** - Efficient Windows hook system
- **Clean shutdown** - Proper resource cleanup

### **Compatibility:**

- **Works with games** - Including fullscreen applications
- **UAC compatible** - Functions across privilege boundaries
- **Multi-monitor support** - Works regardless of window position
- **Stable operation** - Designed for extended use

## Future Roadmap

### **Planned Enhancements:**

- **Configurable hotkey selection**
- **Multiple hotkey support** (different actions)
- **Screenshot preview notifications**
- **Integration with Plot Thickens character workflow**
- **Hotkey conflict detection**
- **Cross-platform support** (if global-hotkeys expands)

## Success Metrics

✅ **Background capture working** - Screenshots taken without window switching  
✅ **Renpy integration functional** - Dialogue hiding/restoration working  
✅ **Stable operation** - No crashes during extended use  
✅ **User-friendly interface** - Simple start/stop controls  
✅ **Production ready** - Comprehensive error handling

This feature represents a **significant productivity enhancement** for visual novel screenshot workflows and demonstrates the potential for advanced automation in the main Plot Thickens application.
