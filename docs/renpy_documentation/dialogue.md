# Ren'Py Dialogue and Narration

> **Fetched from:** https://www.renpy.org/doc/html/dialogue.html  
> **Date:** January 2025  
> **Purpose:** Understanding text structure and character dialogue for The Plot Thickens project

# Dialogue and Narration

Text is fundamental to visual novels, and generally quite important to storytelling-based games. This text may consist of dialogue labeled with the character that is saying it, and narration, which does not have a speaker.

In Ren'Py, most dialogue is written using say statements. The look of dialogue may be customized on a per-character basis by using Character objects.

## Say Statement

The say statement is used for dialogue and narration. Since it's almost always the most frequently used statement in Ren'Py scripts, the say statement has a syntax that minimizes the overhead in writing it. Some example say statements are:

```renpy
"This is narration."

"Eileen" "This is dialogue, with an explicit character name."

e "This is dialogue, using a character object instead."

"Bam!!" with vpunch
```

**Forms of Say Statements:**

1. **Narration**: A string by itself for narration content
2. **Explicit Character**: Two strings - first is character name, second is dialogue
3. **Character Object**: A character object followed by dialogue string
4. **With Transition**: A string with a transition effect

The usual effect of a say statement is to display dialogue on the screen until the user clicks to dismiss it, then to remove that dialogue from the screen.

### Special Characters

Certain characters have special meaning to Ren'Py:

- `{` character begins a text tag
- `[` character begins a substitution
- To use them in dialogue, double them: `{{` and `[[`

Example with special characters:

```renpy
"I walked past a sign saying, \"Let's give it 100%%!\""
```

## Defining Character Objects

By creating a Character object and using it in a say statement, you can customize the look and behavior of dialogue. Characters are created using the define statement:

```renpy
define e = Character("Eileen", who_color="#c8ffc8")
```

Once defined, the character can be used in say statements:

```renpy
e "Hello, world."
```

### Character Constructor

```python
Character(name=..., kind=adv, **args)
```

**Key Parameters:**

**name**
: If a string, the name of the character for dialogue. When name is None, display of the name is omitted, as for narration.

**kind**
: The Character to base this Character off of. Used to define template characters.

**image**
: A string giving the image tag that is linked with this character.

**voice_tag**
: A String that enables the voice file associated with the Character to be muted or played in the 'voice' channel.

### Prefixes and Suffixes

These allow text to be automatically added before and after character names and dialogue:

**what_prefix**
: A string that is prepended to the dialogue being spoken before it is shown.

**what_suffix**
: A string that is appended to the dialogue being spoken before it is shown.

**who_prefix**
: A string that is prepended to the name of the character before it is shown.

**who_suffix**
: A string that is appended to the name of the character before it is shown.

### Controlling Interactions

**condition**
: If given, this should be a string containing a Python expression. If the expression is false, the dialogue does not occur.

**interact**
: If true (default), an interaction occurs whenever the dialogue is shown. If false, additional elements can be added to the screen.

**advance**
: If true (default), the player can click to advance. If false, an alternate means must be provided.

**callback**
: A function that is called when events occur while the character is speaking.

### Click-to-Continue Indicators

**ctc**
: A displayable to use as the click-to-continue indicator.

**ctc_pause**
: A displayable for when text is paused by `{p}` or `{w}` text tags.

**ctc_position**
: Controls the location of the click-to-continue indicator:

- "nestled": Displayed as part of the text
- "nestled-close": Similar to nestled but no break allowed
- "fixed": Uses positioning from screen or displayable properties

### Example Character Definitions

```renpy
# Basic character with color
define e = Character("Eileen", who_color="#c8ffc8")

# Character with image tag
define s = Character("Sylvie", image="sylvie")

# Character with prefixes
define narrator = Character(None, what_prefix='"', what_suffix='"')

# Conditional character
define mysterious = Character("???", condition="not revealed_identity")

# Character with voice tag
define protagonist = Character("[player_name]", voice_tag="protag")
```

### Character Methods

Characters can also be called as functions to temporarily override their properties:

```renpy
# Temporarily change character color
e(who_color="#ff0000") "I'm angry!"

# Normal color resumes
e "Back to normal."
```

---

**Key Points for The Plot Thickens:**

1. **Text Structure**: Say statements are the primary dialogue mechanism
2. **Character Objects**: Reusable character definitions with customizable properties
3. **Narration vs Dialogue**: Different syntax patterns for different text types
4. **Character Linking**: Characters can be linked to image tags for automatic sprite changes
5. **Voice Integration**: Voice tags for organizing and controlling voice playback
6. **Conditional Dialogue**: Characters can have conditions controlling when they appear
7. **Text Formatting**: Support for prefixes, suffixes, and special character handling
8. **Interactive Control**: Options for controlling user interaction with dialogue

This is crucial for understanding how Ren'Py scripts structure dialogue and manage character interactions.
