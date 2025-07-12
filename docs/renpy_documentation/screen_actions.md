# Ren'Py Screen Actions, Values, and Functions

## Overview

Screen Actions, Values, and Functions are the **programmatic heart** of Ren'Py development. These are the tools that VN developers use to create interactive elements, manage data, handle user input, and control game flow. This is where most creative liberties and custom programming occur in visual novels.

**Core Concepts:**

- **Actions**: Invoked when buttons are activated, hovered, or unhovered
- **Values**: Used with bars and inputs to set/adjust underlying properties
- **Functions**: Utility functions for screen management and interaction

## Actions

Actions are the primary way to make screens interactive. They can be:

- Single actions: `Return("value")`
- Function calls: Any function that takes no arguments
- Action lists: `[SetVariable("flag", True), Jump("next_scene")]`

**Action Properties:**

- **Sensitivity**: Actions determine if buttons are sensitive (clickable)
- **Selection**: Actions determine if buttons appear selected
- **Chaining**: Multiple actions can be combined in lists

### Control Actions

These manage screens, interaction results, and control flow:

#### Basic Control

```renpy
# End interaction and transfer control
Call("label", arg1, arg2)              # Call label with arguments
Jump("label")                          # Jump to label
Return("value")                        # Return value from interaction
NullAction()                          # Do nothing (for hover effects)

# Screen management
Show("screen_name", transition=dissolve)     # Show another screen
Hide("screen_name", transition=fade)         # Hide a screen
ToggleScreen("inventory")                    # Toggle screen visibility
ShowTransient("popup", transition=dissolve) # Show temporary screen
```

#### Menu and Game Control

```renpy
# Menu actions
MainMenu(confirm=True, save=True)       # Return to main menu
Quit(confirm=None)                      # Quit game
ShowMenu("save")                        # Show game menu screen
Start("start")                          # Start new game

# File operations
Continue()                              # Load last save
QuickSave(message="Quick save complete.")
QuickLoad(confirm=True)
FileTakeScreenshot()                    # Take save screenshot
```

### Data Actions

Data actions provide systematic ways to manipulate variables, screen variables, fields, and dictionaries:

#### Variable Management Pattern

| Manager       | Variable              | ScreenVariable              | LocalVariable              | Field              | Dict              |
| ------------- | --------------------- | --------------------------- | -------------------------- | ------------------ | ----------------- |
| **Set**       | `SetVariable()`       | `SetScreenVariable()`       | `SetLocalVariable()`       | `SetField()`       | `SetDict()`       |
| **Toggle**    | `ToggleVariable()`    | `ToggleScreenVariable()`    | `ToggleLocalVariable()`    | `ToggleField()`    | `ToggleDict()`    |
| **Cycle**     | `CycleVariable()`     | `CycleScreenVariable()`     | `CycleLocalVariable()`     | `CycleField()`     | `CycleDict()`     |
| **Increment** | `IncrementVariable()` | `IncrementScreenVariable()` | `IncrementLocalVariable()` | `IncrementField()` | `IncrementDict()` |

#### Examples

```renpy
# Global variable manipulation
SetVariable("player_name", "Alex")           # player_name = "Alex"
ToggleVariable("show_hints")                 # show_hints = not show_hints
CycleVariable("difficulty", ["Easy", "Medium", "Hard"])
IncrementVariable("score", 10)               # score += 10

# Screen variable manipulation (for current screen)
SetScreenVariable("selected_option", "magic")
ToggleScreenVariable("show_details")
CycleScreenVariable("view_mode", ["list", "grid", "icons"])

# Object field manipulation
SetField(player, "level", 5)                # player.level = 5
IncrementField(player, "experience", 100)   # player.experience += 100

# Dictionary/list manipulation
SetDict(inventory, "potions", 3)            # inventory["potions"] = 3
AddToSet(collected_items, "magic_sword")    # Add to set/list
RemoveFromSet(collected_items, "old_key")   # Remove from set/list
ToggleSetMembership(favorites, character)   # Toggle membership
```

### File Actions

Comprehensive save/load system management:

```renpy
# Universal file action - load if on load screen, save otherwise
FileAction(name=1, page="auto")

# Specific file operations
FileSave(name=1, confirm=True, page="quick")
FileLoad(name=1, confirm=True, page="auto")
FileDelete(name=1, confirm=True, page="save")

# Page management
FilePage("auto")                        # Switch to auto-save page
FilePageNext(max=10, wrap=True)         # Next page with wraparound
FilePagePrevious(max=10, wrap=True)     # Previous page
```

### Audio Actions

Complete audio system control:

```renpy
# Playback control
Play("music", "bgm.ogg", selected=True)    # Play with selection state
Queue("sound", "sfx.wav")                  # Queue audio file
Stop("voice")                              # Stop channel
PauseAudio("music", value=True)            # Pause/unpause

# Volume and mixer control
SetMixer("music", 0.7)                     # Set volume (0.0-1.0)
GetMixer("sound", db=False)                # Get current volume
SetMute("sfx", True)                       # Mute/unmute mixer
ToggleMute(["music", "sound"])             # Toggle multiple mixers
```

### Focus Actions

Advanced focus and UI interaction management:

```renpy
# Focus rectangle capture and management
CaptureFocus("dropdown")                   # Capture current focus area
ClearFocus("dropdown")                     # Clear captured focus
GetFocusRect("tooltip")                    # Get focus rectangle
ToggleFocus("menu_area")                   # Toggle focus capture

# Useful for tooltips, dropdowns, context menus
```

### Other Utility Actions

```renpy
# User interaction
Confirm("Are you sure?", yes=Quit(), no=NullAction())
CopyToClipboard("Achievement unlocked!")
MouseMove(x=100, y=200, duration=0.5)
Screenshot()                               # Take screenshot

# Development and debugging
EditFile("script.rpy", line=42)           # Open file in editor
Notify("Settings saved!")                 # Show notification
Help("controls")                          # Show help

# Advanced control
Function(my_function, arg1, arg2)         # Call custom function
RestartStatement()                        # Restart current statement
Rollback(force="menu")                    # Force rollback
Skip(fast=True, confirm=False)            # Begin skipping
With(dissolve)                            # Apply transition

# Conditional actions
If(player.level > 5,
   true=Show("advanced_menu"),
   false=Show("basic_menu"))

# Scroll control for viewports
Scroll("inventory_viewport", "vertical increase", amount="page")
```

## Bar Values

Bar values control the data behind progress bars, sliders, and adjustable elements:

### Basic Bar Values

```renpy
# Static and animated values
StaticValue(value=0.5, range=1.0)         # Fixed value display
AnimatedValue(value=0.8, range=1.0, delay=2.0)  # Animated transition

# Variable-based bars
VariableValue("player_health", range=100)   # Global variable
ScreenVariableValue("volume", range=1.0)    # Screen variable
LocalVariableValue("temp_val", range=10)    # Local variable (used screens)
FieldValue(player, "mana", range=100)       # Object field
DictValue(stats, "strength", range=20)     # Dictionary value

# Audio position
AudioPositionValue("music", update_interval=0.1)

# Mixer volumes
MixerValue("music")                        # Audio mixer volume
```

### Viewport Scrolling

```renpy
# Scroll bars for viewports
XScrollValue("inventory_viewport")         # Horizontal scrolling
YScrollValue("gallery_viewport")           # Vertical scrolling
```

## Input Values

Input values manage text input fields and control their behavior:

```renpy
# Variable-based inputs
VariableInputValue("player_name", default=True, returnable=True)
ScreenVariableInputValue("search_text", default=True)
LocalVariableInputValue("temp_input", returnable=False)
FieldInputValue(player, "nickname", default=True)
DictInputValue(settings, "username", returnable=True)

# Special input types
FilePageNameInputValue(                    # File page naming
    pattern="Page {}",
    auto="Auto Saves",
    quick="Quick Saves"
)

# Input methods (all values have these)
my_input = VariableInputValue("name")
my_input.Enable()                          # Enable editing
my_input.Disable()                         # Disable editing
my_input.Toggle()                          # Toggle editing
DisableAllInputValues()                    # Disable all inputs
```

## Preference System

The `Preference()` function provides easy access to common game preferences:

### Display Preferences

```renpy
Preference("display", "fullscreen")       # Fullscreen mode
Preference("display", "window")           # Windowed mode
Preference("display", 2.0)                # Windowed at 2x size
Preference("display", "toggle")           # Toggle display mode
```

### Text and Interface

```renpy
Preference("text speed", 142)             # Characters per second
Preference("text speed", 0)               # Instant text
Preference("transitions", "all")          # Show all transitions
Preference("transitions", "none")         # Disable transitions
Preference("skip", "seen")                # Skip only seen text
Preference("skip", "all")                 # Skip all text
```

### Audio Preferences

```renpy
Preference("music volume", 0.7)           # Set music volume
Preference("sound volume", 0.5)           # Set sound volume
Preference("voice volume", 0.8)           # Set voice volume
Preference("music mute", "toggle")        # Toggle music mute
Preference("all mute", "toggle")          # Toggle all audio
```

### Accessibility

```renpy
Preference("self voicing", "enable")      # Enable text-to-speech
Preference("font size", 1.2)              # Font scaling
Preference("font line spacing", 1.1)      # Line spacing scaling
Preference("high contrast text", "enable") # High contrast mode
Preference("system cursor", "enable")     # Use system cursor
```

### Auto-Forward and Timing

```renpy
Preference("auto-forward", "enable")      # Enable auto-forward
Preference("auto-forward time", 10)       # Seconds per 250 chars
Preference("wait for voice", "enable")    # Wait for voice
Preference("voice sustain", "enable")     # Sustain voice
```

## Advanced Programming Patterns

### Custom Actions

```python
# Create custom action class
class MyCustomAction(Action):
    def __init__(self, value):
        self.value = value

    def __call__(self):
        # Action implementation
        persistent.custom_flag = self.value
        renpy.restart_interaction()

    def get_selected(self):
        return persistent.custom_flag == self.value

    def get_sensitive(self):
        return True  # Always enabled

# Usage in screens
textbutton "Custom Action" action MyCustomAction("special")
```

### Complex Action Combinations

```renpy
# Multiple actions with conditional sensitivity
textbutton "Advanced Option":
    action [
        SensitiveIf(SetVariable("unlocked", True)),
        SetVariable("current_mode", "advanced"),
        Show("advanced_settings"),
        Play("sound", "menu_select.ogg")
    ]

# Selected state management
textbutton "Option A":
    action [
        SelectedIf(SetVariable("choice", "A")),
        SetVariable("choice", "A"),
        Function(update_display)
    ]
```

### Dynamic Value Creation

```python
# Create values dynamically based on data
screen character_stats():
    vbox:
        for stat_name, stat_value in character.stats.items():
            hbox:
                text "[stat_name]:"
                bar:
                    value FieldValue(character.stats, stat_name, range=100)
                    xsize 200
```

## Integration with The Plot Thickens

### Analysis Applications

**Action Detection:**

- Parse button actions to understand user interactions
- Identify variable management patterns
- Track state changes and their triggers
- Map navigation flows between screens

**Data Flow Analysis:**

- Identify variables used in screens
- Track how data flows between screens
- Understand save/load patterns
- Map preference and settings systems

**UI Interaction Mapping:**

- Catalog all interactive elements
- Understand input/output patterns
- Identify custom action implementations
- Map user journey through interfaces

### Source Code Integration

**For Ren'Py Source API:**

- Parse action definitions in buttons and hotspots
- Extract variable references and modifications
- Identify screen transition patterns
- Track audio and media management

**For Story Board System:**

- Visualize user interaction points
- Show data flow between scenes
- Map decision consequences
- Display state management patterns

**For Character Management:**

- Track character-related variable changes
- Identify character state management
- Map character interaction patterns

This documentation provides the foundation for understanding how visual novels implement their interactive elements and data management - crucial for analyzing and visualizing the programmatic aspects of VN projects in The Plot Thickens.
