# Custom Statements and Extensions

Ren'Py allows developers to create custom statements that extend the engine's capabilities beyond built-in functionality. This enables domain-specific languages, complex automation, and seamless integration of custom systems.

## Overview

Custom statements are user-defined extensions that:

- Add new syntax to Ren'Py script language
- Provide domain-specific abstractions
- Simplify complex or repetitive operations
- Integrate external systems seamlessly
- Maintain Ren'Py's declarative style

## Basic Custom Statement Structure

### Simple Statement Definition

```python
init python:
    def my_statement_function(text_value):
        # Implementation here
        renpy.say(narrator, f"Custom: {text_value}")

    # Register the statement
    renpy.register_statement("mystmt",
        parse=my_statement_parse,
        execute=my_statement_function,
        predict=my_statement_predict
    )

    def my_statement_parse(lex):
        # Parse the statement arguments
        text = lex.rest()
        return {"text": text}
```

### Statement Usage

```renpy
# In Ren'Py script
mystmt "This is my custom statement!"
```

## Advanced Statement Registration

### Complete Statement Definition

```python
init python:
    def combat_parse(lex):
        # Parse: combat enemy "goblin" health 50 attack 10
        enemy_type = lex.string()

        properties = {}
        while not lex.eol():
            key = lex.name()
            value = lex.integer() if lex.integer() else lex.string()
            properties[key] = value

        return {
            "enemy_type": enemy_type,
            "properties": properties
        }

    def combat_execute(parsed):
        enemy_type = parsed["enemy_type"]
        properties = parsed["properties"]

        # Start combat system
        combat_manager.start_battle(enemy_type, **properties)

        # Show combat screen
        renpy.call_screen("combat_interface")

    def combat_predict(parsed):
        # Predict images/sounds that will be used
        enemy_type = parsed["enemy_type"]
        renpy.predict(f"enemy_{enemy_type}.png")
        renpy.predict_sound(f"battle_{enemy_type}.ogg")

    def combat_lint(parsed):
        # Validate statement during lint checking
        enemy_type = parsed["enemy_type"]
        if not enemy_exists(enemy_type):
            renpy.error(f"Unknown enemy type: {enemy_type}")

    # Register with all handlers
    renpy.register_statement("combat",
        parse=combat_parse,
        execute=combat_execute,
        predict=combat_predict,
        lint=combat_lint
    )
```

### Usage Examples

```renpy
# Combat statement usage
combat "goblin" health 50 attack 10 speed 5
combat "dragon" health 500 attack 50 special_attack "fire_breath"
```

## Statement Categories

### Simple Action Statements

```python
# Quick save statement
init python:
    def quicksave_parse(lex):
        slot_name = lex.string() if not lex.eol() else "quick"
        return {"slot": slot_name}

    def quicksave_execute(parsed):
        slot = parsed["slot"]
        renpy.take_screenshot()
        renpy.save(f"quick_{slot}")
        renpy.notify(f"Game saved to quick slot '{slot}'")

    renpy.register_statement("quicksave",
        parse=quicksave_parse,
        execute=quicksave_execute
    )

# Usage
quicksave "before_boss"
quicksave  # Uses "quick" as default
```

### Configuration Statements

```python
# Scene mood statement
init python:
    def mood_parse(lex):
        mood_name = lex.name()

        properties = {}
        while not lex.eol():
            if lex.keyword("tint"):
                properties["tint"] = lex.string()
            elif lex.keyword("music"):
                properties["music"] = lex.string()
            elif lex.keyword("sound"):
                properties["sound"] = lex.string()
            else:
                lex.error("Unknown mood property")

        return {
            "mood": mood_name,
            "properties": properties
        }

    def mood_execute(parsed):
        mood = parsed["mood"]
        props = parsed["properties"]

        # Apply visual effects
        if "tint" in props:
            renpy.show("mood_overlay", what=Solid(props["tint"], alpha=0.3))

        # Change music
        if "music" in props:
            renpy.music.play(props["music"], fadeout=1.0, fadein=1.0)

        # Play ambient sound
        if "sound" in props:
            renpy.sound.play(props["sound"], loop=True)

    renpy.register_statement("mood",
        parse=mood_parse,
        execute=mood_execute
    )

# Usage
mood tense tint "#440000" music "tension.ogg" sound "storm.ogg"
mood peaceful tint "#004400" music "calm.ogg"
```

### Character Animation Statements

```python
# Character action statement
init python:
    def action_parse(lex):
        character = lex.name()
        action_type = lex.name()

        modifiers = {}
        while not lex.eol():
            if lex.keyword("speed"):
                modifiers["speed"] = lex.float()
            elif lex.keyword("repeat"):
                modifiers["repeat"] = lex.integer()
            elif lex.keyword("to"):
                modifiers["target"] = lex.name()

        return {
            "character": character,
            "action": action_type,
            "modifiers": modifiers
        }

    def action_execute(parsed):
        char = parsed["character"]
        action = parsed["action"]
        mods = parsed["modifiers"]

        if action == "move":
            target = mods.get("target", "center")
            speed = mods.get("speed", 1.0)

            renpy.show(char, at_list=[
                Move(eval(target), speed)
            ])

        elif action == "bounce":
            repeat = mods.get("repeat", 3)
            renpy.show(char, at_list=[
                Bounce(repeat)
            ])

        elif action == "spin":
            speed = mods.get("speed", 1.0)
            renpy.show(char, at_list=[
                RotateMatrix(360 * speed)
            ])

    renpy.register_statement("action",
        parse=action_parse,
        execute=action_execute
    )

# Usage
action mary move to left speed 0.5
action john bounce repeat 5
action mary spin speed 2.0
```

## Complex Statement Examples

### Inventory Management

```python
init python:
    def inventory_parse(lex):
        operation = lex.name()  # add, remove, check
        item = lex.string()

        modifiers = {}
        if operation in ["add", "remove"]:
            if not lex.eol():
                modifiers["amount"] = lex.integer()

        return {
            "operation": operation,
            "item": item,
            "modifiers": modifiers
        }

    def inventory_execute(parsed):
        op = parsed["operation"]
        item = parsed["item"]
        mods = parsed["modifiers"]

        if op == "add":
            amount = mods.get("amount", 1)
            inventory_system.add_item(item, amount)
            renpy.notify(f"Added {amount} {item}")

        elif op == "remove":
            amount = mods.get("amount", 1)
            if inventory_system.remove_item(item, amount):
                renpy.notify(f"Removed {amount} {item}")
            else:
                renpy.notify(f"Not enough {item}")

        elif op == "check":
            count = inventory_system.get_count(item)
            renpy.say(narrator, f"You have {count} {item}")

    renpy.register_statement("inventory",
        parse=inventory_parse,
        execute=inventory_execute
    )

# Usage
inventory add "healing_potion" 3
inventory remove "gold" 50
inventory check "magic_sword"
```

### Dialogue System Extensions

```python
init python:
    def think_parse(lex):
        # think character "thought text" style italic color "#888888"
        character = lex.name()
        thought = lex.string()

        style_props = {}
        while not lex.eol():
            if lex.keyword("style"):
                style_props["style"] = lex.name()
            elif lex.keyword("color"):
                style_props["color"] = lex.string()
            elif lex.keyword("size"):
                style_props["size"] = lex.integer()

        return {
            "character": character,
            "thought": thought,
            "style": style_props
        }

    def think_execute(parsed):
        char_name = parsed["character"]
        thought = parsed["thought"]
        style = parsed["style"]

        # Get character object
        char = eval(char_name)

        # Create thought styling
        thought_style = ""
        if "style" in style:
            if style["style"] == "italic":
                thought = f"{i}{thought}{/i}"

        if "color" in style:
            thought = f"{{color={style['color']}}}{thought}{{/color}}"

        # Add thought indicators
        thought = f"({thought})"

        # Say with character
        char(thought, what_prefix="", what_suffix="")

    renpy.register_statement("think",
        parse=think_parse,
        execute=think_execute
    )

# Usage
think mary "I wonder what he's thinking..." style italic color "#888888"
think john "This is suspicious..." color "#ff0000"
```

## Advanced Parsing Techniques

### Multi-Line Statements

```python
init python:
    def dialogue_block_parse(lex):
        # dialogue_block character:
        #     "Line 1"
        #     "Line 2"
        #     "Line 3"

        character = lex.name()
        lex.require(":")
        lex.expect_eol()

        lines = []
        while lex.advance() and lex.pos:
            if lex.text.strip():
                line = lex.string()
                lines.append(line)

        return {
            "character": character,
            "lines": lines
        }

    def dialogue_block_execute(parsed):
        char_name = parsed["character"]
        lines = parsed["lines"]

        char = eval(char_name)

        for line in lines:
            char(line)

    renpy.register_statement("dialogue_block",
        parse=dialogue_block_parse,
        execute=dialogue_block_execute,
        block=True  # Indicates multi-line statement
    )
```

### Conditional Parsing

```python
init python:
    def if_item_parse(lex):
        # if_item "potion" >= 3:
        #     "You have enough potions!"
        # else:
        #     "You need more potions."

        item = lex.string()
        operator = lex.name()  # >=, <=, ==, !=, >, <
        amount = lex.integer()
        lex.require(":")

        return {
            "item": item,
            "operator": operator,
            "amount": amount
        }

    def if_item_execute(parsed):
        item = parsed["item"]
        op = parsed["operator"]
        amount = parsed["amount"]

        current = inventory_system.get_count(item)

        if op == ">=" and current >= amount:
            return True
        elif op == "<=" and current <= amount:
            return True
        elif op == "==" and current == amount:
            return True
        elif op == "!=" and current != amount:
            return True
        elif op == ">" and current > amount:
            return True
        elif op == "<" and current < amount:
            return True

        return False

    renpy.register_statement("if_item",
        parse=if_item_parse,
        execute=if_item_execute,
        block=["else"],  # Supports else clause
        condition=True   # Acts as conditional
    )
```

## Statement Integration Patterns

### With Screen Integration

```python
init python:
    def show_popup_parse(lex):
        message = lex.string()

        options = {}
        while not lex.eol():
            if lex.keyword("timeout"):
                options["timeout"] = lex.float()
            elif lex.keyword("position"):
                options["position"] = lex.name()

        return {"message": message, "options": options}

    def show_popup_execute(parsed):
        msg = parsed["message"]
        opts = parsed["options"]

        # Show screen with message
        renpy.show_screen("popup_message",
            message=msg,
            timeout=opts.get("timeout", 3.0),
            position=opts.get("position", "center")
        )

    renpy.register_statement("popup",
        parse=show_popup_parse,
        execute=show_popup_execute
    )

# Usage
popup "Game saved!" timeout 2.0 position "top"
popup "Achievement unlocked!"
```

### With Transform Integration

```python
init python:
    def camera_shake_parse(lex):
        intensity = lex.float() if not lex.eol() else 1.0
        duration = lex.float() if not lex.eol() else 1.0

        return {"intensity": intensity, "duration": duration}

    def camera_shake_execute(parsed):
        intensity = parsed["intensity"]
        duration = parsed["duration"]

        # Create shake transform
        shake_transform = Transform(
            pos=(renpy.random.randint(-intensity*10, intensity*10),
                 renpy.random.randint(-intensity*10, intensity*10))
        )

        # Apply to camera
        renpy.show_layer_at([shake_transform], camera=True)

        # Reset after duration
        renpy.timeout(duration)
        renpy.show_layer_at([], camera=True)

    renpy.register_statement("shake",
        parse=camera_shake_parse,
        execute=camera_shake_execute
    )

# Usage
shake 2.0 0.5  # Intensity 2.0, duration 0.5 seconds
shake          # Default values
```

## Best Practices

### Design Principles

- Keep statements simple and focused
- Follow Ren'Py's declarative style
- Provide clear error messages
- Support common use cases efficiently

### Implementation Guidelines

- Always validate input in parse phase
- Use prediction to improve performance
- Implement lint checking for development aid
- Handle edge cases gracefully

### Error Handling

```python
def safe_statement_parse(lex):
    try:
        # Parsing logic
        return parsed_data
    except Exception as e:
        lex.error(f"Parse error: {e}")

def safe_statement_execute(parsed):
    try:
        # Execution logic
        pass
    except Exception as e:
        renpy.error(f"Execution error: {e}")
```

### Performance Considerations

- Minimize work in execute phase
- Use prediction for resource loading
- Cache expensive computations
- Consider rollback implications

Custom statements enable powerful domain-specific extensions while maintaining Ren'Py's approachable syntax. They're particularly valuable for complex systems that benefit from declarative expression.
