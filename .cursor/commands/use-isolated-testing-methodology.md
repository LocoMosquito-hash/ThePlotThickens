# Use Isolated Testing Methodology

When debugging or testing Flow Visualizer components, **always refer to** `@ISOLATED_TESTING_METHODOLOGY.md` for systematic troubleshooting.

## When to Apply This Methodology

✅ **Use isolated testing when:**
- A component works in isolation but fails in integration
- Reproducing a bug reported in a specific game
- Testing new parsing logic or grammar changes
- Debugging CSAP (screen parsing) issues
- Debugging CMAP (menu parsing) issues
- Debugging AHS (Authoritative Hierarchy System) issues
- Investigating label detection or flow connection problems
- Testing data transformation pipelines
- Performance profiling specific components

## The Systematic Approach

Follow this **layered isolation** strategy from the methodology:

```
1. Full Pipeline Test → Does it work end-to-end?
2. Component Test → Does the component work alone?
3. Extract Real Data → What data is actually flowing?
4. Compare → What's different between working and broken?
5. Fix → Make the minimal change
6. Verify → Rerun all tests
```

## Key Principles from the Methodology

### 1. **Create Standalone Test Scripts**

Create temporary scripts like:
- `test_*.py` - Full pipeline tests
- `diagnose_*.py` - Component-specific diagnostics
- `verify_*.py` - Verification after fixes
- `extract_*.py` - Data extraction utilities

### 2. **Progressive Narrowing**

Start broad, end narrow:
- Does the full pipeline work?
- Which component is failing?
- What input causes the failure?
- What line of code is the problem?

### 3. **Capture Intermediate Data**

Save data to files for comparison:
```python
# Save extracted content
with open(f"debug_extracted_{name}.txt", 'w', encoding='utf-8') as f:
    f.write(content)
```

### 4. **Test in Isolation First**

Before modifying integration code, verify the component works alone:
```python
# Test CMAP alone with manual input
menu_text = """menu:
    "Choice 1":
        jump label1
"""
result = parser.parse_menu(menu_text)
```

## Component-Specific Sections in the Methodology

The `ISOLATED_TESTING_METHODOLOGY.md` document includes detailed testing procedures for:

- **CSAP (Screen Parsing)** - Lines 69-279
  - Testing screen elements and hotspots
  - Extracting real screen content
  - Comparing manual vs. extracted content

- **CMAP (Menu Parsing)** - Lines 282-496
  - Testing menu choices and destinations
  - Extracting menus from .rpy files
  - Testing conditional choices

- **Label Parsing** - Lines 499-657
  - Label detection tests
  - Flow connection verification
  - Orphan label identification

- **Performance Profiling** - Lines 661-713
  - Timing each parsing stage
  - Identifying bottlenecks

## Templates Available

The methodology includes ready-to-use templates:
- Generic component test template (lines 786-886)
- Menu extraction script (lines 432-487)
- Screen content extraction (lines 220-278)
- Flow connection testing (lines 586-657)

## Remember to Clean Up

After debugging, remove temporary test files:
```python
# Remove test scripts when done
test_*.py
diagnose_*.py
verify_*.py
extract_*.py
debug_*.txt
extracted_*.txt
```

## Quick Reference

**Before starting any component debugging:**
1. Read the relevant section in `@ISOLATED_TESTING_METHODOLOGY.md`
2. Create a standalone test script
3. Test the component in isolation first
4. Extract real data if isolated test passes
5. Compare extracted vs. manual input
6. Fix the minimal code needed
7. Verify with both isolated and pipeline tests
8. Clean up temporary files

---

**See Also:**
- `@ISOLATED_TESTING_METHODOLOGY.md` - Full methodology documentation
- `@preventencodingissuesintesting` - Encoding fixes for test scripts

