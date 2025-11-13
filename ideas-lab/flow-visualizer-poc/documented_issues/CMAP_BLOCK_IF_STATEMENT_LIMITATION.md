# CMAP Parser: Block-Style If Statement Limitation

## Issue Summary

The CMAP (Custom Menu AST Parser) does not support **block-style if statements with indented bodies** within menu choice bodies. Menus containing these structures will fall back to regex parsing.

**Status**: Known Limitation - Acceptable for Flow Visualization  
**Impact**: Low - Regex fallback correctly extracts control flow  
**Date Identified**: 2024-11-13

---

## Technical Details

### What Works ✅

**Inline if statements** (single statement on same line):
```renpy
menu:
    "Choice 1":
        if True: jump label_one
    "Choice 2":
        if condition: call function_two
```

### What Doesn't Work ❌

**Block-style if statements** (multiple indented statements):
```renpy
menu:
    "Playful. (lp)":
        if True:
            $ lp += 1
            A "This goddess is indeed my girlfriend."
    "Naughty boy. (dp)":
        if True:
            $ dp += 1
            A "Not yet, but the day will come when I will have you both."
```

---

## Root Cause

The CMAP grammar uses Lark's LALR parser without an indentation-aware lexer. Supporting block-style if statements requires:

1. **INDENT/DEDENT tokens** - Python-style indentation tracking
2. **Recursive statement blocks** - `choice_body: statement+` where statements can contain blocks
3. **Complex grammar rules** - Handling nested indentation levels

Current grammar for if statements:
```lark
if_statement: IF conditional_expression ":" statement
```

This expects a single statement after the colon, not an indented block of statements.

---

## Error Example

**File**: `T:\AG\TheShrink\game\prologue.rpy` (line 3965)

**Error Message**:
```
[CMAP] Parse error: Unexpected token Token('STRING', '"Naughty boy. (dp)"') at line 4, column 9.
Expected one of: WITH, PAUSE, PASS, EMPTY_STRING, DOLLAR, IF, CALL, IDENTIFIER, RETURN, SCENE, PYTHON, JUMP
Previous tokens: [Token('COLON', ':')]

[CMAP] Problem menu context:
[CMAP]   1:     menu:
[CMAP]   2:         "Playful. (lp)":
[CMAP]   3:             if True:
[CMAP]   4:         "Naughty boy. (dp)":  # ← Parser sees menu choice where statement expected
```

The parser sees the `if True:` and expects a statement immediately after, but finds a new menu choice instead (because the indented block wasn't recognized as part of the if statement).

---

## Fallback Behavior

When CMAP parsing fails, the system automatically falls back to **regex-based parsing**:

```python
# From parser.py
if result is None:
    print(f"⚠️ Failed to parse menu at line {line_num}, falling back to regex")
    # Regex extraction still works correctly
```

The regex fallback:
- ✅ **Correctly extracts** `jump`, `call`, `return` statements
- ✅ **Correctly identifies** menu choices
- ✅ **Correctly generates** flow graph edges
- ❌ Does NOT provide AST-level detail for choice bodies
- ❌ Does NOT preserve exact line number mappings

---

## Why This is Acceptable

For **Flow Visualization** purposes, the regex fallback is sufficient because:

1. **Control flow is preserved** - All jumps, calls, and returns are detected
2. **Dialogue is irrelevant** - We don't care about dialogue statements for flow analysis
3. **Graph structure is correct** - Menu → Choice → Target relationships are maintained
4. **Variable assignments don't affect flow** - `$ lp += 1` doesn't change narrative paths

The AST parser's primary advantage is:
- Faster parsing
- Better error messages
- More detailed metadata

None of these are critical when the regex fallback functions correctly.

---

## Potential Solutions (Not Implemented)

### Option 1: Add Indentation Support (High Complexity)

Use Lark's `postlex` with an `Indenter` class:

```python
from lark.indenter import Indenter

class RenpyIndenter(Indenter):
    NL_type = '_NEWLINE'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4
```

Update grammar:
```lark
if_statement: IF conditional_expression ":" _NEWLINE _INDENT statement_block _DEDENT

statement_block: statement+
```

**Downside**: Significantly increases grammar complexity, requires rewriting multiple rules.

### Option 2: Ignore If Statements (Not Recommended)

Remove if statement support entirely and rely on regex for all conditional logic.

**Downside**: Breaks inline if statements that currently work correctly.

### Option 3: Hybrid Approach (Potential Future Enhancement)

Detect block-style if statements during preprocessing and flatten them before parsing:

```python
# Transform this:
if True:
    $ lp += 1
    A "dialogue"

# Into this (for parsing only):
if True: $ lp += 1
if True: A "dialogue"
```

**Downside**: Requires additional preprocessing step, may introduce edge cases.

---

## Games Affected

Known games with block-style if statements in menus:
- **The Shrink** (multiple menus in `prologue.rpy`)
- Potentially other games using similar patterns

The regex fallback ensures these games are still fully supported for flow visualization.

---

## Workaround for Developers

If you're developing a Ren'Py game and want optimal CMAP parsing, use **inline if statements** in menu choice bodies:

```renpy
# Instead of:
"My choice":
    if condition:
        $ var += 1
        jump next_label

# Use:
"My choice":
    if condition: $ var += 1
    if condition: jump next_label
```

Note: This is purely for parser optimization. The regex fallback handles both cases correctly.

---

## Related Code

### Grammar File
`app/renpy-source-api/renpy_sdk/cmap/menu_grammar_simple.lark`

```lark
// Current inline-only if statement
if_statement: IF conditional_expression ":" statement
```

### Parser File
`app/renpy-source-api/renpy_sdk/cmap/cmap_parser.py`

```python
def if_statement(self, items):
    """Transform if statement in choice body."""
    # items: [IF, conditional_expression, statement]
    # Only handles single statement, not blocks
```

### Fallback Mechanism
`app/renpy-source-api/parser.py`

```python
def _extract_menu_with_cmap(self, menu_text, line_num, file_path):
    result = self.cmap_parser.parse_menu(menu_text)
    if result is None:
        # Fallback to regex parsing
        return self._extract_menu_regex(menu_text, line_num, file_path)
```

---

## Conclusion

This limitation is **documented and acceptable** for the current use case:
- The regex fallback provides correct flow visualization
- The AST parser handles the majority of menus successfully
- No user-facing functionality is lost
- Future enhancement possible if needed, but not a priority

**Recommendation**: Leave as-is unless AST-level detail becomes critical for features beyond flow visualization.

