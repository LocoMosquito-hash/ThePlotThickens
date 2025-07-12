# Creator-Defined Displayables

Creator-Defined Displayables (CDD) are the most advanced way to customize Ren'Py's behavior, allowing developers to create complex interactive elements, 2D mini-games, and custom visual systems. They provide complete control over pygame events, rendering, and displayable placement.

## Overview

Creator-defined displayables are Python classes that inherit from `renpy.Displayable`. They can:

- Handle arbitrary pygame events
- Render other displayables at custom locations
- Create interactive mini-games and complex UI elements
- Implement custom visual effects and animations
- Build sophisticated user interface components

**Prerequisites**: Strong object-oriented Python programming skills are essential for effective CDD development.

## Basic Example: Distance-Based Alpha Effect

```python
init python:
    import math

    class Appearing(renpy.Displayable):
        def __init__(self, child, opaque_distance, transparent_distance, **kwargs):
            # Initialize parent class
            super(Appearing, self).__init__(**kwargs)

            # Store configuration
            self.child = renpy.displayable(child)
            self.opaque_distance = opaque_distance
            self.transparent_distance = transparent_distance

            # State variables
            self.alpha = 0.0
            self.width = 0
            self.height = 0

        def render(self, width, height, st, at):
            # Create transform with current alpha
            t = Transform(child=self.child, alpha=self.alpha)

            # Render child with transform
            child_render = renpy.render(t, width, height, st, at)
            self.width, self.height = child_render.get_size()

            # Create and return our render
            render = renpy.Render(self.width, self.height)
            render.blit(child_render, (0, 0))
            return render

        def event(self, ev, x, y, st):
            # Calculate distance from center
            distance = math.hypot(x - (self.width / 2), y - (self.height / 2))

            # Determine alpha based on distance
            if distance <= self.opaque_distance:
                alpha = 1.0
            elif distance >= self.transparent_distance:
                alpha = 0.0
            else:
                alpha = 1.0 - (distance - self.opaque_distance) / (self.transparent_distance - self.opaque_distance)

            # Trigger redraw if alpha changed
            if alpha != self.alpha:
                self.alpha = alpha
                renpy.redraw(self, 0)

            # Pass event to child
            return self.child.event(ev, x, y, st)

        def visit(self):
            return [self.child]

# Usage in screen
screen alpha_magic:
    add Appearing("logo.png", 100, 200):
        xalign 0.5
        yalign 0.5
```

## renpy.Displayable Class

### Constructor

```python
class renpy.Displayable:
    def __init__(self, **properties):
        # Pass unknown keyword arguments to parent
        super(MyDisplayable, self).__init__(**properties)
```

### Core Methods

#### render(self, width, height, st, at)

**Required override** - Returns a `renpy.Render` object defining what appears on screen.

**Parameters:**

- `width, height`: Available space in pixels
- `st`: Shown timebase (seconds since first display)
- `at`: Animation timebase (seconds since image with same tag was shown)

**Usage Patterns:**

```python
def render(self, width, height, st, at):
    # Create child renders
    child_render = renpy.render(self.child, width, height, st, at)

    # Create our render
    render = renpy.Render(width, height)
    render.blit(child_render, (0, 0))

    return render
```

#### event(self, ev, x, y, st)

Handles pygame events. Return non-None to end interaction with that value.

**Parameters:**

- `ev`: Pygame event object
- `x, y`: Event coordinates relative to displayable's upper-left
- `st`: Shown timebase

**Event Handling Patterns:**

```python
def event(self, ev, x, y, st):
    # Handle specific events
    if ev.type == pygame.MOUSEBUTTONDOWN:
        if self.hit_test(x, y):
            return "clicked"

    # Ignore event without passing to others
    raise renpy.IgnoreEvent()

    # Pass to child (most common)
    return self.child.event(ev, x, y, st)
```

#### visit(self)

Returns list of child displayables for proper lifecycle management.

```python
def visit(self):
    return [self.child1, self.child2]  # All child displayables
```

#### per_interact(self)

Called at start of each interaction. Use for triggering redraws.

## renpy.Render Class

### Creation and Basic Operations

```python
# Create render
render = renpy.Render(width, height)

# Draw child renders
render.blit(source_render, (x, y), main=True)

# Place displayables with automatic positioning
render.place(displayable, x, y, width, height, st=st, at=at)

# Get render size
width, height = render.get_size()
```

### Advanced Rendering Features

#### Canvas Operations

```python
def render(self, width, height, st, at):
    render = renpy.Render(width, height)
    canvas = render.canvas()

    # Drawing operations (pygame.draw methods without surface parameter)
    canvas.rect("#FF0000", (10, 10, 100, 50))
    canvas.circle("#00FF00", (50, 50), 25)
    canvas.line("#0000FF", (0, 0), (100, 100), 3)

    return render
```

#### Subsurfaces and Clipping

```python
# Create subsurface (clipped region)
sub_render = main_render.subsurface((x, y, width, height))

# Zoom children (not coordinates)
render.zoom(xzoom, yzoom)
```

### Model-Based Rendering (Advanced)

```python
def render(self, width, height, st, at):
    render = renpy.Render(width, height)

    # Enable model-based rendering
    render.mesh = True

    # Add shaders and uniforms
    render.add_shader("vertex_shader")
    render.add_uniform("time", st)
    render.add_property("blend_mode", "multiply")

    return render
```

## Utility Functions

### Core Utilities

```python
# Convert to displayable
d = renpy.displayable("image.png")

# End interaction immediately
renpy.end_interaction("return_value")

# Check pixel opacity
is_opaque = renpy.is_pixel_opaque(displayable, width, height, st, at, x, y)

# Load images
render = renpy.load_image(image_manipulator)
surface = renpy.load_surface(image_manipulator)

# Event mapping
if renpy.map_event(ev, "mousedown_1"):
    # Handle left click
```

### Timing and Updates

```python
# Schedule timeout event
renpy.timeout(seconds)

# Schedule redraw
renpy.redraw(self, when_seconds)

# Trigger immediate redraw
renpy.redraw(self, 0)
```

## Advanced Patterns

### Interactive Game Element

```python
class MiniGame(renpy.Displayable):
    def __init__(self, **kwargs):
        super(MiniGame, self).__init__(**kwargs)
        self.player_pos = [100, 100]
        self.game_state = "playing"

    def render(self, width, height, st, at):
        render = renpy.Render(width, height)

        # Draw game background
        bg = renpy.render(Solid("#001122"), width, height, st, at)
        render.blit(bg, (0, 0))

        # Draw player
        player = renpy.render(Solid("#FF0000"), 20, 20, st, at)
        render.blit(player, self.player_pos)

        return render

    def event(self, ev, x, y, st):
        if self.game_state != "playing":
            return None

        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_LEFT:
                self.player_pos[0] = max(0, self.player_pos[0] - 10)
                renpy.redraw(self, 0)
            elif ev.key == pygame.K_RIGHT:
                self.player_pos[0] = min(780, self.player_pos[0] + 10)
                renpy.redraw(self, 0)
```

### Dynamic Layout Manager

```python
class FlexLayout(renpy.Displayable):
    def __init__(self, children, direction="horizontal", **kwargs):
        super(FlexLayout, self).__init__(**kwargs)
        self.children = [renpy.displayable(c) for c in children]
        self.direction = direction

    def render(self, width, height, st, at):
        # Calculate child sizes and positions
        if self.direction == "horizontal":
            child_width = width // len(self.children)
            render = renpy.Render(width, height)

            for i, child in enumerate(self.children):
                child_render = renpy.render(child, child_width, height, st, at)
                render.blit(child_render, (i * child_width, 0))

        return render

    def visit(self):
        return self.children
```

## Best Practices

### Performance Optimization

- Cache expensive calculations in `per_interact()`
- Use `renpy.redraw()` strategically, not excessively
- Prefer smaller render sizes when possible
- Reuse render objects when state hasn't changed

### Event Handling

- Always handle coordinate systems relative to displayable
- Use `raise renpy.IgnoreEvent()` to ignore without passing through
- Pass events to children when appropriate
- Return interaction values for menu/choice systems

### State Management

- Keep displayable state minimal and pickleable
- Avoid storing pygame surfaces or other non-serializable objects
- Use separate data structures for complex game state
- Consider rollback implications for stateful games

### Integration Patterns

- Wrap in Transform for positioning and basic effects
- Use with screen language for complex layouts
- Combine with ATL for animation integration
- Consider accessibility and input method compatibility

Creator-Defined Displayables provide the ultimate flexibility for custom Ren'Py experiences, from simple visual effects to complex interactive systems. They bridge the gap between Ren'Py's declarative systems and full pygame programming.
