# Statement Equivalents and Python API

Ren'Py provides Python function equivalents for every statement, enabling programmatic control over the game engine. This allows dynamic behavior, conditional logic, and integration with external systems.

**Important Note**: Using Python equivalents may disable some optimizations like lint checks and prediction, potentially affecting performance and error detection.

## Dialogue System

### Basic Dialogue

```python
# Statement form
e "Hello, world."
"And then the sun exploded."

# Python equivalent
$ e("Hello, world.")
$ narrator("And then the sun exploded.")

# Alternative using renpy.say()
$ renpy.say(e, "Hello, world.")
$ renpy.say(None, "And then the sun exploded.")  # None = narrator
```

### Character Proxy Functions

Create dynamic character selection:

```python
define lucy_normal = Character("Lucy")
define lucy_evil = Character("Evil Lucy")

init python:
    def l(what, **kwargs):
        if lucy_is_evil:
            lucy_evil(what, **kwargs)
        else:
            lucy_normal(what, **kwargs)

label start:
    $ lucy_is_evil = False
    l "Usually, I feel quite normal."

    $ lucy_is_evil = True
    l "But sometimes, I get really mad!"
```

### Say Arguments and Interaction

```python
# Statement with arguments
e "Hello, world." (what_size=32)

# Python equivalent (automatic interact=True)
$ e("Hello, world.", what_size=32, interact=True)

# Manual interaction control
$ e("Hello, world.", what_size=32, interact=False)  # No interaction
$ e("Hello, world.", what_size=32)                  # interact=True implied

# Character creation with arguments
$ Character(kind=e, what_size=32)("Hello, world.")
```

### Window Management

```python
# Hide dialogue window
$ _window_hide(trans=False, auto=False)    # window hide
$ _window_hide(trans=None, auto=False)     # window hide None
$ _window_hide(auto=True)                  # window auto hide

# Show dialogue window
$ _window_show(trans=False, auto=False)    # window show
$ _window_show(trans=dissolve, auto=False) # window show dissolve
$ _window_show(auto=True)                  # window auto show

# Window control variables
$ _window = True        # Force window visible
$ _window_auto = True   # Enable automatic window management
```

## Choice Menus

### Basic Menu Creation

```python
# Statement form
menu:
    "Which direction would you like to go?"

    "East":
        jump east_path

    "West":
        jump west_path

# Python equivalent
$ narrator("Which direction would you like to go?", interact=False)
$ result = renpy.display_menu([
    ("East", "east"),
    ("West", "west")
])

if result == "east":
    jump east_path
elif result == "west":
    jump west_path
```

### Advanced Menu Options

```python
# Menu with captions (None value)
$ result = renpy.display_menu([
    ("Chapter Selection", None),  # Caption
    ("Chapter 1", "ch1"),
    ("Chapter 2", "ch2"),
    ("Chapter 3", "ch3")
])

# Menu with custom screen
$ result = renpy.display_menu([
    ("Option A", "a"),
    ("Option B", "b")
], screen="custom_choice")

# NVL-style menu
$ result = renpy.display_menu([
    ("Yes", True),
    ("No", False)
], type="nvl")

# Menu with custom layer
$ result = renpy.display_menu([
    ("Continue", "continue"),
    ("Quit", "quit")
], _layer="overlay")
```

### Choice Arguments

```python
# Menu with per-item arguments using renpy.Choice
$ result = renpy.display_menu([
    ("Attack", renpy.Choice("attack", icon="sword")),
    ("Defend", renpy.Choice("defend", icon="shield")),
    ("Magic", renpy.Choice("magic", icon="wand", disabled=not has_mana))
])
```

## Image Display

### Basic Image Operations

```python
# Statement forms
scene bg bedroom
show mary happy
hide mary
show mary sad at left

# Python equivalents
$ renpy.scene()  # Clear all images
$ renpy.show("bg bedroom")

# Combined scene statement
$ renpy.scene()
$ renpy.show("bg bedroom")
# Equivalent to: scene bg bedroom

$ renpy.show("mary happy")
$ renpy.hide("mary")
$ renpy.show("mary sad", at_list=[left])
```

### Advanced Image Display

```python
# Complex show statement
show mary happy at center, bounce behind john zorder 10 as mary_alias onlayer overlay

# Python equivalent
$ renpy.show("mary happy",
    at_list=[center, bounce],
    behind=["john"],
    zorder=10,
    tag="mary_alias",
    layer="overlay"
)

# Show expression
show expression my_displayable as temp_image

# Python equivalent
$ renpy.show("temp_image", what=my_displayable)

# Show with ATL
show mary:
    alpha 0.0
    linear 1.0 alpha 1.0

# Python equivalent
$ renpy.show("mary", atl=Transform(alpha=0.0, linear=1.0, alpha=1.0))
```

### Image Definition

```python
# Statement form
image mary happy = "mary_happy.png"

# Python equivalent
$ renpy.image("mary happy", "mary_happy.png")

# Complex image definition
$ renpy.image("mary happy", Composite(
    (800, 600),
    (0, 0), "mary_base.png",
    (300, 200), "mary_happy_face.png"
))
```

### Layer Management

```python
# Show layer at transform
show layer master at blur

# Python equivalent
$ renpy.show_layer_at([blur], layer="master")

# Camera statement
camera at shake

# Python equivalent
$ renpy.show_layer_at([shake], camera=True)

# Reset transform state
$ renpy.show_layer_at([new_transform], reset=True)

# Preserve transform state
$ renpy.show_layer_at([new_transform], reset=False)
```

### Image Queries

```python
# Get current transforms on image
transforms = renpy.get_at_list("mary")
if transforms:
    print("Mary has transforms:", transforms)

# Check what's shown
if renpy.get_at_list("mary") is not None:
    print("Mary is currently shown")
```

## Transitions

### Basic Transitions

```python
# Statement form
with dissolve

# Python equivalent
$ renpy.with_statement(dissolve)

# Force transition even if disabled
$ renpy.with_statement(dissolve, always=True)

# Check if user interrupted
interrupted = renpy.with_statement(dissolve)
if interrupted:
    "You seem impatient!"
```

## Control Flow

### Jump Operations

```python
# Statement form
jump label_name

# Python equivalent
$ renpy.jump("label_name")

# Conditional jump
if condition:
    $ renpy.jump("special_path")
```

### Call Operations

```python
# Statement form
call subroutine_label

# Python equivalent
$ renpy.call("subroutine_label")

# Call with arguments
call subroutine_label(arg1, arg2, keyword=value)

# Python equivalent
$ renpy.call("subroutine_label", arg1, arg2, keyword=value)

# Return to current statement (re-execute)
$ renpy.call("subroutine_label", from_current=True)

# Return from call
return value

# Python equivalent
$ renpy.return_statement(value)
```

## Pause and Timing

### Pause Operations

```python
# Statement forms
pause
pause 3.0

# Python equivalents
$ renpy.pause()         # Indefinite pause
$ renpy.pause(3.0)      # 3-second pause

# Advanced pause options
$ renpy.pause(
    delay=2.0,          # 2-second timeout
    predict=True,       # End when prediction complete
    modal=False,        # Continue during modal screens
    hard=False          # Allow user to interrupt (recommended)
)

# Check if user interrupted
interrupted = renpy.pause(3.0)
if interrupted:
    "You clicked to continue!"
else:
    "Time's up!"
```

## Layered Images

### Attribute-Based Images

```python
# Statement form
layeredimage mary:
    group outfit:
        attribute dress default "mary_dress.png"
        attribute uniform "mary_uniform.png"

    group expression:
        attribute happy default "mary_happy.png"
        attribute sad "mary_sad.png"

# Python equivalent
$ renpy.image("mary", LayeredImage([
    Attribute("outfit", "dress", "mary_dress.png", default=True),
    Attribute("outfit", "uniform", "mary_uniform.png"),
    Attribute("expression", "happy", "mary_happy.png", default=True),
    Attribute("expression", "sad", "mary_sad.png")
], image_format="mary_{}.png"))
```

### Conditional Displayables

```python
# Complex layered image with conditions
$ renpy.image("complex_character", LayeredImage([
    # Base layer
    Attribute(None, "base", "char_base.png", default=True),

    # Conditional clothing
    Condition("has_jacket", "char_jacket.png"),

    # Expression with transforms
    Attribute("face", "happy", "char_happy.png",
              at=[Transform(pos=(100, 50))],
              default=True),

    # Outfit variations
    Attribute("outfit", "casual", "char_casual.png", default=True),
    Attribute("outfit", "formal", "char_formal.png"),

    # When conditions
    Attribute("special", "glow", "char_glow.png",
              when="has_power and not is_tired")
]))
```

## Advanced Patterns

### Dynamic Character Creation

```python
init python:
    def create_character(name, color="#ffffff"):
        return Character(name, color=color)

    def speak_as(char_name, text, color="#ffffff"):
        char = create_character(char_name, color)
        char(text)

# Usage
$ speak_as("Mysterious Voice", "Who goes there?", "#ff0000")
```

### Conditional Dialogue Systems

```python
init python:
    def mood_dialogue(character, happy_text, sad_text):
        if character.mood == "happy":
            character(happy_text)
        else:
            character(sad_text)

# Usage
$ mood_dialogue(mary, "I'm feeling great!", "I'm feeling down...")
```

### Dynamic Menu Generation

```python
init python:
    def create_location_menu(locations):
        choices = []
        for location in locations:
            if location.available:
                choices.append((location.name, location.id))

        return renpy.display_menu(choices)

# Usage
$ available_locations = [town, forest, castle]
$ choice = create_location_menu(available_locations)
```

### Image Management Systems

```python
init python:
    def show_character_emotion(character, emotion, position=center):
        # Hide current character
        renpy.hide(character)

        # Show with new emotion
        image_name = f"{character} {emotion}"
        renpy.show(image_name, at_list=[position])

# Usage
$ show_character_emotion("mary", "happy", left)
$ show_character_emotion("john", "surprised", right)
```

## Best Practices

### When to Use Python Equivalents

- Dynamic character or dialogue systems
- Complex conditional logic
- Integration with external data
- Runtime-generated content
- Advanced state management

### Performance Considerations

- Python equivalents may disable prediction
- Lint checking might not catch errors
- Some optimizations may not apply
- Test performance with real content

### Error Handling

```python
init python:
    def safe_jump(label):
        if renpy.has_label(label):
            renpy.jump(label)
        else:
            renpy.say(narrator, f"Error: Label '{label}' not found!")

    def safe_character_say(char, text):
        try:
            char(text)
        except Exception as e:
            narrator(f"Dialogue error: {e}")
```

### Integration Patterns

```python
# Combine statements and Python for best results
label dynamic_scene:
    $ character_name = determine_speaker()
    $ dialogue_text = get_localized_text()

    # Use statement form when possible
    scene bg dynamic_location

    # Use Python when necessary
    $ speak_as(character_name, dialogue_text)

    menu:
        "What do you do?"

        "Option A":
            $ handle_choice("a")

        "Option B":
            $ handle_choice("b")
```

Understanding statement equivalents enables powerful dynamic behavior while maintaining Ren'Py's visual novel strengths. Use judiciously to balance flexibility with performance and maintainability.
