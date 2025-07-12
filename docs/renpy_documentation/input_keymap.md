# Input and Keymap System

Ren'Py's keymap system provides comprehensive control over input handling, allowing developers to customize keyboard, mouse, and gamepad bindings. The system maps physical input events to logical game actions.

## Keymap Overview

The `config.keymap` dictionary maps event names to lists of keysyms (key symbols) that trigger those events.

**Important Note**: Many players expect standard Ren'Py keybindings. Consider carefully before changing default controls.

## Keysym Types

### Mouse Buttons

Format: `'mousedown_#'` or `'mouseup_#'` where # is button number

```python
'mousedown_1'    # Left mouse button press
'mouseup_1'      # Left mouse button release
'mousedown_2'    # Middle mouse button press
'mousedown_3'    # Right mouse button press
'mousedown_4'    # Scroll wheel up
'mousedown_5'    # Scroll wheel down
```

### Keyboard Characters

Direct character strings (case-sensitive):

```python
'a'              # Lowercase 'a' key
'A'              # Uppercase 'A' (Shift+a)
'7'              # Number 7 key
' '              # Space bar (character)
```

### Keyboard Symbolic Names

Pygame K\_ constants for special keys:

```python
'K_BACKSPACE'    # Backspace key
'K_RETURN'       # Enter key
'K_TAB'          # Tab key
'K_ESCAPE'       # Escape key
'K_SPACE'        # Space bar (symbolic)
'K_LEFT'         # Left arrow
'K_RIGHT'        # Right arrow
'K_UP'           # Up arrow
'K_DOWN'         # Down arrow
'K_F1'           # F1 function key
'K_DELETE'       # Delete key
```

## Modifier Prefixes

Combine modifiers with underscores before the main keysym:

### Modifier Keys

```python
'alt_K_RETURN'     # Alt + Enter
'ctrl_K_s'         # Ctrl + S
'shift_K_TAB'      # Shift + Tab
'meta_K_LEFT'      # Meta/Cmd + Left (Mac Command key)
```

### Modifier Combinations

```python
'shift_alt_K_F5'   # Shift + Alt + F5
'ctrl_shift_K_s'   # Ctrl + Shift + S
```

### Special Modifiers

```python
'osctrl_K_c'       # Platform-appropriate: Alt on Mac, Ctrl elsewhere
'anymod_K_SPACE'   # Matches regardless of modifier state
'noshift_K_h'      # Matches only when Shift is NOT pressed
```

### Key State Modifiers

```python
'caps_K_a'         # When Caps Lock is on
'nocaps_K_a'       # When Caps Lock is off
'num_K_1'          # When Num Lock is on
'nonum_K_1'        # When Num Lock is off
'repeat_K_LEFT'    # Key repeat (held down)
'anyrepeat_K_LEFT' # Initial press or repeat
'keydown_K_SPACE'  # Key press (default)
'keyup_K_SPACE'    # Key release
```

## Default Keymap

### Core Navigation

```python
config.keymap = {
    # Rollback (undo)
    'rollback': [
        'anyrepeat_K_PAGEUP',
        'anyrepeat_KP_PAGEUP',
        'K_AC_BACK',           # Android back
        'mousedown_4'          # Scroll wheel up
    ],

    # Advance dialogue
    'dismiss': [
        'K_RETURN',
        'K_SPACE',
        'K_KP_ENTER',
        'K_SELECT',
        'mouseup_1'            # Left click
    ],

    # Roll forward (redo)
    'rollforward': [
        'anyrepeat_K_PAGEDOWN',
        'anyrepeat_KP_PAGEDOWN',
        'mousedown_5'          # Scroll wheel down
    ],

    # Game menu
    'game_menu': [
        'K_ESCAPE',
        'K_MENU',
        'K_PAUSE',
        'mouseup_3'            # Right click
    ]
}
```

### System Controls

```python
# Screenshots
'screenshot': [
    'alt_K_s',
    'alt_shift_K_s',
    'noshift_K_s'
],

# Fullscreen toggle
'toggle_fullscreen': [
    'alt_K_RETURN',
    'alt_K_KP_ENTER',
    'K_F11',
    'noshift_K_f'
],

# Hide UI
'hide_windows': [
    'mouseup_2',           # Middle click
    'noshift_K_h'
],

# Skip text
'skip': [
    'anymod_K_LCTRL',      # Left Ctrl
    'anymod_K_RCTRL'       # Right Ctrl
],

'toggle_skip': ['K_TAB'],
'fast_skip': ['>', 'shift_K_PERIOD']
```

### Input Controls

```python
# Text input
'input_backspace': ['anyrepeat_K_BACKSPACE'],
'input_enter': ['K_RETURN', 'K_KP_ENTER'],
'input_left': ['anyrepeat_K_LEFT', 'anyrepeat_KP_LEFT'],
'input_right': ['anyrepeat_K_RIGHT', 'anyrepeat_KP_RIGHT'],
'input_delete': ['anyrepeat_K_DELETE', 'anyrepeat_KP_DELETE'],
'input_home': ['K_HOME', 'KP_HOME', 'meta_K_LEFT'],
'input_end': ['K_END', 'KP_END', 'meta_K_RIGHT'],

# Clipboard operations
'input_copy': [
    'ctrl_noshift_K_INSERT',
    'ctrl_noshift_K_c',
    'meta_noshift_K_c'     # Mac Command+C
],
'input_paste': [
    'shift_K_INSERT',
    'ctrl_noshift_K_v',
    'meta_noshift_K_v'     # Mac Command+V
],

# Word navigation
'input_jump_word_left': ['osctrl_K_LEFT', 'osctrl_KP_LEFT'],
'input_jump_word_right': ['osctrl_K_RIGHT', 'osctrl_KP_RIGHT'],
'input_delete_word': ['osctrl_K_BACKSPACE'],
'input_delete_full': ['meta_K_BACKSPACE']
```

### Focus Navigation

```python
'focus_left': ['anyrepeat_K_LEFT', 'anyrepeat_KP_LEFT'],
'focus_right': ['anyrepeat_K_RIGHT', 'anyrepeat_KP_RIGHT'],
'focus_up': ['anyrepeat_K_UP', 'anyrepeat_KP_UP'],
'focus_down': ['anyrepeat_K_DOWN', 'anyrepeat_KP_DOWN']
```

### Development Tools

```python
'reload_game': ['alt_K_r', 'shift_K_r'],
'launch_editor': ['shift_K_e'],
'inspector': ['alt_noshift_K_i', 'shift_K_i'],
'console': ['shift_K_o', 'alt_shift_K_o'],
'developer': ['alt_K_d', 'shift_K_d']
```

## Gamepad Support

### Gamepad Keysyms

Format: `'pad_*button*_press'` or `'pad_*button*_release'`

```python
config.pad_bindings = {
    # Navigation
    'pad_dpleft_press': ['focus_left', 'bar_left', 'viewport_leftarrow'],
    'pad_dpright_press': ['focus_right', 'bar_right', 'viewport_rightarrow'],
    'pad_dpup_press': ['focus_up', 'bar_up', 'viewport_uparrow'],
    'pad_dpdown_press': ['focus_down', 'bar_down', 'viewport_downarrow'],

    # Analog sticks
    'pad_leftx_neg': ['focus_left', 'bar_left', 'viewport_leftarrow'],
    'pad_leftx_pos': ['focus_right', 'bar_right', 'viewport_rightarrow'],
    'pad_lefty_neg': ['focus_up', 'bar_up', 'viewport_uparrow'],
    'pad_lefty_pos': ['focus_down', 'bar_down', 'viewport_downarrow'],

    # Action buttons
    'pad_a_press': ['dismiss', 'button_select', 'bar_activate'],
    'pad_b_press': ['game_menu'],
    'pad_x_press': ['button_alternate'],
    'pad_y_press': ['hide_windows'],

    # Triggers and shoulders
    'pad_leftshoulder_press': ['rollback'],
    'pad_rightshoulder_press': ['rollforward'],
    'pad_righttrigger_pos': ['dismiss', 'button_select'],

    # System buttons
    'pad_start_press': ['game_menu'],
    'pad_back_press': ['rollback'],

    # Repeat versions for held buttons
    'repeat_pad_leftshoulder_press': ['rollback'],
    'repeat_pad_rightshoulder_press': ['rollforward']
}
```

### Gamepad Configuration

```python
# Disable problematic controllers
config.controller_blocklist = [
    "Nintendo Switch Pro Controller"  # Requires special initialization
]
```

## Customizing Keymaps

### Adding Bindings

```python
init python:
    # Add 't' key to dismiss dialogue
    config.keymap['dismiss'].append('K_t')

    # Add multiple bindings
    config.keymap['screenshot'].extend(['F12', 'ctrl_shift_K_s'])
```

### Removing Bindings

```python
init python:
    # Remove space bar from dismiss
    config.keymap['dismiss'].remove('K_SPACE')

    # Clear all bindings for an action
    config.keymap['fast_skip'] = []
```

### Creating Custom Actions

```python
init python:
    # Define new action
    config.keymap['custom_action'] = ['K_F9', 'ctrl_K_q']

# Handle in screen or label
screen my_screen():
    key "custom_action" action Return("custom_triggered")
```

### Platform-Specific Bindings

```python
init python:
    import platform

    if platform.system() == "Darwin":  # Mac
        config.keymap['copy'] = ['meta_K_c']
        config.keymap['paste'] = ['meta_K_v']
    else:  # Windows/Linux
        config.keymap['copy'] = ['ctrl_K_c']
        config.keymap['paste'] = ['ctrl_K_v']
```

## Advanced Keymap Techniques

### Conditional Keymaps

```python
init python:
    def update_keymap_for_mode(mode):
        if mode == "battle":
            config.keymap['attack'] = ['K_SPACE', 'mousedown_1']
            config.keymap['defend'] = ['K_LSHIFT', 'mousedown_3']
        else:
            # Remove battle keys
            config.keymap.pop('attack', None)
            config.keymap.pop('defend', None)

        # Clear cache to apply changes
        renpy.clear_keymap_cache()
```

### Input Context Management

```python
screen game_screen():
    # Different contexts have different key meanings
    if game_mode == "dialogue":
        key "K_SPACE" action Return("next")
    elif game_mode == "menu":
        key "K_SPACE" action Return("select")
    elif game_mode == "battle":
        key "K_SPACE" action Return("attack")
```

### Custom Input Handlers

```python
init python:
    class CustomInput(renpy.Displayable):
        def __init__(self, **kwargs):
            super(CustomInput, self).__init__(**kwargs)

        def event(self, ev, x, y, st):
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_F1:
                    return "help_requested"
                elif ev.key == pygame.K_F2:
                    return "save_quick"

            # Let other handlers process the event
            raise renpy.IgnoreEvent()
```

## Accessibility Features

### Voice and Audio Cues

```python
'self_voicing': ['alt_K_v', 'K_v'],
'clipboard_voicing': ['alt_shift_K_c', 'shift_K_c'],
'accessibility': ['shift_K_a']
```

### Alternative Input Methods

```python
# Support for various input devices
'dismiss_unfocused': [],  # For touch devices
'button_ignore': ['mousedown_1'],  # Ignore accidental presses
'extra_voicing': ['?']  # Additional accessibility help
```

## Best Practices

### Design Principles

- Maintain familiar controls when possible
- Provide alternative input methods
- Consider different platforms and input devices
- Test with actual players using different input methods

### Implementation Guidelines

- Use `init python:` blocks for keymap modifications
- Call `renpy.clear_keymap_cache()` after runtime changes
- Provide visual feedback for custom key bindings
- Document custom controls for players

### Testing Strategies

- Test on multiple platforms (Windows, Mac, Linux)
- Verify gamepad functionality if supported
- Check accessibility features work correctly
- Ensure key combinations don't conflict with system shortcuts

The keymap system provides extensive customization while maintaining the familiar Ren'Py input experience. Understanding these patterns enables creation of accessible, intuitive control schemes for any type of visual novel or interactive experience.
