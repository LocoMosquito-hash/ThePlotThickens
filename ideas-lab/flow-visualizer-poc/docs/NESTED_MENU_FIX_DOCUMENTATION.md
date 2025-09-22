# Nested Menu Fix Documentation

## Issue Description

The Ren'Py flow visualizer had a problem with nested menu structures where choices from nested menus were incorrectly appearing in their parent menus, causing duplicate choices and incorrect flow visualization.

### Example Problem

For this Ren'Py script structure:

```renpy
label day5:
    if readshow == 0:
        menu:                           # Menu 1 (Parent)
            "Game mode.":               # Choice 1
                jump day5start
            "Read mode.":               # Choice 2
                menu:                   # Menu 2 (Nested)
                    "Romantic man.":    # Nested Choice 1
                        jump day5rom
                    "Rude man.":        # Nested Choice 2
                        jump day5rud
```

**Before the fix**, the visualizer showed:

- **Parent Menu**: "Game mode.", "Read mode.", "Romantic man.", "Rude man." (4 choices - WRONG!)
- **Nested Menu**: "Romantic man.", "Rude man." (2 choices)

**After the fix**, the visualizer correctly shows:

- **Parent Menu**: "Game mode.", "Read mode." (2 choices - CORRECT!)
- **Nested Menu**: "Romantic man.", "Rude man." (2 choices)

## Root Cause

The issue was in the `parse_menu_structure` method in `app/renpy-source-api/parser.py`. The parser was:

1. **Over-parsing**: When parsing the parent menu, it would continue parsing all choices it encountered, including those that belonged to nested menus
2. **No Boundary Detection**: The parser didn't recognize when it encountered a nested `menu:` statement and should stop parsing choices for the current menu
3. **Double Processing**: Both the parent and nested menus were being processed separately, but the nested menu choices were included in both

## Solution Implementation

### 1. Enhanced Menu Parsing Logic

**File**: `app/renpy-source-api/parser.py`
**Method**: `parse_menu_structure` (lines 861-869)

```python
elif current_choice and line_indent > indent_level:
    # This line belongs to the current choice

    # Check if this is a nested menu - if so, stop parsing this menu
    if (self.patterns['menu'].match(line) or self.patterns['menu_with_name'].match(line)):
        # We've hit a nested menu, stop parsing choices for this menu
        menu.choices.append(current_choice)
        current_choice = None
        break

    # ... continue with normal parsing
```

**Key Changes:**

- Added detection for nested `menu:` statements within choice blocks
- When a nested menu is encountered, the parser immediately stops parsing the current menu
- This prevents nested menu choices from being incorrectly added to the parent menu

### 2. Nested Menu Detection and Attachment

**File**: `app/renpy-source-api/parser.py`
**Method**: `find_all_menus` (lines 1169-1192)

The system already had logic to:

- Calculate nesting levels based on indentation
- Attach nested menus to their parent choices
- Create proper hierarchical relationships

### 3. Flow Graph Processing

**File**: `app/renpy-source-api/parser.py`
**Method**: `build_flow_graph` (lines 2502-2518)

The flow graph building logic correctly:

- Only processes top-level menus (`nesting_level == 0`)
- Recursively processes nested menu structures
- Creates proper parent-child relationships

## How It Works Now

### 1. Menu Detection Phase

```
find_all_menus() scans the file and finds:
├── Menu 1 (line 6, nesting_level=0)
│   ├── "Game mode." → jump day5start
│   └── "Read mode." → [nested menu attached]
└── Menu 2 (line 10, nesting_level=1)
    ├── "Romantic man." → jump day5rom
    └── "Rude man." → jump day5rud
```

### 2. Menu Parsing Phase

```
parse_menu_structure() for Menu 1:
├── Parses "Game mode." choice
├── Parses "Read mode." choice
├── Encounters nested "menu:" statement
└── STOPS parsing (prevents duplicate choices)

parse_menu_structure() for Menu 2:
├── Parses "Romantic man." choice
└── Parses "Rude man." choice
```

### 3. Hierarchy Building Phase

```
build_flow_graph() creates:
├── day5 Label Node
└── Menu 1 (top-level)
    ├── "Game mode." → day5start
    └── "Read mode." → Menu 2 (nested)
        ├── "Romantic man." → day5rom
        └── "Rude man." → day5rud
```

### 4. Visualization Result

The visualizer now correctly displays:

- **day5 label** connects to **first menu**
- **First menu** contains only "Game mode." and "Read mode."
- **"Game mode."** connects directly to `day5start`
- **"Read mode."** connects to **nested menu container**
- **Nested menu** contains "Romantic man." and "Rude man."
- **"Romantic man."** connects to `day5rom`
- **"Rude man."** connects to `day5rud`

## Technical Details

### Key Files Modified

- `app/renpy-source-api/parser.py`: Enhanced `parse_menu_structure` method

### Key Methods

- `parse_menu_structure()`: Now stops parsing when encountering nested menus
- `_calculate_menu_nesting_level()`: Determines menu hierarchy
- `_find_parent_choice_for_nested_menu()`: Links nested menus to parent choices
- `_process_nested_menu_structures()`: Processes nested menu hierarchy

### Parser Patterns Used

- `self.patterns['menu']`: Matches `menu:` statements
- `self.patterns['menu_with_name']`: Matches `menu label_name:` statements

## Benefits

1. **Accurate Visualization**: Parent menus only show their actual choices
2. **Proper Hierarchy**: Nested menus are correctly represented as child nodes
3. **Clear Flow**: The story flow is now visually correct and easy to follow
4. **Scalable**: Works with any level of menu nesting
5. **Maintainable**: Clean separation between parent and nested menu processing

## Testing

The fix was verified with the "16 years later" VN's `day5` label, which contains the exact nested menu structure described above. The visualization now correctly shows the proper hierarchy without duplicate choices.
