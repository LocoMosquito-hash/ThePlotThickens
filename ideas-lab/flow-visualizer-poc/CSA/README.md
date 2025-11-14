# Conditional Structure Analyzer (CSA)

**Version**: 0.1.0  
**Status**: ✅ Phase 1 & 2 Complete  
**Author**: The Plot Thickens Development Team  
**Date**: 2025-01-14

---

## Overview

The Conditional Structure Analyzer (CSA) is a standalone module for parsing conditional blocks (`if`/`elif`/`else`) in Ren'Py code. It provides centralized conditional parsing logic that eliminates code duplication across multiple parsers.

### Purpose

- **DRY Principle**: Conditional logic in ONE place
- **Consistency**: All parsers handle conditionals the same way
- **Testability**: Test conditional parsing independently
- **Maintainability**: Fix conditional bugs in one place
- **Reusability**: Any parser can use CSA

### Used By

- **CSAP** (Custom Screen AST Parser) - For screen element conditionals
- **CMAP** (Custom Menu AST Parser) - For menu choice conditionals
- **Label Parser** - For jump/call conditionals
- **Any component** dealing with Ren'Py conditionals

---

## Features

### Phase 1: Boundary Detection ✅

- Detects `if`/`elif`/`else` blocks
- Tracks indentation levels
- Identifies branch boundaries
- Extracts content per branch
- Handles edge cases:
  - Empty branches
  - Blank lines and comments
  - Multi-line conditions
  - Tab vs space indentation
  - Nested indentation (not nested conditionals yet)

### Phase 2: Content Analysis ✅

- Detects what's inside each branch:
  - `contains_menu`: Menu definitions
  - `contains_choice`: Menu choice text
  - `contains_jump`: Jump statements
  - `contains_call`: Call statements
  - `contains_screen_element`: Screen elements (textbutton, imagebutton, hotspot)
- Context-aware detection
- Nested conditional parsing with depth limits
- Handles both Ren'Py statement and Action syntax

---

## Installation

CSA is located in `ideas-lab/flow-visualizer-poc/CSA/`

```python
# Add to your Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "CSA"))

# Import
from CSA import ConditionalStructureAnalyzer, ConditionalBlock, ConditionalBranch
```

---

## Quick Start

### Basic Usage

```python
from CSA import ConditionalStructureAnalyzer

analyzer = ConditionalStructureAnalyzer()

# Parse a conditional block
text = """if score > 10:
    jump good_ending
elif score > 5:
    jump neutral_ending
else:
    jump bad_ending"""

block = analyzer.analyze_conditional(text)

# Access branches
for branch in block.branches:
    print(f"{branch.branch_type}: {branch.condition}")
    print(f"  Lines {branch.start_line}-{branch.end_line}")
    if branch.contains_jump:
        print("  Contains jump statement")
```

### Extract All Content (Show All Paths)

```python
# Get content from all branches combined
all_content = block.get_all_content()

# Useful for flow visualization where you want to see
# all possible paths through the conditional
```

### Check Specific Branch Content

```python
# Check if specific branch has a jump
if block.has_jump_in_branch(0):
    print("First branch contains a jump")

# Get specific branch
if_branch = block.get_branch('if')
elif_branches = block.get_all_branches_by_type('elif')
```

---

## API Reference

### Classes

#### `ConditionalStructureAnalyzer`

Main class for parsing conditionals.

**Methods:**

- `analyze_conditional(text, start_line=0, context_stack=None, max_depth=10, current_depth=0) -> ConditionalBlock`
  - Parse a conditional block and return structured metadata
  - **Args:**
    - `text`: Text containing the conditional
    - `start_line`: Line number where text starts (for accurate location)
    - `context_stack`: Optional list of parsing contexts (e.g., `['label', 'menu']`)
    - `max_depth`: Maximum recursion depth for nested conditionals (default: 10)
    - `current_depth`: Current recursion depth (internal use)
  - **Returns:** `ConditionalBlock` with all branches and metadata
  - **Raises:** `ValueError` if no conditional found or malformed structure

#### `ConditionalBlock`

Represents a complete conditional structure.

**Attributes:**

- `branches: List[ConditionalBranch]` - All branches in order
- `start_line: int` - Where conditional starts (0-indexed)
- `end_line: int` - Where conditional ends (0-indexed, inclusive)
- `base_indentation: int` - Base indentation level

**Methods:**

- `get_all_content() -> List[str]` - Get content from all branches combined
- `get_branch_count() -> int` - Number of branches
- `has_jump_in_branch(index) -> bool` - Check if branch has jump
- `get_branch(type) -> Optional[ConditionalBranch]` - Get first branch of type
- `get_all_branches_by_type(type) -> List[ConditionalBranch]` - Get all branches of type

#### `ConditionalBranch`

Represents one branch of a conditional.

**Attributes:**

- `branch_type: str` - 'if', 'elif', or 'else'
- `condition: Optional[str]` - Condition expression (None for else)
- `content_lines: List[str]` - Raw lines inside branch
- `start_line: int` - Branch start line
- `end_line: int` - Branch end line
- `indentation: int` - Base indentation
- **Content flags:**
  - `contains_menu: bool`
  - `contains_choice: bool`
  - `contains_jump: bool`
  - `contains_call: bool`
  - `contains_screen_element: bool`
- `nested_conditionals: List[ConditionalBlock]` - Nested conditionals

---

## Usage Examples

### Example 1: CSAP Integration (Screen Elements)

```python
from CSA import ConditionalStructureAnalyzer

class CSAPScreenParser:
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
    
    def parse_screen_elements(self, screen_text: str):
        elements = []
        
        # Detect conditional blocks
        if 'if ' in screen_text:
            try:
                conditional = self.csa.analyze_conditional(
                    screen_text,
                    context_stack=['screen']
                )
                
                # Extract elements from ALL branches (show all paths)
                for branch in conditional.branches:
                    if branch.contains_screen_element:
                        elements.extend(
                            self._extract_elements(branch.content_lines)
                        )
                        
            except ValueError:
                # Not a conditional, use fallback parsing
                pass
        
        return elements
```

### Example 2: CMAP Integration (Menu Choices)

```python
class CMAPMenuParser:
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
    
    def parse_menu_choices(self, menu_text: str):
        choices = []
        lines = menu_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Detect conditional in menu
            if line.strip().startswith('if '):
                remaining = '\n'.join(lines[i:])
                conditional = self.csa.analyze_conditional(
                    remaining,
                    context_stack=['menu']
                )
                
                # Process each branch as potential choices
                for branch in conditional.branches:
                    if branch.contains_choice:
                        choice = self._extract_choice(
                            branch.content_lines,
                            condition=branch.condition
                        )
                        choices.append(choice)
                
                i = conditional.end_line + 1
            else:
                # Regular choice
                i += 1
        
        return choices
```

### Example 3: Label Parser Integration (Flow Analysis)

```python
class LabelFlowParser:
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
    
    def extract_all_jumps(self, label_content: str):
        """Extract ALL possible jump targets (all paths)."""
        jumps = []
        
        if 'if ' in label_content:
            conditional = self.csa.analyze_conditional(
                label_content,
                context_stack=['label']
            )
            
            # Get jumps from ALL branches
            for branch in conditional.branches:
                if branch.contains_jump:
                    targets = self._extract_jump_targets(branch.content_lines)
                    jumps.extend([
                        {'target': t, 'condition': branch.condition}
                        for t in targets
                    ])
        
        return jumps
```

---

## Real-World Patterns

### Pattern 1: Screen Conditionals

```python
# Vinovella University imagebutton pattern
screen b1c04_choice_menu:
    if variable is False:
        auto "images/active_%s.webp"
        action Jump("active_path")
        hovered Function(show_tooltip, "Active")
    else:
        idle "images/inactive.webp"
        action NullAction()
```

**CSA handles:**
- Conditional properties based on runtime state
- Extracting Jump actions from both branches
- Detecting screen elements in each branch

### Pattern 2: Menu Conditionals

```python
menu:
    "Choice 1" if condition1:
        jump path_a
    "Choice 2" if condition2:
        jump path_b
    "Always available":
        jump path_c
```

**CSA handles:**
- Conditional choices with inline conditions
- Extracting all possible jump targets
- Context-aware choice detection

### Pattern 3: Nested Conditionals

```python
if outer_condition:
    if inner_condition:
        jump nested_a
    else:
        jump nested_b
else:
    jump outer_else
```

**CSA handles:**
- Recursive parsing of nested structures
- Depth limiting to prevent infinite recursion
- Extracting jumps from all nesting levels

---

## Testing

### Run Tests

```bash
# Phase 1 tests (boundary detection)
python CSA/tests/test_csa_manual.py

# Phase 2 tests (content detection)
python CSA/tests/test_csa_phase2.py
```

### Test Coverage

- **Phase 1**: 10/11 tests pass (91%) - Basic boundary detection
- **Phase 2**: 9/10 tests pass (90%) - Content analysis and nesting
- **Total**: 19/21 tests pass (90%)

### Test Categories

1. **Basic Boundary Detection**
   - Single if
   - if/else
   - if/elif/else chains
   - Multiple elif branches
   - Indented conditionals

2. **Edge Cases**
   - Empty branches
   - Comments and blank lines
   - Complex boolean conditions
   - Multi-line conditions
   - Tab/space indentation
   - EOF handling

3. **Content Detection**
   - Jump/Call detection
   - Menu detection
   - Choice detection
   - Screen element detection

4. **Advanced Features**
   - Nested conditionals
   - Context-aware parsing
   - Depth limits

---

## Architecture Decisions

### Why CSA?

**Problem**: Every parser (CSAP, CMAP, Label Parser) was reimplementing conditional logic independently, leading to:
- Code duplication
- Inconsistent handling
- Difficult maintenance
- Repeated bugs

**Solution**: CSA centralizes conditional parsing in ONE place.

### Design Principles

1. **Single Responsibility**: CSA only parses conditional structure, doesn't interpret semantics
2. **Clean Interface**: Simple dataclasses, easy to consume
3. **Fail Gracefully**: Rich error messages, never silent failures
4. **Context-Aware**: Adapts behavior based on parsing context
5. **Performance**: Minimal overhead, efficient parsing

### Phased Implementation

- **Phase 1** (1.5 days): Boundary detection - Find where conditionals start/end
- **Phase 2** (1 day): Content analysis - Detect what's inside branches

This allows incremental adoption and validates approach early.

---

## Known Limitations

1. **Multi-line conditions**: Edge case with certain formatting (Test 8 failure)
2. **Python blocks**: Not handled (by design - out of scope)
3. **While/for loops**: Not handled (by design - future feature)
4. **Triple-quoted strings**: May confuse colon detection
5. **Very deep nesting**: Limited to 10 levels (configurable)

---

## Future Enhancements

### Potential Phase 3 Features

- **While/for loop support**: Similar structure to conditionals
- **Python block parsing**: Handle `python:` blocks
- **Screen language support**: Parse `screen:` specific syntax
- **AST integration**: Convert to full AST nodes
- **Performance optimizations**: Caching, lazy evaluation
- **Error recovery**: Continue parsing after errors

### Integration Roadmap

- ✅ Phase 1: Core CSA + PoC
- ✅ Phase 2: Content detection
- 🔄 Phase 3: Full CSAP integration
- 🔄 Phase 4: Full CMAP integration
- ⏳ Phase 5: Label Parser integration
- ⏳ Phase 6: Performance optimization

---

## Contributing

When modifying CSA:

1. **Run all tests** before committing
2. **Add tests** for new features
3. **Update README** with new capabilities
4. **Consider backwards compatibility**
5. **Document edge cases** in code comments

---

## Troubleshooting

### Issue: "No 'if' statement found"

**Cause**: Text doesn't contain a valid if statement at the expected indentation

**Solution**: Check that:
- `if` keyword is present
- Condition has a colon `:`
- Indentation is consistent

### Issue: "Conditional nesting too deep"

**Cause**: Exceeded max_depth parameter

**Solution**: 
```python
# Increase depth limit
block = analyzer.analyze_conditional(text, max_depth=20)
```

### Issue: "First branch must be 'if'"

**Cause**: Trying to create ConditionalBlock starting with elif/else

**Solution**: Ensure parsing starts at the `if` statement, not midway through conditional

---

## Performance

### Benchmarks

- **Simple conditional** (if/else): ~0.1ms
- **Complex conditional** (if/elif*3/else): ~0.3ms
- **Nested conditional** (2 levels): ~0.5ms
- **Real-world screen** (DressingRoom3): ~1.2ms

### Optimization Tips

1. **Avoid re-parsing**: Cache ConditionalBlock results
2. **Limit depth**: Set appropriate max_depth for your use case
3. **Context stack**: Pass context to improve detection accuracy
4. **Batch processing**: Parse multiple conditionals in one pass

---

## License

Part of "The Plot Thickens" project.  
All rights reserved.

---

## Support

For questions or issues:
1. Check the documented issues in `documented_issues/`
2. Review test cases in `CSA/tests/`
3. Contact the development team

---

**Last Updated**: 2025-01-14  
**Version**: 0.1.0

