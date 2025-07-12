# Ren'Py Labels & Control Flow

> **Fetched from:** https://www.renpy.org/doc/html/label.html  
> **Date:** January 2025  
> **Purpose:** Understanding story structure and branching for The Plot Thickens project

# Labels & Control Flow

## Label Statement

Label statements allow the given name to be assigned to a program point. They exist solely to be called or jumped to, either from Ren'Py script, Python functions, or from screens.

```renpy
label sample1:
    "Here is 'sample1' label."

label sample2(a="default"):
    "Here is 'sample2' label."
    "a = [a]"
```

A label statement may have a block associated with it. In that case, control enters the block whenever the label statement is reached, and proceeds with the statement after the label statement whenever the end of the block is reached: the following code, when jumping to the "origin" label, produces the "a, b, c" sequence.

```renpy
label origin:
    "a"

label hasblock:
    "b"

"c"
return
```

### Global and Local Labels

There are two kinds of labels: **global** and **local** labels. Global labels live in one global namespace shared across all project files and thus should have unique names per game. A local label on the other hand refer to a global label, so several local labels in the game can have the same name, provided they are related to different global labels. To declare a local label, prefix its name with a period `.`, and put it under a global label which it will belong to. For example:

```renpy
label global_label:
    "Under a global label.."

label .local_label:
    "..resides a local one."
    jump .another_local

label .another_local:
    "And another !"
    jump .local_label
```

Local labels can be referenced directly inside the same global label they are declared in, or by their full name, consisting of global and local name parts:

```renpy
label another_global:
    "Now lets jump inside a local label located somewhere else."
    jump global_label.local_name
```

### Label Parameters

The label statement may take an optional list of parameters. These parameters are processed as described in PEP 570, with two exceptions:

First, the values of default parameters are evaluated at call time.

Second, the variables are scoped dynamically, rather than lexically. This means that when a variable gets its value from a label parameter, it will be reverted (to the previous value of the variable if it had one, or to the absence of the variable otherwise) when a return statement is reached.

```renpy
default a = 3

label start:
    menu:
        "Call":
            call label_with_params(5)
        "Jump":
            jump label_without_params
    jump start

label label_with_params(a):

label label_without_params:
    e "a = [a]"  # displays 5 or 3 depending on what path was taken
    return
```

It doesn't generally make sense to have a label with parameters be reached by a jump or a previous statement. For an example of labels with parameters, see the call statement.

## Jump Statement

The **jump statement** is used to transfer control to the given label.

If the expression keyword is present, the expression following it is evaluated, and the string so computed is used as the label name of the statement to jump to. If the expression keyword is not present, the label name of the statement to jump to must be explicitly given.

A local label name can be passed, either with expression or without, and either with the global label prepended ("global_label.local_label"), or starting with a dot (".local_label").

Unlike call, jump does not push the next statement onto a stack. As a result, there's no way to return to where you've jumped from.

```renpy
label loop_start:
    e "Oh no! It looks like we're trapped in an infinite loop."
    jump loop_start
```

## Call Statement

The **call statement** is used to transfer control to the given label. It also pushes the next statement onto the call stack, allowing the return statement to return control to the statement following the call.

If the expression keyword is present, the expression following it is evaluated, and the resulting string is used as the name of the label to call. If the expression keyword is not present, the name of the label to call must be explicitly given.

A local label name can be passed, either with expression or without, and either with the global label prepended ("global_label.local_label"), or starting with a dot (".local_label").

If the optional **from clause** is present, it has the effect of including a label statement with the given name as the statement immediately following the call statement. An explicit label helps to ensure that saved games with return stacks can return to the proper place when loaded on a changed script.

The call statement may take arguments, which are processed as described in PEP 448.

When using a call expression with an arguments list, the **pass keyword** must be inserted between the expression and the arguments list. Otherwise, the arguments list will be parsed as part of the expression, not as part of the call.

```renpy
label start:
    e "First, we will call a subroutine."

    call subroutine
    call subroutine(2)
    call expression "sub" + "routine" pass (count=3)

    return

# ...

label subroutine(count=1):
    e "I came here [count] time(s)."
    e "Next, we will return from the subroutine."
    return
```

> **Warning:** Publishing a game without from clauses for each call statement is dangerous, if you intend to publish updates of the game later on. If no such clauses are added, and if you edit the file containing the call instruction, there is a potential risk for saves made inside the called label to become broken.
>
> Using the "Add from clauses to calls" option when building a game's distribution can solve that issue.

## Return Statement

The **return statement** pops the top statement off of the call stack, and transfers control to it. If the call stack is empty, the return statement restarts Ren'Py, returning control to the main menu.

If the optional expression is given to return, it is evaluated, and it's result is stored in the `_return` variable. This variable is dynamically scoped to each context.

## Special Labels

The following labels are used by Ren'Py:

**start**
: By default, Ren'Py jumps to this label when the game starts.

**quit**
: If it exists, this label is called in a new context when the user quits the game.

**after_load**
: If it exists, this label is called when a game is loaded. It can be use to fix data when the game is updated. If data is changed by this label, renpy.block_rollback() should be called to prevent those changes from being reverted if the player rolls back past the load point.

**splashscreen**
: If it exists, this label is called when the game is first run, before showing the main menu. Please see Adding a Splashscreen.

**before_main_menu**
: If it exists, this label is called before the main menu. It is used in rare cases to set up the main menu, for example by starting a movie playing in the background.

**main_menu**
: If it exists, this label is called instead of the main menu. If it returns, Ren'Py will start the game at the start label. For example, the following will immediately start the game without displaying the main menu.

    ```renpy
    label main_menu:
        return
    ```

**after_warp**
: If it is existed, this label is called after a warp but before the warped-to statement executes. Please see Warping to a line.

**hide_windows**
: If it exists, this label is called when the player hides the windows with the right mouse button or the H key. If this returns true, the hide is cancelled (it's assumed the hide has occurred). Otherwise, the hide continues.

Ren'Py also uses the following labels to show some of the special screens:

- main_menu_screen
- load_screen
- save_screen
- preferences_screen
- joystick_preferences_screen

## Labels & Control Flow Functions

**renpy.call_stack_depth()**
: Returns the depth of the call stack of the current context - the number of calls that have run without being returned from or popped from the call stack.

**renpy.dynamic(\*variables, \*\*kwargs)**
: This can be given one or more variable names as arguments. This makes the variables dynamically scoped to the current call. When the call returns, the variables will be reset to the value they had when this function was called.

    Variables in named stores are supported.

    If the variables are given as keyword arguments, the value of the argument is assigned to the variable name.

    Example calls are:

    ```python
    $ renpy.dynamic("x", "y", "z")
    $ renpy.dynamic("mystore.serial_number")
    $ renpy.dynamic(players=2, score=0)
    ```

**renpy.get_all_labels()**
: Returns the set of all labels defined in the program, including labels defined for internal use in the libraries.

**renpy.get_return_stack()**
: Returns a list giving the current return stack. The return stack is a list of statement names.

    The statement names will be strings (for labels), or opaque tuples (for non-label statements).

**renpy.has_label(name)**
: Returns true if name is a valid label in the program, or false otherwise.

    **name**
    :   Should be a string to check for the existence of a label. It can also be an opaque tuple giving the name of a non-label statement.

**renpy.mark_label_seen(label)**
: Marks the named label as if it has been already executed on the current user's system.

**renpy.mark_label_unseen(label)**
: Marks the named label as if it has not been executed on the current user's system yet.

**renpy.pop_call()**
: Pops the current call from the call stack, without returning to the location. Also reverts the values of dynamic variables, the same way the Ren'Py return statement would.

    This can be used if a label that is called decides not to return to its caller.

**renpy.seen_label(label)**
: Returns true if the named label has executed at least once on the current user's system, and false otherwise. This can be used to unlock scene galleries, for example.

**renpy.set_return_stack(stack)**
: Sets the current return stack. The return stack is a list of statement names.

    Statement names may be strings (for labels) or opaque tuples (for non-label statements).

    The most common use of this is to use:

    ```python
    renpy.set_return_stack([])
    ```

    to clear the return stack.

## Contexts

Contexts are used internally by Ren'Py to manage the changeable and saveable state of the game. Contexts include:

- the currently running Ren'Py statement,
- the call stack, as described above, and the names and former values of dynamic variables created by renpy.dynamic(),
- the images currently being shown (and information about them like their attributes, the transforms applied to them and so on),
- the screens being shown, and the variables inside them,
- the audio that is playing or queued.

Most of the time there is only one context at play, and only one instance of each of these elements exists. This changes when entering the main or game menus; everything above can be changed, and will be restored when leaving the menu context. Some of these changes are automatic, like the screens layer being cleared when entering a context.

Ren'Py also creates new contexts as part of Replay and when hiding the interface.

The creation of screen language has considerably lessened the need for creating contexts.

Rollback is only enabled in the base context (meaning, when there is only one context), and only the base context is saved, which is why the game menu uses a context.

### Context Functions

**renpy.call_in_new_context(label, \*args, \*\*kwargs)**
: This creates a new context, and then starts executing Ren'Py script from the given label in that context. Rollback is disabled in the new context, and saving/loading will occur in the top level context.

    Use this to begin a second interaction with the user while inside an interaction.

    This takes an optional keyword argument:

    **\_clear\_layers**
    :   If True (the default), the layers are cleared before the new interaction starts. If False, the layers are not cleared. If a list, only the layers in the list are cleared.

**renpy.context()**
: Returns an object that is unique to the current context. The object is copied when entering a new context, but changes to the copy do not change the original.

    The object is saved and participates in rollback.

**renpy.context_dynamic(\*variables)**
: This can be given one or more variable names as arguments. This makes the variables dynamically scoped to the current context. When returning to the prior context, the variables will be reset to the value they had when this function was called.

    Variables in named stores are supported.

    Example calls are:

    ```python
    $ renpy.context_dynamic("x", "y", "z")
    $ renpy.context_dynamic("mystore.serial_number")
    ```

**renpy.context_nesting_level()**
: Returns the nesting level of the current context. This is 0 for the outermost context (the context that is saved, loaded, and rolled-back), and is non-zero in other contexts, such as menu and replay contexts.

**renpy.invoke_in_new_context(callable, \*args, \*\*kwargs)**
: This function creates a new context, and invokes the given Python callable (function) in that context. When the function returns or raises an exception, control returns to the original context. It's generally used to call a Python function that needs to display information to the player (like a confirmation prompt) from inside an event handler.

    Additional arguments and keyword arguments are passed to the callable.

    A context created with this function cannot execute Ren'Py script. Functions that would change the flow of Ren'Py script, like renpy.jump(), are handled by the outer context. If you want to call Ren'Py script rather than a Python function, use renpy.call\_in\_new\_context() instead.

    This takes an optional keyword argument:

    **\_clear\_layers**
    :   If True (the default), the layers are cleared before the new interaction starts. If False, the layers are not cleared. If a list, only the layers in the list are cleared.

**renpy.jump_out_of_context(label)**
: Causes control to leave the current context, and then to be transferred in the parent context to the given label.

**renpy.reset_all_contexts()**
: This pops all contexts off the context stack, resetting the dynamic variables as it does so. When this is done, a new context is created, the current statement ends, and the game continues from the next statement. This will put Ren'Py into the state it was at startup, with the exception of data and the start point.

    This can be used to reset everything about the game - shown image, playing music, etc, as if the game started from the beginning.

    Because of how completely this resets Ren'Py, this function immediately ends the current statement.

    This is mainly intended for use in an after\_load label, where it can bring the game back to the state it was in when it started. It's then up to the game to re-establish the scene, music, etc, and it can then jump to the label it wants to continue at.

---

_Built with Sphinx using a theme provided by Read the Docs._
