# Ren'Py Configuration Variables

> **Fetched from:** https://www.renpy.org/doc/html/config.html  
> **Date:** January 2025  
> **Purpose:** Understanding project settings and behavior control for The Plot Thickens project

# Configuration Variables

Configuration variables control the behavior of Ren'Py's implementation, allowing Ren'Py itself to be customized in a myriad of ways. These range from the common (such as changing the screen size) to the obscure (adding new kinds of archive files).

Ren'Py's implementation makes the assumption that, once the GUI system has initialized, configuration variables will not change. Changing configuration variables outside of init blocks can lead to undefined behavior. Configuration variables are not part of the save data.

Most configuration variables are easily set using a define statement:

```renpy
define config.rollback_enabled = False
```

Dict and list variables can be populated using define or in an init python block:

```renpy
define config.preload_fonts += ["OrthodoxHerbertarian.ttf"]
define config.adjust_attributes["eileen"] = eileen_adjust_function

init python hide:
    def inter_cbk():
        # this is a terrible callback
        renpy.notify("Interacting !")
    config.interact_callbacks.append(inter_cbk)
```

## Project Info

**config.name**
: This should be a string giving the name of the game. This is included as part of tracebacks and other log files, helping to identify the version of the game being used.

**config.version**  
: This should be a string giving the version of the game. This is included as part of tracebacks and other log files, helping to identify the version of the game being used.

**config.window_icon**
: If not None, this is expected to be the filename of an image giving an icon that is used for the game's main window.

**config.window_title**
: The static portion of the title of the window containing the Ren'Py game. `_window_subtitle` is appended to this to get the full title of the window. If None, defaults to the value of config.name.

## Auto-Forward Mode

**config.afm_bonus** = 25
: The number of bonus characters added to every string when auto-forward mode is in effect.

**config.afm_callback**
: If not None, a Python function that is called to determine if it is safe to auto-forward.

**config.afm_characters** = 250
: The number of characters in a string it takes to cause the amount of time specified in the auto forward mode preference.

**config.afm_voice_delay** = .5
: The number of seconds after a voice file finishes playing before AFM can advance text.

## Callbacks

These take functions that are called when certain events occur:

**config.after_default_callbacks**
: A list of functions that are called (with no arguments) whenever default statements are processed.

**config.context_callback**
: This is a callback that is called with no arguments when Ren'Py enters a new context, such as a menu context.

**config.interact_callbacks**
: A list of functions that are called (without any arguments) when an interaction is started or restarted.

**config.label_callbacks**
: This is a list of callbacks that are called whenever a label is reached. The callbacks are called with two arguments:

- The name of the label
- True if reached through jumping/calling/new context, False otherwise

**config.periodic_callbacks**
: This is a list of functions that are called, with no arguments, at around 20Hz.

**config.python_callbacks**
: A list of functions called whenever a Python block is run outside of the init phase.

**config.scene_callbacks**
: A list of functions called when the scene statement runs. Functions are called with the layer name as argument.

**config.start_callbacks**
: A list of callback functions called after the init phase, but before the game starts.

**config.statement_callbacks**
: A list of functions called when a statement is executed. Special statement names include:

- "say" - Normal say statements
- "say-bubble" - Say statements in bubble mode
- "say-nvl" - Say statements in NVL mode
- "menu" - Normal menu statements
- "menu-nvl" - Menu statements in NVL mode

## Characters and Dialogue

**config.all_character_callbacks**
: A list of callbacks that are called by all characters. This list is prepended to the list of character-specific callbacks.

**config.character_callback**
: The default value of the callback parameter of Character.

**config.character_id_prefixes**
: Specifies a list of style property prefixes that can be given to a Character().

**config.say_allow_dismiss**
: If not None, this should be a function called when the user attempts to dismiss a say statement.

**config.say_arguments_callback**
: If not None, this should be a function that takes the speaking character, followed by positional and keyword arguments.

## Choice Menus

**config.auto_choice_delay**
: If not None, this variable gives a number of seconds that Ren'Py will pause at an in-game menu before picking a random choice.

**config.menu_arguments_callback**
: If not None, this should be a function that takes positional and/or keyword arguments called whenever a menu statement runs.

**config.menu_include_disabled** = False
: When this variable is set, choices disabled with the if statement are included as disabled buttons.

**config.narrator_menu** = True
: If true, narration inside a menu is displayed using the narrator character.

## Display

**config.screen_height** = 600
: The virtual height of the game, in pixels. Usually set by gui.init() to a much larger size.

**config.screen_width** = 800
: The virtual width of the game, in pixels. Usually set by gui.init() to a much larger size.

**config.physical_height**
: If set, this is the default height of the window containing the Ren'Py game, in pixels.

**config.physical_width**
: If set, this is the default width of the window containing the Ren'Py game, in pixels.

**config.gl_clear_color** = "#000"
: The color that the window is cleared to before images are drawn.

**config.gl_resize** = True
: Determines if the user is allowed to resize an OpenGL-drawn window.

**config.mipmap** = True
: Controls if Ren'Py generates mipmaps for images. Values: True, "auto", or False.

**config.nearest_neighbor** = False
: Uses nearest-neighbor filtering by default, to support pixel art.

## File I/O

**config.file_open_callback**
: If not None, this is a function that is called with the file name when a file needs to be opened.

**config.open_file_encoding** = False
: If not False, this is the encoding that renpy.open_file() uses when its encoding parameter is None.

## Input, Focus, and Events

**config.allow_screensaver** = True
: If True, the screensaver may activate while the game is running.

**config.controller_blocklist**
: A list of strings matched against controller GUIDs to prevent initialization.

**config.keymap**
: This variable contains a keymap giving the keys and mouse buttons assigned to each possible operation.

**config.longpress_duration** = 0.5
: The amount of time the player must press the screen for a longpress to be recognized on a touch device.

**config.pad_bindings**
: An equivalent of config.keymap for gamepads.

**config.web_input** = True
: If True, the web platform will use the browser's input system to handle renpy.input().

## Layers

**config.layers** = ['master', 'transient', 'screens', 'overlay']
: This variable gives a list of all layers that Ren'Py knows about, in display order.

**config.bottom_layers**
: List of layer names displayed beneath all other layers, not participating in transitions.

**config.top_layers**
: List of layer names displayed above all other layers, not participating in transitions.

**config.default_tag_layer** = "master"
: The layer an image is shown on if its tag is not found in config.tag_layer.

**config.tag_layer**
: A dictionary mapping image tag strings to layer name strings.

**config.transient_layers**
: List of transient layers that are cleared after each interaction.

**config.sticky_layers**
: List of layer names that take precedence when a tag is shown on them.

**config.clear_layers**
: List of layer names to clear when entering the main and game menus.

**config.context_clear_layers**
: List of layers that are cleared when entering a new context.

## Media (Music, Sound, and Video)

**config.has_music** = True
: If true, the "music" mixer is enabled.

**config.has_sound** = True  
: If true, the "sfx" mixer is enabled.

**config.has_voice** = True
: If true, the "voice" mixer is enabled.

**config.main_menu_music**
: If not None, a music file to play when at the main menu.

**config.game_menu_music**
: If not None, a music file to play when at the game menu.

**config.fadeout_audio** = 0.016
: The default audio fadeout time used when audio is stopped or changed.

**config.play_channel** = "audio"
: The name of the audio channel used by renpy.play(), hover_sound, and activate_sound.

**config.auto_channels**
: Used to define automatic audio channels. Maps channel names to (mixer, prefix, suffix) tuples.

**config.movie_mixer** = "music"
: The mixer that is used when a Movie() automatically defines a channel for video playback.

**config.skip_sounds** = False
: If True, non-looping audio will not be played when Ren'Py is skipping.

## Mouse

**config.mouse**
: This variable controls the use of user-defined mouse cursors. If None, the system mouse is used.

**config.mouse_displayable**
: If not None, this should either be a displayable or a callable that returns a displayable for custom mouse display.

**config.mouse_hide_time** = 30
: The mouse is hidden after this number of seconds has elapsed without any mouse input.

## Paths

**config.archives**
: A list of archive files that will be searched for images and other data.

**config.gamedir**
: The full path leading to the game's game/ directory. This is a read-only variable.

**config.savedir**
: The complete path to the directory in which the game is saved.

---

**Key Points for The Plot Thickens:**

1. **Project Analysis**: config.name, config.version, and config.gamedir provide project metadata
2. **Behavior Understanding**: Callbacks reveal how different game events are handled
3. **Display Configuration**: Screen size, layer setup, and rendering options
4. **Asset Management**: Audio/video mixer configuration and file handling
5. **Input Systems**: Keymap and controller configuration for user interaction
6. **Layer Architecture**: Understanding how visual elements are organized and displayed
7. **File Organization**: Archive systems and directory structure configuration
8. **Event Handling**: Comprehensive callback system for tracking game state changes

This configuration system provides deep insights into how Ren'Py projects are structured and behave, essential for analyzing existing projects and understanding their architecture.
