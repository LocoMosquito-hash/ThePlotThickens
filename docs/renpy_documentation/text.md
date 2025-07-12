# Ren'Py Text System

## Overview

The Text system in Ren'Py is a sophisticated framework for displaying and formatting text in visual novels. It handles everything from basic text display to complex formatting, multi-language support, animations, and interactive text elements. Understanding the text system is crucial for analyzing how VNs present dialogue, UI text, and narrative content.

**Key Components:**

- **Text Displayables**: Core text rendering objects
- **Text Tags**: Inline formatting and styling
- **Interpolation**: Dynamic content insertion
- **Font Management**: Multi-language and custom font support
- **Text Processing**: Translation, formatting, and manipulation

## Text Display Process

Ren'Py processes text in the following order:

1. **Translation**: Apply language-specific text
2. **Interpolation**: Insert dynamic values and expressions
3. **Styling**: Apply styles and text tags
4. **Layout**: Position and flow text
5. **Rendering**: Draw text to screen

## Text Interpolation

Dynamic content insertion using square brackets:

### Basic Interpolation

```renpy
# Variable interpolation
define player_name = "Alex"
g "Welcome to the academy, [player_name]!"

# Expression interpolation
g "Your score is [score + bonus] points!"

# Object property access
g "Level [player.level] character with [player.health] HP."

# Complex expressions
g "Progress: [int(100.0 * current / total)]%"
```

### Interpolation Flags

```renpy
# Formatting flags (!flag format)
g "Floating point: [value:.2f]"           # Two decimal places
g "Percentage: [ratio:.1%]"                # Percentage with 1 decimal

# Conversion flags
g "Debug info: [data!r]"                   # repr() representation
g "String: [value!s]"                      # str() conversion
g "Quoted: [user_input!q]"                 # Quote text tags
g "Translated: [message!t]"                # Translate text
g "Interpolated: [template!i]"             # Recursive interpolation

# Case conversion
g "Uppercase: [text!u]"                    # UPPERCASE
g "Lowercase: [text!l]"                    # lowercase
g "Capitalized: [text!c]"                  # Capitalized
g "Lower then cap: [text!lc]"              # Lowercase then capitalize

# Combined flags
g "Final result: [message!tq]"             # Translate then quote
```

### Interpolation Scope

```renpy
# Search order:
# 1. Screen-local variables (in screens)
# 2. Interpolate namespace
# 3. Global namespace

# Custom interpolation scope
screen custom_display():
    $ local_scope = {"special_var": "custom value"}
    text "Value: [special_var]" substitute True scope local_scope
```

## Text Tags

Text tags provide inline formatting and special functionality:

### Basic Formatting Tags

```renpy
# Font styling
"{b}Bold text{/b}"
"{i}Italic text{/i}"
"{u}Underlined text{/u}"
"{s}Strikethrough text{/s}"
"{plain}Remove all formatting{/plain}"

# Size manipulation
"{size=+10}Bigger{/size} normal {size=-5}smaller{/size}"
"{size=24}Fixed size{/size}"
"{size=*1.5}1.5x bigger{/size}"

# Color and appearance
"{color=#ff0000}Red text{/color}"
"{alpha=0.5}Semi-transparent{/alpha}"
"{alpha=+0.2}More opaque{/alpha}"
"{alpha=*0.5}Half opacity{/alpha}"

# Font changes
"{font=special.ttf}Custom font{/font}"
```

### Advanced Text Tags

```renpy
# Kerning (character spacing)
"{k=2}S p a c e d{/k} normal {k=-1}tight{/k}"

# Outlines and shadows
"{outlinecolor=#000000}Black outline{/outlinecolor}"

# Spacing insertion
"Before{space=20}after the gap"
"Line 1{vspace=30}Line 2 with vertical space"

# Features (OpenType)
"{feature:liga=0}No ligatures{/feature}"
"{feature:smcp=1}Small caps{/feature}"

# Text shaders (advanced effects)
"{shader=wavy}Wavy text effect{/shader}"
```

### Interactive Text Tags

```renpy
# Hyperlinks
"Visit {a=https://renpy.org}Ren'Py's website{/a}"
"Go to {a=jump:next_scene}next scene{/a}"
"Call {a=call:subroutine}function{/a}"
"Show {a=show:inventory}inventory screen{/a}"

# Custom protocols
"Custom: {a=myprotocol:data}link{/a}"
```

### Dialogue-Specific Tags

```renpy
# Timing control
"Text appears{w} then continues{w=2.0} after 2 seconds"
"Paragraph 1{p}Paragraph 2{p=1.5}Paragraph 3 after delay"

# Auto-advance
"This line{nw}"
"This line{fast} continues immediately"

# Text completion control
"Visible text{done} invisible text after this"

# Clear (NVL mode)
"""
Block 1
Block 2
{clear}
Block 3 on new page
"""
```

### Accessibility Tags

```renpy
# Self-voicing
"Visual {image=heart.png}{alt}heart{/alt} symbol"
"Silent {noalt}<3{/noalt}{alt}heart{/alt} for screen readers"

# Translation tags (for string differentiation)
"New{#playlist} Game"  # Different from "New Game" without tag
```

### Style Tags

```renpy
# Apply named styles to text sections
"Normal {=mystyle}styled text{/=mystyle} normal"

# Multiple style properties
style mystyle:
    color "#ff0000"
    size 20
    bold True
```

## Ruby Text (Furigana)

Support for pronunciation guides and annotations:

### Setup Ruby Styles

```renpy
# Configure ruby text styling
style ruby_style is default:
    size 12
    yoffset -20
    color None  # Inherit parent color

style say_dialogue:
    ruby_line_leading 12
    ruby_style style.ruby_style

style history_text:
    ruby_line_leading 12
    ruby_style style.ruby_style
```

### Ruby Text Usage

```renpy
# Lenticular bracket method (【】)
e "Pronunciation: 【東京|とうきょう】"
e "Translation: 【東京|Tokyo】"

# Tag method
e "Kanji: 東{rt}とう{/rt}京{rt}きょう{/rt}"
e "With base: {rb}東京{/rb}{rt}Tokyo{/rt}"

# Alternate ruby
e "Main: 東京{art}Capital{/art}"
```

## Font Management

### Font Loading and Selection

```renpy
# Basic font specification
style default:
    font "fonts/main.ttf"

# Font with fallbacks
style text:
    font "custom.ttf"  # Primary font
    # Automatic fallback to system fonts

# Font collections
style special:
    font "1@collection.ttc"  # Second font in collection
```

### Font Groups (Multi-language)

```python
# Combine multiple fonts for different character ranges
init python:
    japanese_font = FontGroup().add(
        "english.ttf", 0x0020, 0x007f    # ASCII range
    ).add(
        "japanese.ttf", 0x3040, 0x309f   # Hiragana
    ).add(
        "japanese.ttf", 0x30a0, 0x30ff   # Katakana
    ).add(
        "japanese.ttf", 0x4e00, 0x9faf   # CJK ideographs
    )

style multilingual:
    font japanese_font
```

### Font Replacement

```python
# Replace font combinations with better versions
init python:
    config.font_replacement_map[
        "main.ttf", False, True  # Font, bold, italic
    ] = (
        "main-italic.ttf", False, False  # Replacement
    )
```

### Font Aliases

```python
# Create convenient font aliases
define config.font_name_map["title"] = "fancy_title.ttf"
define config.font_name_map["code"] = "monospace.ttf"

# Usage
text "Game Title" font "title"
text "Code sample" font "code"
```

### Variable Fonts

```renpy
# OpenType variable font support
style variable_text:
    font "variable.ttf"
    shaper "harfbuzz"  # Required for variable fonts
    instance "light"   # Named instance
    axis {"weight": 300, "width": 125}  # Axis values

# Text tags for variable fonts
"Normal {instance=bold}bold instance{/instance} normal"
"Normal {axis:weight=700}bold weight{/axis} normal"
```

### Image-Based Fonts

```python
# Register bitmap fonts
init python:
    # BMFont
    renpy.register_bmfont(
        name="pixel", size=16, filename="pixel.fnt"
    )

    # SFont
    renpy.register_sfont(
        name="retro", size=12, filename="retro.png",
        spacewidth=8, baseline=10
    )
```

## Language and Localization

### Language Configuration

```renpy
# Set language for line breaking
define gui.language = "japanese-loose"  # or "korean-with-spaces"

# Fast line breaking for large text
define gui.language = "greedy"
```

### Vertical Text

```renpy
# Vertical text display
style vertical_text:
    vertical True

# Mixed orientation tags
"Vertical {horiz}horizontal{/horiz} vertical"
"Horizontal {vert}vertical{/vert} horizontal"
```

## Text Displayables

### Basic Text Displayable

```python
# Create text programmatically
text_display = Text(
    "Hello World",
    size=20,
    color="#ffffff",
    slow=True,  # Typewriter effect
    scope={"custom_var": "value"},
    substitute=True  # Enable interpolation
)
```

### Parameterized Text

```renpy
# Reusable text with parameters
image dynamic_text = ParameterizedText(
    xalign=0.5,
    yalign=0.0,
    size=24
)

# Usage
show dynamic_text "Score: [score]" at center
```

### Text with Callbacks

```python
# Text with completion callback
def text_complete():
    renpy.notify("Text finished!")

slow_text = Text(
    "Slowly appearing text...",
    slow=True,
    slow_done=text_complete
)
```

## Advanced Text Features

### Custom Text Tags

```python
# Define custom text tag behavior
init python:
    def custom_tag(tag, argument, contents):
        if tag == "rainbow":
            # Implement rainbow text effect
            return [(renpy.TEXT_TAG, "color=#ff0000")] + contents + [(renpy.TEXT_TAG, "/color")]
        return contents

    config.custom_text_tags["rainbow"] = custom_tag

# Usage
"Normal {rainbow}colorful{/rainbow} text"
```

### Text Processing Functions

```python
# Text utility functions
filtered = renpy.filter_text_tags(
    text,
    allow={"b", "i", "color"}  # Only allow these tags
)

substituted = renpy.substitute(
    "Hello [name]",
    scope={"name": "World"}
)

transformed = renpy.transform_text(
    "Hello World",
    lambda s: s.upper()  # Transform function
)
```

### Text Overflow Detection

```renpy
# Enable text overflow logging
define config.debug_text_overflow = True

# Text with size constraints
text "Long text content...":
    xmaximum 200
    ymaximum 100
    # Will log if text exceeds bounds
```

## Performance and Optimization

### Slow Text Optimization

```renpy
# Optimize for slow text rendering
style slow_text:
    line_leading 2      # Prevent line overlap
    line_spacing 1      # Adequate line spacing
    line_overlap_split 0.5  # Handle character overlap
```

### Text Prediction

```renpy
# Control text caching and prediction
$ renpy.predict_text(["Common", "dialogue", "strings"])

# Disable prediction for dynamic text
text "[random_content()]" predict False
```

## Integration with The Plot Thickens

### Text Analysis Applications

**Dialogue Extraction:**

- Parse character dialogue and narrative text
- Identify speaker patterns and dialogue structure
- Extract text formatting and styling information
- Track language and localization usage

**Interactive Element Detection:**

- Find hyperlinks and interactive text elements
- Identify text-based navigation and choices
- Parse custom text tags and their behaviors
- Map text-driven user interactions

**Formatting Analysis:**

- Catalog text styling patterns and themes
- Identify font usage and character support
- Extract formatting conventions and standards
- Analyze accessibility features and implementations

### Source Code Integration

**For Ren'Py Source API:**

- Parse text content and extract dialogue
- Identify character speech patterns
- Extract text formatting and styling
- Track variable interpolation usage

**For Story Board System:**

- Visualize dialogue flow and character interactions
- Show text formatting and styling patterns
- Display narrative structure and pacing
- Map text-based story progression

**For Character Management:**

- Extract character dialogue and speech patterns
- Identify character-specific text styling
- Track character name and title usage
- Map character relationship indicators in text

### Text Processing for Analysis

**Content Extraction:**

- Remove formatting tags for pure text analysis
- Extract interpolated variables and expressions
- Identify translatable content and localization keys
- Parse ruby text and pronunciation guides

**Pattern Recognition:**

- Identify common text formatting patterns
- Recognize dialogue conventions and structures
- Extract narrative voice and style indicators
- Map text-based game mechanics and features

This comprehensive understanding of Ren'Py's text system enables The Plot Thickens to effectively analyze and process the textual content of visual novels, understanding both the content and the sophisticated formatting and presentation techniques used by developers.
