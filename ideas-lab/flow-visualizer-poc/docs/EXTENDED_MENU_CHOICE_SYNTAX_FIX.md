# Extended Menu Choice Syntax Fix

## Issue Description

Some Ren'Py games use non-standard menu choice syntax with additional parameters after the choice text, which caused the flow visualizer to fail parsing these choices entirely.

### Example Problem

**Standard Ren'Py Syntax (works):**

```renpy
menu:
    "Choice Text":
        # choice content
```

**Extended Syntax (was failing):**

```renpy
menu:
    "Sign Contract" (pre="[smgr]", post=""):
        # choice content
    "Uncle Buck" (pre="[smgr]", post=""):
        # choice content
```

### Impact

- **Game Affected**: "23 Sisters" (T:\AG\23Sisters-0.12b-pc\game\script.rpy)
- **Symptoms**: 13 menu choices with parameter syntax were not being parsed
- **Result**: Missing choice nodes and connections in flow visualization

## Root Cause

The menu choice regex pattern was too restrictive:

**Original Pattern:**

```python
'menu_choice': re.compile(r'^\s*"([^"]+)"\s*:')
```

This pattern expected:

- `"Choice Text"` followed immediately by `:`
- When it encountered `"Choice Text" (parameters):`, it failed to match because of the unexpected parentheses

## Solution

### File Modified

`app/renpy-source-api/parser.py` - Line 333

### Change Applied

**Before:**

```python
'menu_choice': re.compile(r'^\s*"([^"]+)"\s*:'),
```

**After:**

```python
'menu_choice': re.compile(r'^\s*"([^"]+)"\s*(?:\([^)]*\))?\s*:'),
```

### Pattern Breakdown

| Component        | Purpose                                              |
| ---------------- | ---------------------------------------------------- |
| `^\s*`           | Start of line + optional whitespace                  |
| `"([^"]+)"`      | **Capture group 1**: Main choice text inside quotes  |
| `\s*`            | Optional whitespace after closing quote              |
| `(?:\([^)]*\))?` | **NEW**: Optional non-capturing group for parameters |
| `\s*:`           | Optional whitespace + required colon                 |

### Parameter Group Details

- `(?:...)` - Non-capturing group (doesn't interfere with choice text capture)
- `\([^)]*\)` - Matches parentheses with any content inside
- `?` - Makes the entire parameter group optional

## Verification

### Test Cases Handled

✅ **Standard Format**: `"Choice Text":` → Captures "Choice Text"  
✅ **Extended Format**: `"Sign Contract" (pre="[smgr]", post=""):` → Captures "Sign Contract"  
✅ **With Whitespace**: `"Uncle Buck"   (pre="[smgr]", post="")   :` → Captures "Uncle Buck"

### Backwards Compatibility

- ✅ All existing games continue to work unchanged
- ✅ No impact on standard Ren'Py menu syntax
- ✅ Only adds support for the extended parameter syntax

## Benefits

1. **Surgical Fix**: Minimal code change with maximum impact
2. **Robust Parsing**: Handles both standard and extended choice syntax
3. **Clean Extraction**: Still captures only the main choice text, ignoring parameters
4. **Future-Proof**: Can handle various parameter formats within parentheses

## Testing

**Game**: "23 Sisters" (23Sisters-0.12b-pc)
**File**: T:\AG\23Sisters-0.12b-pc\game\script.rpy
**Results**: All 13 previously failing menu choices now parse correctly

### Example Successful Parses

- Line 644: `"Sign Contract" (pre="[smgr]", post=""):` → "Sign Contract"
- Line 1457: `"Uncle Buck" (pre="[smgr]", post=""):` → "Uncle Buck"
- Line 1535: `"Mothman" (pre="[smgr]", post=""):` → "Mothman"
- Line 1661: `"Heroin Addicts" (pre="[smgr]", post=""):` → "Heroin Addicts"

## Prevention of Regression

### Code Review Checklist

- [ ] Verify `menu_choice` regex pattern includes optional parameter group
- [ ] Test with both standard and extended choice syntax
- [ ] Ensure captured group (1) contains only the choice text, not parameters

### Test Cases to Maintain

```python
# Standard format
assert re.match(pattern, '"Standard Choice":')
# Extended format
assert re.match(pattern, '"Extended Choice" (param="value"):')
# With whitespace
assert re.match(pattern, '"Spaced Choice"   (param="value")   :')
```

### Warning Signs of Regression

- Menu choices with parentheses not appearing in visualization
- Reduced choice count in games using extended syntax
- Parser warnings about unrecognized choice patterns

## Technical Notes

- **Pattern Type**: Non-capturing optional group
- **Performance Impact**: Negligible (single regex change)
- **Memory Impact**: None (same capture group structure)
- **Compatibility**: Full backwards compatibility maintained

This fix ensures the flow visualizer can handle diverse Ren'Py coding styles while maintaining robust parsing for all standard menu formats.
