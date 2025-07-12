# Ren'Py Transforms

> **Fetched from:** https://www.renpy.org/doc/html/transforms.html  
> **Date:** January 2025  
> **Purpose:** Understanding positioning, animation, and visual dynamics for The Plot Thickens project

# Transforms

Transforms are used to turn a displayable into another displayable. There are several kinds of transforms, and various ways to create them. The built-in transforms are used to control where an image is placed on the screen, while user-defined transforms can cause more complex effects, like motion, zoom, rotation, and complex color effects.

Transforms can be applied to images by passing them to the at clause of the show or scene statements:

```renpy
show eileen happy at right
```

Multiple transforms can be applied by separating them with commas. These transforms are applied from left-to-right:

```renpy
show eileen happy at halfsize, right
```

## Applying Transforms in Python

There are several ways to apply transform `t` to displayable `d` in Python:

1. **Most universal:** `At(d, t)` - works with all transforms
2. **ATL transforms:** `d(child=t)` - works with all ATL transforms
3. **Python transforms:** `t(d)` - works with all Python transforms and ATL transforms without positional parameters

**At(d, \*args)**
: Given a displayable d, applies each of the transforms in args to it. The transforms are applied in left-to-right order.

```renpy
transform birds_transform:
    xpos -200
    linear 10 xpos 800
    pause 20
    repeat

image birds = At("birds.png", birds_transform)
```

## Built-in Transforms

Ren'Py ships with a number of transforms defined by default. These transforms position things on the screen:

```
+-----------------------------------------------------------+
|topleft, reset         top              topright         |
|                                                          |
|                                                          |
|                                                          |
|                   truecenter                            |
|                                                          |
|                                                          |
|                                                          |
|                                                          |
offscreenleft|left    center, default    right|offscreenright
+-----------------------------------------------------------+
```

### Available Built-in Transforms:

**center**
: Centers horizontally, and aligns to the bottom of the screen.

**default**
: Centers horizontally, and aligns to the bottom of the screen. Can be redefined via config.default_transform.

**left**
: Aligns to the bottom-left corner of the screen.

**right**
: Aligns to the bottom-right corner of the screen.

**top**
: Centers horizontally, and aligns to the top of the screen.

**topleft**
: Aligns to the top-left corner of the screen.

**topright**
: Aligns to the top-right corner of the screen.

**truecenter**
: Centers both horizontally and vertically.

**offscreenleft**
: Places the displayable off the left side of the screen, aligned to the bottom.

**offscreenright**
: Places the displayable off the right side of the screen, aligned to the bottom.

**reset**
: Resets the transform to default values, removing any properties set before it.

## ATL - Animation and Transformation Language

The Animation and Transformation Language (ATL) is a high-level language for creating animations, moving displayables across the screen, setting their position, applying transformations, and more.

### Transform Statement

The transform statement creates a new transform:

```renpy
transform left_to_right:
    xalign 0.0
    linear 2 xalign 1.0
    repeat

transform ariana.left:
    xalign .3

transform animated_ariana_disp:
    "ariana"
    pause 1.0
    "ariana_reverse"
    pause 1.0
    repeat
```

### Image Statement with ATL Block

```renpy
image animated_ariana_img:
    "ariana"
    pause 1.0
    "ariana_reverse"
    pause 1.0
    repeat
```

### Scene and Show Statements with ATL Block

```renpy
show eileen happy:
    xalign 1.0

scene bg washington:
    zoom 2.0
```

## ATL Statement Types

### Contains Statement

Sets or replaces the child of the current ATL transform:

```renpy
transform an_animation:
    "1.png"
    pause 2
    "2.png"
    pause 2
    repeat

image move_an_animation:
    contains an_animation
    xalign 0.0
    linear 1.0 yalign 1.0
```

### Number Statement (Pause)

Pauses execution for a specified number of seconds:

```renpy
image atl_example:
    contains "logo_base.png"
    pause 1.0  # or just: 1.0
    "logo_bw.png" with Dissolve(0.5, alpha=True)
    3  # Pause for 3 seconds
    repeat
```

### Properties Statement

Sets one or more transform properties to new values:

```renpy
transform rightoid:
    xalign .9

transform ariana.left:
    xanchor .3
    xpos 100
```

### Interpolation Statement

The main way of creating smooth animations:

```renpy
show logo base:
    # Show at upper right
    xalign 1.0 yalign 0.0

    # Take 1.0 seconds to move left
    linear 1.0 xalign 0.0

    # Use ease warper to move to center
    ease 1.0 truecenter

    # Circular motion with multiple circles
    anchor (0.5, 0.5)
    linear 2.0 yalign 0.0 clockwise circles 3

    # Spline motion with control knots
    linear 2.0 align (0.5, 1.0) knot (0.0, .33) knot (1.0, .66)

    # Multiple properties at once
    linear 2.0 xalign 1.0 yalign 1.0
```

### Parallel Statement

Executes multiple ATL blocks simultaneously:

```renpy
show logo base:
    parallel:
        xalign 0.0
        linear 1.3 xalign 1.0
        linear 1.3 xalign 0.0
        repeat
    parallel:
        yalign 0.0
        linear 1.6 yalign 1.0
        linear 1.6 yalign 0.0
        repeat
```

### Choice Statement

Randomly selects from multiple options:

```renpy
image eileen random:
    choice:
        "eileen happy"
    choice:
        "eileen vhappy"
    choice:
        "eileen concerned"
    pause 1.0
    repeat
```

### Repeat Statement

Causes the block to resume execution from the beginning:

```renpy
show logo base:
    xalign 0.0
    linear 1.0 xalign 1.0
    linear 1.0 xalign 0.0
    repeat  # Infinite loop

# or with count:
show logo:
    xalign 0.0
    linear 1.0 xalign 1.0
    repeat 2  # Execute at most twice total
```

### Block Statement

Groups statements for organization:

```renpy
show logo base:
    alpha 0.0
    xalign 0.0
    yalign 0.0
    linear 1.0 alpha 1.0
    block:
        linear 1.0 xalign 1.0
        linear 1.0 xalign 0.0
        repeat
```

### Animation Statement

Tells Ren'Py that the block uses the animation timebase:

```renpy
image eileen happy moving:
    animation
    "eileen happy"
    xalign 0.0
    linear 5.0 xalign 1.0
    repeat

image eileen vhappy moving:
    animation
    "eileen vhappy"
    xalign 0.0
    linear 5.0 xalign 1.0
    repeat
```

### On Statement (Event Handlers)

Defines event handlers for transforms:

```renpy
show logo base:
    on show:
        alpha 0.0
        linear .5 alpha 1.0
    on hide:
        linear .5 alpha 0.0

transform pulse_button:
    on hover, idle:
        linear .25 zoom 1.25
        linear .25 zoom 1.0
```

### Time Statement

Transfers control at specific times:

```renpy
image backgrounds:
    "bg band"
    xoffset 0
    block:
        linear 1 xoffset 10
        linear 1 xoffset 0
        repeat
    # Control transfers here at 2 seconds
    time 2.0
    xoffset 0
    "bg whitehouse"
    time 4.0
    "bg washington"
```

### Function Statement

Allows ATL to use Python code:

```renpy
init python:
    def slide_vibrate(trans, st, at, /):
        if st > 1.0:
            trans.xalign = 1.0
            trans.yoffset = 0
            return None
        else:
            trans.xalign = st
            trans.yoffset = random.randrange(-10, 11)
            return 0

show logo base:
    function slide_vibrate
    pause 1.0
    repeat
```

## External Events

The following events are triggered automatically:

**start**
: Triggered on entering an on statement (pseudo-event)

**show**
: Triggered when transform is shown with show/scene and no existing tag

**replace**
: Triggered when transform replaces an existing image with the same tag

**hide**
: Triggered when transform is hidden with hide statement

**replaced**
: Triggered when the transform is replaced by another

**hover, idle, selected_hover, selected_idle, insensitive, selected_insensitive**
: Triggered when button states change

## Warpers

Warpers are functions that change the timing of interpolations. They map time t (0.0 to 1.0) to t' (also 0.0 to 1.0 but can exceed).

### Built-in Warpers:

**pause**
: Pause, then jump to new value. If t == 1.0, t' = 1.0. Otherwise, t' = 0.0.

**linear**
: Linear interpolation. t' = t

**ease**
: Start slow, speed up, then slow down. t' = .5 - math.cos(math.pi \* t) / 2.0

**easein**
: Start fast, then slow down. t' = math.cos((1.0 - t) \* math.pi / 2.0)

**easeout**
: Start slow, then speed up. t' = 1.0 - math.cos(t \* math.pi / 2.0)

### Robert Penner's Easing Functions:

| Ren'Py Name  | Effect                  |
| ------------ | ----------------------- |
| ease_back    | Overshoots then settles |
| ease_bounce  | Bouncing effect         |
| ease_circ    | Circular motion curve   |
| ease_cubic   | Cubic curve             |
| ease_elastic | Elastic/spring effect   |
| ease_expo    | Exponential curve       |
| ease_quad    | Quadratic curve         |
| ease_quart   | Quartic curve           |
| ease_quint   | Quintic curve           |

Add "in" or "out" prefixes for variations:

- `easein_*` - Start fast, slow down
- `easeout_*` - Start slow, speed up

### Custom Warpers:

```renpy
python early hide:
    @renpy.atl_warper
    def custom_warper(t):
        return t * t  # Quadratic

transform custom_move:
    xpos 0
    warp custom_warper 5 xpos 520
```

## Parameter Passing and Currying

ATL transforms can have parameters set at different times:

```renpy
transform screamer(child, screamee, wait_time=2, flash_time=.1):
    child
    pause wait_time
    screamee
    pause flash_time
    child

# Partial parameter setting
define shorter_screamer = screamer(wait_time=1)
define eileen_excited_screamer = screamer(screamee="eileen excited", flash_time=.2)

label start:
    show hannah happy at screamer(screamee="hannah surprised", wait_time=1.5)
    show eileen vhappy at eileen_excited_screamer
    show patricia sad at eileen_excited_screamer(screamee="patricia wow")
```

### Special Child Parameter

If an ATL transform has a parameter named "child", it automatically sets the child of the transform:

```renpy
transform lucy_jump_scare(child):
    # The child is implicitly set as the child of the transform
    pause 5
    # Jump scare
    "lucy mad"
    pause .2
    # Go back to the original child
    child

transform marquee(width, height=1.0, duration=2.0, child=None):
    xcenter 0.5
    ycenter 0.5
    crop (0, 0, 0.5, 500)
    contains:
        child
        xanchor 0.0
        xpos 1.0
        linear duration xanchor 1.0 xpos 0.0
```

## Transform Property Inheritance

When transforms are replaced, properties are inherited from the old transform to the new one. This applies to:

- ATL transforms
- Built-in transforms
- Transform class instances

Position properties (xpos, ypos, xanchor, yanchor, etc.) have special inheritance rules where child values override parent values.

---

**Key Points for The Plot Thickens:**

1. **Scene Positioning**: Built-in transforms provide standard positioning patterns (left, right, center, etc.)
2. **Animation Analysis**: ATL statements reveal how objects move and change over time
3. **Timing Control**: Understanding warpers and interpolation for smooth transitions
4. **Event-Driven Behavior**: On statements show how transforms respond to user interactions
5. **Parallel Operations**: Multiple simultaneous animations and transformations
6. **State Management**: Transform properties and inheritance patterns
7. **Dynamic Behavior**: Function statements for complex, code-driven animations
8. **Conditional Animation**: Choice statements for randomized or conditional effects

This transform system is essential for understanding how Ren'Py projects create dynamic visual presentations and manage complex scene transitions.
