# Save, Load, and Rollback System

Ren'Py provides a comprehensive save/load system with rollback functionality that allows players to save game state, load previous saves, and roll back to earlier decisions. This system is fundamental to the visual novel experience.

## What is Saved

### Internal State

Ren'Py automatically saves all internal state that changes during gameplay:

- Current statement and return stack
- Displayed images and displayables
- Active screens and their variable values
- Playing music and audio
- NVL-mode text blocks list

### Python State

Variables in the store that have **changed** since game start, plus all reachable objects:

- Variables modified after `label start`
- Objects accessible through changed variables
- Variables defined with `default` statement (always saved)

**Important**: Only variable _changes_ matter - field modifications don't trigger saves.

```python
# Example of what gets saved
define a = 1           # NOT saved (never changes)
define o = object()    # NOT saved (variable unchanged)
default c = 17         # ALWAYS saved (default statement)

label start:
    $ b = 1           # SAVED (variable changed)
    $ o.value = 42    # Object modified, but 'o' variable unchanged = NOT saved
```

## What Isn't Saved

### Variables and Objects

- Python variables unchanged after game start
- Configuration variables and styles (init-only)
- Image name mappings to displayables
- Aliased objects between saved/unsaved variables (dangerous!)

### Control Flow

- Execution path (how you got to current statement)
- Statements added mid-game won't re-execute
- Loop state in Python blocks

**Dangerous Aliasing Example:**

```python
init python:
    a = object()
    a.f = 1

label start:
    $ b = a        # 'b' is saved, 'a' is not
    $ b.f = 2      # Modifies shared object
    # Save/load may break a-b aliasing!
```

### Non-Serializable Objects

Cannot be pickled and thus cannot be saved:

- Render objects
- Iterator and generator objects
- Coroutine tasks and futures
- File-like objects and network sockets
- Inner functions and lambdas

## Save Location Rules

Saves occur at the **start** of Ren'Py statements in the outermost interaction context.

### Problematic Pattern (Python block):

```python
python:
    i = 0
    while i < 10:
        i += 1
        narrator("The count is now [i].")
    # Save/load in middle resets loop!
```

### Correct Pattern (Ren'Py statements):

```python
$ i = 0
while i < 10:
    $ i += 1
    "The count is now [i]."
    # Each statement is a save point
```

## Working with Non-Serializable Objects

### Use Python Hide Blocks

```python
# Wrong - 'f' might be saved between statements
$ f = open("file.txt", "w")
$ f.write("data")
$ f.close()

# Correct - variables in hide block aren't saved
python hide:
    f = open("file.txt", "w")
    f.write("data")
    f.close()

# Even better - with statement
python hide:
    with open("file.txt", "w") as f:
        f.write("data")
```

### Coroutines and Async

```python
# Wrong - sleep_task might be saved
$ sleep_task = sleep_func()
$ asyncio.run(sleep_task)

# Correct - not assigned to variable
$ asyncio.run(sleep_func())
```

## Save File Structure

Ren'Py save files are compressed archives containing:

### Game State

- Serialized Python objects representing game state
- All changed variables and reachable objects
- Internal Ren'Py state (images, screens, audio, etc.)

### Metadata Dictionary

Standard fields available through various access methods:

```python
# Get full metadata
metadata = renpy.slot_json("1-1")

# Standard fields
save_name = metadata.get('_save_name', '')        # User-defined name
renpy_version = metadata.get('_renpy_version')    # [8, 3, 7, 25031702]
game_version = metadata.get('_version')           # Game's config.version
runtime = metadata.get('_game_runtime')           # Seconds of user input time
created = metadata.get('_ctime')                  # Unix timestamp
```

### Custom Metadata

```python
# Add custom fields via callbacks
def save_custom_data():
    return {
        'chapter': current_chapter,
        'completion': completion_percentage,
        'difficulty': difficulty_setting
    }

define config.save_json_callbacks = [save_custom_data]

# Access custom data
metadata = renpy.slot_json("1-1")
chapter = metadata.get('chapter')
```

## Core Save/Load Functions

### Save Operations

```python
# Basic save
$ renpy.save("1-1")

# Save with name
$ save_name = "Chapter 1 - The Beginning"
$ renpy.save("1-1", extra_info=save_name)

# Save with custom metadata
$ renpy.save("1-1", extra_info="Boss Fight", extra_json={'boss': 'dragon'})

# Take screenshot before saving
$ renpy.take_screenshot()
$ renpy.save("1-1")
```

### Load Operations

```python
# Load game (never returns if successful)
$ renpy.load("1-1")

# Check if save exists
if renpy.can_load("1-1"):
    $ renpy.load("1-1")

# Get save data without loading
save_data = renpy.get_save_data("1-1")
player_name = save_data.get('player_name', 'Unknown')
```

### Save Management

```python
# List all saves
all_saves = renpy.list_slots()

# List saves matching pattern
auto_saves = renpy.list_slots("auto-")
quick_saves = renpy.list_slots("quick-")

# Find newest save
newest = renpy.newest_slot()
newest_auto = renpy.newest_slot("auto-")

# Copy and rename saves
$ renpy.copy_save("1-1", "backup-1")
$ renpy.rename_save("temp", "1-1")

# Delete save
$ renpy.unlink_save("1-1")
```

### Save Metadata Access

```python
# Get save metadata
metadata = renpy.slot_json("1-1")
if metadata:
    name = metadata.get('_save_name', 'Unnamed Save')
    time = metadata.get('_ctime')

# Get modification time
mtime = renpy.slot_mtime("1-1")

# Get save screenshot
screenshot = renpy.slot_screenshot("1-1")
```

## Rollback System

### What Data is Rolled Back

- Variables changed after init phase
- Revertible objects (lists, dicts, sets, objects from Ren'Py script)
- Objects inheriting from revertible types
- renpy.Displayable objects

### Automatic Conversions

Ren'Py automatically converts in script files:

```python
# These become revertible automatically
my_list = [1, 2, 3]           # Revertible list
my_dict = {'key': 'value'}    # Revertible dict
my_set = {1, 2, 3}           # Revertible set

# List/dict/set comprehensions
squares = [x*x for x in range(10)]  # Revertible

# Classes defined in Ren'Py scripts
class MyClass:                # Instances are revertible
    pass
```

### Non-Revertible Objects

- Objects created in pure Python code
- Built-in Python types outside script context
- Objects that can't be pickled

## Advanced Save Features

### Retain Data After Load

Preserve specific data across save/load cycles:

```python
screen edit_value:
    hbox:
        text "[value]"
        textbutton "+" action SetVariable("value", value + 1)
        textbutton "-" action SetVariable("value", value - 1)
        textbutton "Done" action Return(True)

label start:
    $ value = 0
    $ renpy.retain_after_load()  # Preserve edits across loads
    call screen edit_value
```

### Traceback Saves

Automatic saves on uncaught exceptions:

```python
# Access traceback save data
traceback = renpy.slot_json("_tracesave-1")["_traceback"]
error_data = renpy.get_save_data("_tracesave-1")
```

### Save Slot Management Patterns

```python
# Auto-save system
label auto_save:
    $ renpy.take_screenshot()
    $ renpy.save("auto-1", extra_info="Auto Save")
    return

# Quick save
$ config.keymap['save_quick'] = ['F5']

# Chapter save system
label save_chapter(chapter_name):
    $ save_name = chapter_name
    $ renpy.take_screenshot()
    $ renpy.save("story-[chapter_number]", extra_info=chapter_name)
    return
```

## Best Practices

### Save System Design

- Implement auto-save at chapter/section boundaries
- Provide multiple save slots for player choice
- Use descriptive save names with progress indicators
- Take screenshots before saving for visual identification

### Data Management

- Keep saveable state minimal and well-organized
- Avoid aliasing between saved and unsaved variables
- Use `default` for variables that should always be saved
- Place complex initialization in init blocks

### Performance Considerations

- Large save files impact load times
- Minimize deeply nested object structures
- Consider save file size when adding custom metadata
- Test save/load with realistic game state sizes

### Player Experience

- Clear save slot organization (auto, quick, manual)
- Visual save previews with screenshots
- Save metadata showing progress/location
- Confirmation for save overwrites

The save/load system is fundamental to VN player experience. Understanding its mechanics ensures reliable game state persistence and smooth player interaction with your narrative.
