# Ren'Py Styles and Style Properties

## Overview

The style system is Ren'Py's powerful mechanism for customizing the visual appearance of displayables. Styles define how text, buttons, windows, and other UI elements look, and provide a systematic way to create consistent, customizable visual themes in visual novels.

**Key Concepts:**

- **Style Properties**: Individual visual attributes (size, color, background, etc.)
- **Style Inheritance**: Styles can inherit from parent styles
- **Style Prefixes**: Automatic style naming and organization
- **Style Variants**: Different styles for different device types
- **Dynamic Styling**: Runtime style changes and preferences

## Style Fundamentals

### How Styles Work

Each displayable has a **built-in style** that can be customized in two ways:

1. **Direct properties**: Applied when creating the displayable
2. **Named styles**: Predefined style objects that gather properties together

```renpy
# Direct properties
text "Hello" size 40 color "#ff0000"

# Named style
style my_text:
    size 40
    color "#ff0000"

text "Hello" style "my_text"
```

### Style Inheritance

Styles form an inheritance hierarchy where child styles inherit properties from their parents:

```renpy
# Parent style
style button:
    background "#cccccc"
    padding (10, 5)

# Child style inherits from button
style my_button is button:
    background "#ff0000"  # Overrides parent
    # padding is inherited from button
```

**Default Inheritance Rules:**

- Styles with underscores inherit from the part before the first underscore
- `my_button` automatically inherits from `button`
- Styles without parents inherit from `default`

## Defining Styles

### Style Statement (Preferred Method)

```renpy
# Basic style definition
style my_text is text:
    size 40
    color "#ffffff"
    font "special.ttf"

# Style without explicit parent (inherits from default)
style big_red:
    size 60
    color "#ff0000"

# Multiple style statements can modify the same style
style big_red:
    outline [(2, "#000000", 0, 0)]  # Adds outline property

# Conditional style definition
style mobile_button is button:
    variant "touch"  # Only applies on touch devices
    size 50
    padding (20, 10)
```

### Style Statement Clauses

```renpy
style my_style is parent:
    # Basic property assignment
    size 20
    color "#ff0000"

    # Clear all previous properties
    clear

    # Copy properties from another style
    take other_style

    # Conditional application
    variant "mobile"

    # Properties from dictionary
    properties {"xalign": 0.5, "yalign": 0.5}
```

### Python Style Definition

```python
init python:
    # Create new style
    style.my_custom_style = Style(style.default)

    # Set properties
    style.my_custom_style.color = "#ff0000"
    style.my_custom_style.size = 24

    # Style management methods
    style.my_custom_style.clear()              # Remove all properties
    style.my_custom_style.set_parent(style.button)  # Change parent
    style.my_custom_style.take(style.other_style)   # Copy properties
```

## Style Properties by Category

### Text Properties

```renpy
style text_style:
    # Font and size
    font "fonts/custom.ttf"
    size 20
    bold True
    italic False
    underline False
    strikethrough False

    # Colors
    color "#ffffff"
    outlines [(2, "#000000", 0, 0)]  # (size, color, x_offset, y_offset)

    # Spacing and alignment
    kerning 0.5
    line_spacing 0
    text_align 0.5  # 0.0=left, 0.5=center, 1.0=right

    # Text direction and language
    vertical False
    ruby_style style.ruby_text
    language "english"
```

### Position Properties

```renpy
style positioned_element:
    # Position
    xpos 100        # Absolute position
    ypos 50
    xalign 0.5      # Relative position (0.0-1.0)
    yalign 0.5
    xanchor 0.5     # Anchor point on displayable
    yanchor 0.5

    # Offset
    xoffset 10      # Additional offset
    yoffset -5

    # Size
    xsize 300       # Fixed size
    ysize 200
    xminimum 100    # Minimum size
    yminimum 50
    xmaximum 500    # Maximum size
    ymaximum 300

    # Fill available space
    xfill True
    yfill False
```

### Window and Background Properties

```renpy
style window_style:
    # Background
    background "#cccccc"           # Solid color
    background "frame.png"         # Image
    background Frame("border.png", 10, 10)  # Nine-patch frame

    # Padding (internal spacing)
    padding (20, 10)              # (horizontal, vertical)
    left_padding 20               # Individual sides
    right_padding 20
    top_padding 10
    bottom_padding 10

    # Margin (external spacing)
    margin (5, 5)
    left_margin 5
    right_margin 5
    top_margin 5
    bottom_margin 5
```

### Button Properties

```renpy
style button_style:
    # Button-specific backgrounds for different states
    idle_background "#cccccc"
    hover_background "#dddddd"
    selected_idle_background "#aaaaaa"
    selected_hover_background "#bbbbbb"
    insensitive_background "#999999"

    # Focus behavior
    focus_mask None             # Custom focus shape
    keyboard_focus True         # Can receive keyboard focus

    # Activation
    activate_sound "click.wav"
    hover_sound "hover.wav"
```

### Layout Properties

```renpy
style container_style:
    # Box layout
    spacing 10                  # Space between children
    box_reverse False           # Reverse child order
    box_wrap False             # Wrap to new line/column

    # Grid layout
    grid_spacing (10, 5)       # (horizontal, vertical) spacing

    # Alignment of children
    xfill True                 # Children fill horizontal space
    yfill False               # Children fill vertical space
```

## Advanced Styling Techniques

### State-Based Styling

Styles can have different properties for different states:

```renpy
style my_button:
    # Default (idle) state
    background "#cccccc"
    color "#000000"

    # Hover state
    hover_background "#dddddd"
    hover_color "#333333"

    # Selected state
    selected_background "#aaaaaa"
    selected_color "#ffffff"

    # Insensitive state
    insensitive_background "#999999"
    insensitive_color "#666666"

    # Focus state
    focus_background "#eeeeee"
```

### Style Prefixes

Style prefixes automatically create hierarchical styles:

```renpy
# Screen with style prefix
screen inventory():
    style_prefix "inventory"

    frame:           # Uses "inventory_frame" style
        vbox:        # Uses "inventory_vbox" style
            text "Items:"  # Uses "inventory_text" style

# Define the prefixed styles
style inventory_frame is frame:
    background "#1a1a1a"
    padding (20, 15)

style inventory_text is text:
    color "#ffffff"
    size 18
```

### Indexed Styles

Create variations of styles programmatically:

```python
init python:
    # Create character-specific button styles
    for character in ["alice", "bob", "charlie"]:
        style.button[character].background = character_colors[character]
        style.button[character].hover_background = character_hover_colors[character]

# Usage in screens
screen character_menu():
    vbox:
        for char in characters:
            textbutton char.name style style.button[char.name]
```

### Style Preferences

Allow players to customize visual appearance:

```python
init python:
    # Register style preference alternatives
    renpy.register_style_preference(
        "text_size",           # Preference name
        "large",               # Alternative name
        style.say_dialogue,    # Style to modify
        "size",                # Property to change
        24                     # Value for this alternative
    )

    renpy.register_style_preference(
        "text_size", "normal", style.say_dialogue, "size", 18
    )

    renpy.register_style_preference(
        "text_size", "small", style.say_dialogue, "size", 14
    )

# Player preference buttons
textbutton "Large Text" action StylePreference("text_size", "large")
textbutton "Normal Text" action StylePreference("text_size", "normal")
textbutton "Small Text" action StylePreference("text_size", "small")
```

## Common Styling Patterns

### Theme Systems

```renpy
# Base theme styles
style default:
    font "fonts/main.ttf"
    color "#ffffff"

# Dark theme
style dark_button is button:
    background "#333333"
    hover_background "#444444"
    color "#ffffff"

style dark_frame is frame:
    background "#222222"

# Light theme
style light_button is button:
    background "#eeeeee"
    hover_background "#dddddd"
    color "#000000"

style light_frame is frame:
    background "#ffffff"

# Theme switching
screen preferences():
    textbutton "Dark Theme":
        action [
            SetVariable("theme", "dark"),
            Function(apply_theme)
        ]
```

### Responsive Design

```renpy
# Base mobile styles
style mobile_text is text:
    variant "mobile"
    size 20
    line_spacing 2

style mobile_button is button:
    variant "mobile"
    padding (15, 10)
    text_size 18

# Desktop styles
style desktop_text is text:
    variant "pc"
    size 16
    line_spacing 0

style desktop_button is button:
    variant "pc"
    padding (10, 5)
    text_size 14
```

### Animation-Ready Styles

```renpy
# Styles designed to work with transforms
style sliding_panel:
    background "#1a1a1a"
    padding (20, 15)
    xsize 300
    # No position properties - handled by transforms

# Usage with transforms
transform slide_in:
    xpos -300
    linear 0.5 xpos 0

show screen side_panel at slide_in
```

## Style Organization Best Practices

### Naming Conventions

```renpy
# Hierarchical naming
style menu_button is button          # Top level
style menu_main_button is menu_button     # Sub-category
style menu_main_save_button is menu_main_button  # Specific use

# Feature-based naming
style large_text is text
style error_text is text
style success_text is text

# Component-based naming
style inventory_frame is frame
style inventory_item_button is button
style inventory_quantity_text is text
```

### Modular Style Files

```renpy
# styles/common.rpy
style default:
    font "fonts/main.ttf"

# styles/buttons.rpy
style button:
    background "#cccccc"
    padding (10, 5)

# styles/text.rpy
style text:
    color "#000000"
    size 16

# styles/themes.rpy
style dark_theme_button is button:
    background "#333333"
    color "#ffffff"
```

## Integration with The Plot Thickens

### Style Analysis Applications

**Visual Pattern Recognition:**

- Identify visual themes and color schemes
- Catalog button styles and their usage patterns
- Map style inheritance hierarchies
- Understand responsive design implementations

**UI Consistency Analysis:**

- Check for style consistency across screens
- Identify style naming patterns and conventions
- Map style prefixes and their usage
- Analyze theme switching implementations

**Asset Organization:**

- Track image assets used in styles
- Identify font usage patterns
- Map style-based asset references
- Understand visual asset management

### Source Code Integration

**For Ren'Py Source API:**

- Parse style definitions in .rpy files
- Extract style property assignments
- Map style inheritance relationships
- Identify style preferences and variants

**For Story Board System:**

- Visualize UI styling patterns
- Show style relationships and hierarchies
- Display theme variations and preferences
- Map visual consistency across scenes

**For Gallery Widget:**

- Apply VN styling patterns to TPT interface
- Implement theme switching capabilities
- Use style inheritance for component organization
- Create responsive design patterns

### Visual Novel Analysis

**Style Documentation:**

- Generate style guides for analyzed VN projects
- Document visual themes and variations
- Map UI component styling patterns
- Identify accessibility features and adaptations

**Design Pattern Extraction:**

- Learn from professional VN styling approaches
- Identify common UI patterns and solutions
- Extract responsive design strategies
- Understand accessibility implementations

This comprehensive understanding of Ren'Py's style system enables The Plot Thickens to better analyze visual novel projects, understand their visual design patterns, and potentially implement similar styling approaches in its own interface design.
