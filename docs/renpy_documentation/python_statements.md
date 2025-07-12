# Ren'Py Python Statements

> **Fetched from:** https://www.renpy.org/doc/html/python.html  
> **Date:** January 2025  
> **Purpose:** Understanding Python integration with Ren'Py scripts for The Plot Thickens project

# Python Statements

Ren'Py is written in the Python programming language, and includes support for including Python inside Ren'Py scripts. Python support can be used for many things, from setting a flag to creating new displayables. This chapter covers ways in which Ren'Py scripts can directly invoke Python, through the various Python statements.

Ren'Py 7 supports Python 2.7. Ren'Py 8 supports Python 3.9.

## Python

The python statement takes a block of Python, and runs the block when control reaches the statement. A basic Python statement can be very simple:

```renpy
python:
    flag = True
```

Python statements can get more complex, when necessary:

```renpy
python:
    player_health = max(player_health - damage, 0)
    if enemy_vampire:
        enemy_health = min(enemy_health + damage, enemy_max_health)
```

There are two modifiers to the Python statement that change its behavior:

**hide**
: If given the hide modifier, the Python statement will run the block of Python in an anonymous scope. The scope will be lost when the Python block terminates.

**in**
: The in modifier takes a name. Instead of executing in the default store, the Python will execute in the store with that name.

## One-line Python Statement

A common case is to have a single line of Python that runs in the default store. For example, a Python one-liner can be used to initialize or update a flag. To make writing Python one-liners more convenient, there is the one-line Python statement.

The one-line Python statement begins with the dollar-sign `$` character, and contains everything else on that line. Here are some example of Python one-liners:

```renpy
# Set a flag.
$ flag = True

# Initialize a variable.
$ romance_points = 0

# Increment a variable.
$ romance_points += 1

# Call a function that exposes Ren'Py functionality.
$ renpy.movie_cutscene("opening.ogv")
```

Python one-liners always run in the default store.

## Init Python Statement

The init python statement runs Python at initialization time, before the game loads. Among other things, this can be used to define classes and functions, or to initialize styles, config variables, or persistent data.

```renpy
init python:
    def auto_voice_function(ident):
        return "voice/" + ident + ".ogg"

    config.auto_voice = auto_voice_function

    if persistent.endings is None:
        persistent.endings = set()

init 1 python:
    # The bad ending is always unlocked.
    persistent.endings.add("bad_ending")
```

A priority number can be placed between init and python. When a priority is not given, 0 is used. Init statements are run in priority order, from lowest to highest. Init statements of the same priority are run in Unicode order by filepath, and then from top to bottom within a file.

Variables that have their value set in an init python block are not saved, loaded, and do not participate in rollback. Therefore, these variables should not be changed after init is over.

## Define Statement

The define statement sets a single variable to a value at init time. The variable is treated as constant, and should not be changed after being set. For example:

```renpy
define e = Character("Eileen")
```

is equivalent to:

```renpy
init python:
    e = Character("Eileen")
```

The define statement can take an optional named store by prepending it to the variable name with a dot:

```renpy
define character.e = Character("Eileen")
```

The define statement can take an optional index, making it possible to add entries to a dictionary:

```renpy
define config.tag_layer["eileen"] = "master"
```

In addition to `=`, define can take two more operators. The `+=` operator adds, and is generally used for list concatenation. The `|=` operator is generally used to concatenate sets:

```renpy
define config.keymap["dismiss"] += [ "K_KP_PLUS" ]
define endings |= { "best_ending" }
```

## Default Statement

The default statement sets a single variable to a value if that variable is not defined when the game starts, or after a new game is loaded. For example:

```renpy
default points = 0
```

When the variable points is not defined at game start, this statement is equivalent to:

```renpy
label start:
    $ points = 0
```

The default statement can take an optional named store:

```renpy
default schedule.day = 0
```

**Important Note**: It is highly recommended to default every variable in your game that is susceptible to change. This prevents variable "leaking" between game sessions.

## Names in the Store

The default place that Ren'Py stores Python variables is called the store. It's important to make sure that the names you use in the store do not conflict.

The define statement assigns a value to a variable, even when it's used to define a character. This means that it's not possible to use the same name for a character and a flag.

## Other Named Stores

Named stores provide a way of organizing Python functions and variables into modules. By placing Python in named stores, you can minimize the chance of name conflicts. Each store corresponds to a Python module.

```renpy
init python in mystore:
    serial_number = 0

    def serial():
        global serial_number
        serial_number += 1
        return serial_number

default character_stats.chloe_substore.friends = {"Eileen",}

label start:
    $ serial = mystore.serial()

    if "Lucy" in character_stats.chloe_substore.friends:
        chloe "Lucy is my friend !"
    elif character_stats.chloe_substore.friends:
        chloe "I have friends, but Lucy is not one of them."

    python in character_stats.chloe_substore:
        friends.add("Jeremy")
```

## Constant Stores

A named store can be declared to be constant by setting a variable named `_constant` to a true value:

```renpy
init python in mystore:
    _constant = True
```

When a store is constant, variables in that store are not saved, and objects reachable solely from those variables do not participate in rollback.

## JSONDB

JSONDB is a two-level database that uses JSON to store its data. It's intended to be used by game developers to store data in a database that can be version-controlled as part of the game script.

```renpy
define balloonData = JSONDB("balloon.json", default={ "enabled" : False })
```

## First and Third-Party Python Modules

Ren'Py can import pure-Python modules and packages. First-party modules can be placed directly into the game directory. Third party packages can be placed into the `game/python-packages` directory.

For example, to install the python-dateutil package:

```bash
pip install --target game/python-packages python-dateutil
```

Then import from an init python block:

```renpy
init python:
    import dateutil.parser
```

---

**Key Points for The Plot Thickens:**

1. **Variable Management**: $ statements for quick variable manipulation
2. **Initialization**: init python for setup code and configuration
3. **Character Definitions**: define statements for creating reusable character objects
4. **State Management**: default statements for game variables
5. **Modular Organization**: Named stores for organizing code
6. **External Libraries**: Support for third-party Python packages
7. **Data Persistence**: JSONDB for game data storage

This is crucial for understanding how Ren'Py scripts integrate Python logic with narrative flow.
