# Ren'Py Displayables

## Overview

Displayables are the fundamental building blocks of everything visual in Ren'Py. They represent any object that can be shown to the user - from simple images and text to complex interactive elements and custom visual effects. Understanding displayables is crucial for analyzing how visual novels construct their visual experiences and implement creative visual programming.

**Key Concepts:**

- **Basic Displayables**: Images, text, solid colors, and null spaces
- **Layout Displayables**: Containers that organize other displayables
- **Interactive Displayables**: Elements that respond to user input
- **Dynamic Displayables**: Elements that change based on game state
- **Effects Displayables**: Visual effects and transformations
- **Custom Displayables**: Developer-created visual elements

## Displayable Types and Usage

When Ren'Py expects a displayable, several things can be provided:

```renpy
# Direct displayable objects
image my_image = Image("character.png")

# Strings with dots (interpreted as filenames)
show "background.jpg"

# Colors (converted to Solid displayables)
show "#ff0000"  # Red solid color
show Color(255, 0, 0, 255)  # RGBA color
show (255, 0, 0, 255)  # RGBA tuple

# Image names (references to defined images)
show eileen happy

# Lists (first matching item is used)
show ["character_[outfit].png", "character_default.png"]

# Dynamic images with substitution
show "character_[mood]_[outfit].png"  # Interpolated at runtime
```

## Image Displayables

### Basic Image Loading

```renpy
# Automatic image creation from filename
image background = "bg_room.png"

# Explicit Image displayable with properties
image character_large = Image(
    "character.png",
    oversample=2,        # Higher quality rendering
    optimize_bounds=True, # Optimize GPU memory usage
    mipmap=True         # Generate mipmaps for scaling
)

# SVG images with DPI control
image vector_logo = Image("logo.svg", dpi=192)
```

### Supported Formats

- **Recommended**: AVIF, WEBP, PNG, JPG, SVG
- **Supported**: GIF (non-animated), BMP
- **Advanced**: Variable resolution and oversampling support

### Image Cache Management

```python
# Configure image caching
define config.image_cache_size = 8  # Screens worth of image data

# Predictive loading
$ renpy.predict_images(["character happy", "background city"])
```

## Image-Like Displayables

### Solid Colors and Shapes

```renpy
# Solid color fills
image red_bg = Solid("#ff0000")
image transparent = Solid("#00000080")  # With alpha

# Null displayables for spacing
image spacer = Null(width=50, height=20)
```

### Frames and Borders

```renpy
# Nine-patch frame scaling
image dialog_frame = Frame(
    "frame.png",
    left=20, top=20, right=20, bottom=20,
    tile=False  # Scale instead of tile
)

# Frame with borders object
image fancy_frame = Frame(
    "border.png",
    Borders(10, 10, 10, 10, pad_left=5, pad_top=5)
)

# Tiled backgrounds
image pattern_bg = Tile("pattern.png")
```

### Composite Images

```renpy
# Combine multiple images at specific positions
image character_composite = Composite(
    (400, 600),                    # Final size
    (0, 0), "character_base.png",  # Base layer
    (50, 100), "clothing.png",     # Clothing layer
    (25, 75), "expression.png"     # Expression layer
)

# Cropped images
image face_closeup = Crop((100, 50, 200, 200), "character_full.png")
```

### Alpha Masking and Effects

```renpy
# Alpha masking using another image's alpha
image masked_character = AlphaMask(
    "character.png",      # Source image
    "character_mask.png", # Mask (alpha channel)
    invert=False         # Normal or inverted mask
)

# Flatten multiple textures into one (for transform effects)
image flattened = Flatten("multi_layer_image")
```

## Layout Displayables

### Box Layouts

```renpy
# Horizontal layout
image button_row = HBox(
    "button1.png",
    Null(width=10),  # Spacing
    "button2.png",
    "button3.png",
    spacing=5        # Automatic spacing
)

# Vertical layout
image menu_column = VBox(
    "title.png",
    "option1.png",
    "option2.png",
    "option3.png",
    spacing=10
)

# Fixed positioning
image overlay = Fixed(
    Image("background.png", xalign=0.0, yalign=0.0),
    Image("character.png", xalign=0.7, yalign=1.0),
    Image("ui_frame.png", xalign=1.0, yalign=0.0)
)
```

### Grid Layout

```renpy
# Structured grid arrangement
image inventory_grid = Grid(
    3, 2,  # 3 columns, 2 rows
    "item1.png", "item2.png", "item3.png",
    "item4.png", "item5.png", "item6.png"
)
```

## Dynamic Displayables

### Condition-Based Display

```renpy
# Show different images based on conditions
image character_mood = ConditionSwitch(
    "character.mood == 'happy'", "character_happy.png",
    "character.mood == 'sad'", "character_sad.png",
    "character.mood == 'angry'", "character_angry.png",
    "True", "character_neutral.png",  # Default
    predict_all=True  # Preload all variants
)

# Show based on what's currently displayed
image emotion_indicator = ShowingSwitch(
    "eileen happy", "indicator_happy.png",
    "eileen sad", "indicator_sad.png",
    None, "indicator_neutral.png"  # Default
)
```

### Dynamic Programming

```python
# Programmatically generated displayables
def dynamic_clock(st, at):
    import time
    current_time = time.strftime("%H:%M:%S")
    return Text(current_time, size=24), 1.0  # Update every second

image live_clock = DynamicDisplayable(dynamic_clock)
```

### Dynamic Images with Interpolation

```renpy
# Images that update with variables
image character_outfit = DynamicImage("character_[outfit]_[mood].png")

# Prefix substitution for style variations
image styled_button = DynamicImage("button_[prefix_]normal.png")
```

## Layer Displayables

```renpy
# Display a layer as a displayable (for detached layers)
image tv_content = Layer("broadcast", clipping=True)

# Configure detached layers
define config.detached_layers += ["broadcast", "overlay"]

# Usage in complex compositions
screen tv_display():
    frame:
        background "#000000"
        padding (10, 10)
        add Layer("broadcast") zoom 0.5
```

## Effects and Visual Manipulation

### Alpha Blending and Transitions

```renpy
# Custom transition effects using control displayables
transform slide_control:
    alpha 0.0
    linear 1.0 alpha 1.0

image custom_transition = AlphaBlend(
    slide_control,     # Control transform
    "old_image.png",   # Old state
    "new_image.png",   # New state
    alpha=True         # Composite with background
)
```

### Placeholder System

```renpy
# Automatic placeholders for undefined images
image character_placeholder = Placeholder(
    "girl",           # Type: 'bg', 'boy', 'girl', or None
    full=True,        # Full body vs 3/4 sprite
    flip=False,       # Horizontal flip
    text="Character Name"  # Custom text
)

# Background placeholders
image scene_placeholder = Placeholder("bg")
```

## Advanced Displayables

### Prefixed Displayables

```python
# Custom displayable prefixes
init -10 python:
    def embiggen_prefix(argument):
        return Transform(argument, zoom=2.0)

    def tint_prefix(argument):
        color, image = argument.split(":", 1)
        return im.MatrixColor(image, im.matrix.tint(*color_from_hex(color)))

    config.displayable_prefix["big"] = embiggen_prefix
    config.displayable_prefix["tint"] = tint_prefix

# Usage
image big_character = "big:character.png"
image red_background = "tint:#ff0000:background.png"
```

### Custom Displayable Classes

```python
init python:
    class ProgressBar(renpy.Displayable):
        def __init__(self, width, height, **kwargs):
            super(ProgressBar, self).__init__(**kwargs)
            self.width = width
            self.height = height

        def render(self, width, height, st, at):
            # Custom rendering logic
            render = renpy.Render(self.width, self.height)

            # Draw progress bar
            progress_width = int(self.width * persistent.progress)
            bar_surf = renpy.render(
                Solid("#00ff00"),
                progress_width, self.height, st, at
            )
            render.blit(bar_surf, (0, 0))

            return render

        def event(self, ev, x, y, st):
            # Handle user input
            if ev.type == pygame.MOUSEBUTTONDOWN:
                # Calculate click position as progress
                persistent.progress = float(x) / self.width
                renpy.redraw(self, 0)

# Usage
image custom_progress = ProgressBar(200, 20)
```

## Displayable Properties and Styling

### Common Properties

```renpy
# Position and size properties
image positioned = Image("character.png"):
    xpos 100 ypos 50          # Absolute position
    xalign 0.5 yalign 1.0     # Relative position (0.0-1.0)
    xanchor 0.5 yanchor 1.0   # Anchor point on displayable
    xoffset 10 yoffset -5     # Additional offset

# Size constraints
image sized = Image("background.png"):
    xsize 800 ysize 600       # Fixed size
    xminimum 400 yminimum 300 # Minimum size
    xmaximum 1200 ymaximum 900 # Maximum size
    xfill True yfill False    # Fill available space

# Style application
image styled = Text("Hello World"):
    style "my_custom_style"
    size 24                   # Direct style property
    color "#ffffff"          # Direct style property
```

### Transform Integration

```renpy
# Displayables with transforms
image animated_character = Image("character.png"):
    at character_entrance    # Apply transform

# Transform properties directly
image floating = Image("particle.png"):
    at transform:
        alpha 0.8
        ypos 100
        linear 2.0 ypos 0
        repeat
```

## Performance Considerations

### Optimization Strategies

```renpy
# Optimize bounds for GPU memory
image optimized = Image("large_sprite.png", optimize_bounds=True)

# Control mipmapping for scaling
image scalable = Image("ui_element.png", mipmap=True)

# Oversample for high-quality rendering
image high_quality = Image("character.png", oversample=2)

# Prediction for smooth performance
$ renpy.predict_displayable(my_complex_displayable)
```

### Memory Management

```python
# Control displayable lifecycle
init python:
    # Preload critical displayables
    important_displayables = [
        Image("character_main.png"),
        Frame("ui_frame.png", 10, 10),
        Composite((400, 600), (0, 0), "base.png", (50, 50), "overlay.png")
    ]

    for d in important_displayables:
        renpy.predict_displayable(d)
```

## Integration with The Plot Thickens

### Visual Analysis Applications

**Asset Organization:**

- Catalog all displayable types and their usage patterns
- Map image assets and their displayable implementations
- Identify visual composition techniques and patterns
- Track performance optimization strategies

**Visual Design Patterns:**

- Analyze layout strategies and UI organization
- Identify visual effects and their implementations
- Map dynamic visual content and state-based displays
- Understand visual hierarchy and composition rules

**Custom Implementation Detection:**

- Find custom displayable classes and their behaviors
- Identify creative visual programming techniques
- Map advanced visual effects and animations
- Track performance optimization implementations

### Source Code Integration

**For Ren'Py Source API:**

- Parse displayable definitions and image assignments
- Extract visual composition and layout patterns
- Identify dynamic displayable usage and conditions
- Track asset references and dependencies

**For Story Board System:**

- Visualize displayable hierarchies and compositions
- Show visual state changes and dynamic content
- Map visual effects and their timing
- Display asset organization and relationships

**For Gallery Widget:**

- Learn from VN image organization strategies
- Implement similar visual composition techniques
- Apply displayable optimization strategies
- Use dynamic displayable patterns for adaptive content

### Asset Management Integration

**Asset Tracking:**

- Catalog all image assets used in displayables
- Map asset dependencies and relationships
- Track optimization settings and configurations
- Identify missing or placeholder assets

**Visual Composition Analysis:**

- Understand how VNs compose complex visuals
- Learn layout strategies and responsive design
- Extract visual effect implementations
- Map visual state management patterns

**Performance Pattern Learning:**

- Identify optimization strategies used by VNs
- Learn memory management techniques
- Understand prediction and caching strategies
- Apply performance patterns to TPT development

This comprehensive understanding of Ren'Py's displayable system enables The Plot Thickens to effectively analyze the visual construction of visual novels, understand creative visual programming techniques, and potentially implement similar approaches for enhanced visual narrative management.
