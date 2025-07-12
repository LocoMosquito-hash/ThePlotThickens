# Ren'Py Screens and Screen Language

## Overview

The screen system in Ren'Py is fundamental for creating user interfaces. Everything the user sees that isn't part of the story images (displayed via scene/show/hide) is part of the user interface, customized using screens.

**Key Concepts:**

- **Images**: Story content displayed via scene, show, hide statements
- **User Interface**: Everything else, customized using screens
- **Screen Functions**: Display information + Allow user interaction
- **Multiple Screens**: More than one screen can be shown simultaneously

## Screen Display Methods

Screens can be displayed in four ways:

1. **Implicitly**: When script statements execute (e.g., say statement shows say screen)
2. **Automatically**: System shows screens (e.g., main_menu screen on startup)
3. **As Actions**: Associated with buttons, mouse, or keyboard (e.g., save screen on right-click/escape)
4. **Explicitly**: Using show/call screen statements

## Screen Variable Scope

Screen variables are resolved in order:

1. **Local Variables**: Only in screens used by another screen (via `use` statement)

   - Set using `SetLocalVariable` action
   - Limited to the used screen only

2. **Screen Variables**: Created with in-screen `Default` or `Python` statements

   - Set through `SetScreenVariable` action
   - Available to the entire screen and used screens

3. **Global Variables**: From the general store
   - Set through `SetVariable` action
   - Available throughout the entire game

**Important**: Screen parameters (passed via parentheses) live in screen variable scope but cannot be edited through actions as they reset to original values.

## Screen Language Syntax

### Basic Structure

```renpy
screen screen_name(parameters):
    """Optional docstring"""
    # Properties (modal, sensitive, tag, zorder, etc.)

    # UI elements
    container:
        property value
        child_element
```

### Screen Statement Properties

- **modal**: Boolean - prevents interaction with displayables below
- **sensitive**: Expression - determines if screen responds to input
- **tag**: String - for screen replacement (same tag replaces previous)
- **zorder**: Integer - display order (higher = closer to user)
- **variant**: String/list - screen variant for different devices
- **style_prefix**: String - prefix for child styles
- **layer**: String - default layer for display
- **roll_forward**: Boolean - roll forward behavior for call screen

## User Interface Elements

### Common Properties (All UI Elements)

- **at**: Transform(s) or anonymous transform
- **default_focus**: Boolean - default focus priority
- **extra_alt**: String - additional self-voicing text
- **focus**: String/integer - focus name for navigation
- **group_alt**: String - group prefix for self-voicing
- **id**: String - identifier for property supply
- **style**: String - style name
- **style_prefix**: String - style prefix for children
- **style_suffix**: String - specific style suffix
- **tooltip**: Object - tooltip content for GetTooltip()

### Layout Containers

#### Fixed

```renpy
fixed:
    # Children positioned via position style properties
    element1 xpos 100 ypos 50
    element2 xpos 200 ypos 100
```

#### Frame

```renpy
frame:
    # Window with background for UI elements
    xpadding 10
    ypadding 10
    child_element
```

#### VBox (Vertical Layout)

```renpy
vbox:
    spacing 10
    child1
    child2
    child3
```

#### HBox (Horizontal Layout)

```renpy
hbox:
    spacing 10
    child1 child2 child3
```

#### Grid

```renpy
grid 2 3:  # 2 columns, 3 rows
    spacing 5
    # Must have exactly (cols * rows) children
    for i in range(6):
        text "Cell [i]"
```

#### Side

```renpy
side "c tl br":  # center, top-left, bottom-right
    spacing 10
    text "Center"
    text "Top-Left"
    text "Bottom-Right"
```

### Interactive Elements

#### Button

```renpy
button:
    action Return("value")
    alternate ShowMenu("context_menu")
    hovered SetVariable("tooltip", "Button info")
    unhovered SetVariable("tooltip", "")

    text "Click Me"
```

#### Textbutton

```renpy
textbutton "Save Game":
    action ShowMenu('save')
    keysym "s"
    text_size 20
```

#### Imagebutton

```renpy
imagebutton:
    auto "button_%s.png"  # _idle, _hover, _selected_idle, etc.
    action Jump("next_scene")
```

#### Input

```renpy
input:
    value InputValue("player_name")
    length 20
    allow "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz "
    changed InputCallback
```

### Display Elements

#### Text

```renpy
text "Hello, World!":
    size 40
    color "#ffffff"
    xalign 0.5
```

#### Bar

```renpy
bar:
    value Preference("music volume")
    range 100
    xsize 200
    released Play("sound", "beep.ogg")
```

#### Add (Images/Displayables)

```renpy
add "background.jpg":
    xalign 0.5
    yalign 0.5
```

### Advanced Elements

#### Viewport (Scrollable Areas)

```renpy
viewport:
    child_size (800, 1200)
    xsize 600
    ysize 400
    mousewheel True
    draggable True

    vbox:
        # Large content that scrolls
        for i in range(100):
            text "Line [i]"
```

#### Vpgrid (Optimized Grid in Viewport)

```renpy
vpgrid:
    cols 3
    spacing 5
    scrollbars "vertical"
    mousewheel True

    for i in range(300):
        textbutton "Item [i]" action Return(i)
```

#### Timer

```renpy
timer 5.0:
    action Jump("timeout")
    repeat False
```

#### Key

```renpy
key "game_menu":
    action ShowMenu('save')

key ["s", "ctrl_s"]:
    action QuickSave()
```

#### Mousearea

```renpy
mousearea:
    area (100, 100, 200, 150)
    hovered Show("tooltip")
    unhovered Hide("tooltip")
```

#### Nearrect (Positioned Near Rectangle)

```renpy
nearrect:
    focus "button_focus"
    preferred_side "bottom"

    frame:
        text "Tooltip content"
```

## Imagemaps

Imagemaps provide a visual way to create interfaces using images with defined interactive areas.

```renpy
screen preferences():
    imagemap:
        auto "gui_prefs_%s.png"

        hotspot (740, 232, 75, 73):
            action Preference("display", "fullscreen")
            alt "Display Fullscreen"

        hotspot (832, 232, 75, 73):
            action Preference("display", "window")
            alt "Display Window"

        hotbar (736, 415, 161, 20):
            value Preference("music volume")
            alt "Music Volume"
```

## Control Statements

### Default (Variable Declaration)

```renpy
screen menu_screen():
    default selected_option = None

    vbox:
        for option in menu_options:
            textbutton option:
                action SetScreenVariable("selected_option", option)
```

### For Loops

```renpy
screen inventory():
    grid 4 3:
        for i, item in enumerate(player_inventory):
            textbutton item.name:
                action Use("item_detail", item)

        # With index for stable transforms
        for i, item index item.id in enumerate(player_inventory):
            textbutton item.name action Return(item)
```

### If Statements

```renpy
screen status_display():
    vbox:
        if player.health > 50:
            text "Healthy" color "#00ff00"
        elif player.health > 20:
            text "Injured" color "#ffff00"
        else:
            text "Critical" color "#ff0000"
```

### Use (Include Other Screens)

```renpy
screen file_slot(slot_number):
    button:
        action FileAction(slot_number)

        hbox:
            add FileScreenshot(slot_number)
            vbox:
                text FileTime(slot_number)
                text FileSaveName(slot_number)

screen save_menu():
    grid 3 3:
        for i in range(1, 10):
            use file_slot(i)
```

### Use with Transclude (Reusable Layouts)

```renpy
screen dialog_frame():
    frame:
        background "dialog_bg.png"
        padding (20, 20)
        transclude

screen confirm_dialog():
    use dialog_frame:
        vbox:
            text "Are you sure?"
            hbox:
                textbutton "Yes" action Return(True)
                textbutton "No" action Return(False)
```

### On (Event Handling)

```renpy
screen animated_menu():
    frame:
        # Handle screen lifecycle events
        on "show" action Play("sound", "menu_open.ogg")
        on "hide" action Play("sound", "menu_close.ogg")

        vbox:
            text "Menu Content"
```

### Showif (Conditional Display with Animation)

```renpy
transform fade_in_out:
    alpha 0.0
    on show:
        linear 0.3 alpha 1.0
    on hide:
        linear 0.3 alpha 0.0

screen notification_system():
    default message = ""

    showif message:
        text message at fade_in_out
```

### Python Blocks

```renpy
screen dynamic_content():
    python:
        current_time = time.strftime("%H:%M")
        formatted_date = time.strftime("%B %d, %Y")

    vbox:
        text "Current Time: [current_time]"
        text "Today's Date: [formatted_date]"
```

## Screen Management Statements

### Show Screen

```renpy
# Basic usage
show screen inventory

# With parameters
show screen character_stats(player_character)

# With properties
show screen overlay zorder 100 onlayer "overlay"

# With transition
show screen menu with dissolve

# Expression-based
$ screen_name = "dynamic_menu"
show screen expression screen_name pass (arg1, arg2)
```

### Hide Screen

```renpy
# Basic hide
hide screen inventory

# With transition
hide screen menu with dissolve

# Expression-based
hide screen expression screen_name
```

### Call Screen (Modal Display)

```renpy
# Shows screen and waits for return value
call screen file_picker
$ selected_file = _return

# With transition
call screen confirmation_dialog with dissolve

# No implicit with None
call screen special_menu(_with_none=False) with fade
```

## Screen Variants

Ren'Py automatically detects device types and selects appropriate screen variants:

```renpy
# Default screen for PC
screen main_menu():
    imagebutton:
        auto "menu_button_%s.png"
        action Start()

# Touch-optimized variant
screen main_menu():
    variant "touch"

    textbutton "Start Game":
        text_size 40  # Larger for touch
        action Start()

# Small screen variant
screen main_menu():
    variant "small"

    vbox:
        # Simplified layout for phones
        textbutton "Start" action Start()
        textbutton "Load" action ShowMenu("load")
```

**Common Variants:**

- `"pc"`: Mouse and keyboard devices
- `"touch"`: Touchscreen devices
- `"small"`: Phone-sized screens
- `"medium"`: Tablet-sized screens
- `"large"`: Desktop screens
- `"mobile"`: Android/iOS
- `"tv"`: Television displays

## Advanced Features

### Has Statement (Container Specification)

```renpy
screen preferences():
    frame:
        has vbox  # Children go into vbox instead of fixed

        text "Display Options"
        textbutton "Fullscreen" action Preference("display", "fullscreen")
        textbutton "Window" action Preference("display", "window")
```

### Drag and Drop

```renpy
screen inventory_drag():
    draggroup:
        for item in inventory:
            drag:
                draggable True
                droppable True
                drag_name item.id

                add item.image
```

### Focus Management

```renpy
screen navigation():
    hbox:
        textbutton "Save" action ShowMenu("save") focus "save_button"
        textbutton "Load" action ShowMenu("load")
        textbutton "Quit" action Quit() default_focus True
```

## Integration with The Plot Thickens

### Relevant Patterns for TPT

1. **UI Layout Analysis**: Understanding how VNs structure their interfaces
2. **Navigation Patterns**: Menu systems, button layouts, screen transitions
3. **Data Display**: Character information, story progress, save systems
4. **Interactive Elements**: Buttons, inputs, drag-and-drop interfaces
5. **Responsive Design**: Screen variants for different device types
6. **Animation Systems**: Showif statements, transform integration
7. **Modal Dialogs**: Call screen patterns for popup windows
8. **Event Handling**: On statements for screen lifecycle management

### Code Analysis Applications

- **Screen Detection**: Identify screen definitions in .rpy files
- **UI Element Mapping**: Catalog buttons, layouts, and interactive elements
- **Navigation Flow**: Trace screen transitions and menu structures
- **Asset References**: Track image and audio files used in screens
- **Action Analysis**: Understand what buttons and interactions do
- **Layout Patterns**: Identify common UI structures and components

### Story Board Integration

- **Screen Visualization**: Represent UI layouts in story board
- **Interaction Mapping**: Show user input points and their effects
- **State Tracking**: Monitor screen variables and their changes
- **Flow Analysis**: Visualize screen transitions and modal behaviors

This documentation provides the foundation for understanding how Ren'Py structures its user interfaces, which will be invaluable for analyzing and visualizing VN projects in The Plot Thickens.
