# Conditional Structure Analyzer (CSA) - Architectural Proposal

**Date:** 2025-01-14  
**Status:** 💭 Proposal/Design Phase  
**Complexity:** 🟡 Medium (2-3 days implementation)  
**Value:** 🟢 High (solves recurring pain point)

## Problem Statement

Conditionals (`if`/`elif`/`else`) appear throughout Ren'Py code and every parser struggles with them independently:

- **CSAP**: 19 conditional-related grammar rules for screen conditionals
- **CMAP**: 32 conditional patterns for menu choice conditionals  
- **Label Parsing**: Ad-hoc regex for conditional jumps
- **Code Duplication**: Each parser reimplements conditional structure detection
- **Inconsistent Handling**: Different parsers handle edge cases differently

### Example Pain Point

```python
menu:
    "Choice 1"
        if cond1 == 5:
            jump x
        elif cond1 == 8:
            jump y
        else:
            jump z
    "Choice 2"
```

**Current approach**: CMAP grammar must handle:
- Detecting conditional start
- Tracking indentation levels
- Finding conditional end
- Extracting content from each branch
- All while parsing menu structure

**Problem**: If CSAP encounters similar conditionals, it reimplements the same logic.

## Proposed Solution

### Conditional Structure Analyzer (CSA)

A **standalone module** that specializes in parsing conditional blocks and returning structured metadata.

```python
class ConditionalStructureAnalyzer:
    """
    Analyzes conditional blocks (if/elif/else) and returns structural metadata.
    
    Purpose: Central authority for conditional structure parsing
    Used by: CSAP, CMAP, Label Parser, any component dealing with conditionals
    """
    
    def analyze_conditional(
        self, 
        text: str, 
        start_line: int = 0
    ) -> ConditionalBlock:
        """
        Parse a conditional block and return its structure.
        
        Args:
            text: Text containing conditional (may include surrounding code)
            start_line: Line number where text starts (for accurate location)
            
        Returns:
            ConditionalBlock with:
            - branches: List of (condition, content_lines, line_range)
            - end_line: Where conditional ends
            - indentation_level: Base indentation
            - content_summary: What types of elements found
        """
        pass
```

### Interface Design

```python
@dataclass
class ConditionalBranch:
    """Represents one branch of a conditional (if/elif/else)."""
    branch_type: str  # 'if', 'elif', 'else'
    condition: Optional[str]  # None for 'else'
    content_lines: List[str]  # Raw lines inside this branch
    start_line: int
    end_line: int
    indentation: int
    
    # Content analysis
    contains_menu: bool = False
    contains_choice: bool = False
    contains_jump: bool = False
    contains_call: bool = False
    contains_screen_element: bool = False

@dataclass
class ConditionalBlock:
    """Complete conditional structure with all branches."""
    branches: List[ConditionalBranch]
    start_line: int
    end_line: int  # Where conditional ends
    base_indentation: int
    
    def get_all_content(self) -> List[str]:
        """Get all content from all branches (for 'show all paths' mode)."""
        pass
    
    def get_branch_count(self) -> int:
        """How many branches (if/elif/else)."""
        return len(self.branches)
    
    def has_jump_in_branch(self, branch_index: int) -> bool:
        """Does this branch contain a jump statement?"""
        return self.branches[branch_index].contains_jump
```

### Usage Examples

#### Example 1: CMAP Using CSA

```python
class CMAPParser:
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
    
    def parse_menu_body(self, lines: List[str]) -> MenuNode:
        i = 0
        choices = []
        
        while i < len(lines):
            line = lines[i]
            
            # Detect conditional
            if line.strip().startswith('if '):
                # Let CSA handle it!
                conditional = self.csa.analyze_conditional(
                    '\n'.join(lines[i:]),
                    start_line=i
                )
                
                # Process each branch as potential choices
                for branch in conditional.branches:
                    if branch.contains_choice:
                        # Extract choice from this branch
                        choice = self._extract_choice_from_lines(
                            branch.content_lines,
                            condition=branch.condition
                        )
                        choices.append(choice)
                
                # Skip past the conditional
                i = conditional.end_line + 1
            else:
                # Regular choice processing
                choices.append(self._parse_choice(line))
                i += 1
        
        return MenuNode(choices=choices)
```

#### Example 2: CSAP Using CSA

```python
class CSAPTransformer:
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
    
    def imagebutton_body(self, items):
        elements = []
        i = 0
        
        while i < len(items):
            item = items[i]
            
            if self._is_conditional(item):
                # Let CSA analyze it
                conditional = self.csa.analyze_conditional_tree(item)
                
                # Extract elements from ALL branches (show all paths)
                for branch in conditional.branches:
                    if branch.contains_screen_element:
                        elements.extend(
                            self._extract_elements(branch.content_lines)
                        )
                
                i += 1
            else:
                elements.append(self._process_item(item))
                i += 1
        
        return elements
```

#### Example 3: Label Parser Using CSA

```python
class LabelParser:
    def __init__(self):
        self.csa = ConditionalStructureAnalyzer()
    
    def extract_jumps(self, label_content: str) -> List[JumpInfo]:
        jumps = []
        lines = label_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if line.strip().startswith('if '):
                # Use CSA
                conditional = self.csa.analyze_conditional(
                    '\n'.join(lines[i:]),
                    start_line=i
                )
                
                # Extract jumps from ALL branches
                for branch in conditional.branches:
                    if branch.contains_jump:
                        jump_targets = self._extract_jump_targets(
                            branch.content_lines
                        )
                        jumps.extend([
                            JumpInfo(target=t, condition=branch.condition)
                            for t in jump_targets
                        ])
                
                i = conditional.end_line + 1
            else:
                # Regular jump
                if 'jump ' in line:
                    jumps.append(self._extract_jump(line))
                i += 1
        
        return jumps
```

## Implementation Approach

### Phase 1: Core CSA (1 day)

1. **ConditionalStructureAnalyzer class**
   - Detect if/elif/else keywords
   - Track indentation levels
   - Identify branch boundaries
   - Extract content per branch

2. **Data structures**
   - `ConditionalBranch`
   - `ConditionalBlock`
   - Clean interface for consumers

3. **Basic tests**
   - Single `if`
   - `if/else`
   - `if/elif/else` chains
   - Multi-line indented content

### Phase 2: Content Detection (1 day)

Add analysis of what's inside each branch:

```python
def _analyze_branch_content(self, lines: List[str]) -> Dict[str, bool]:
    """Detect what types of elements are in this branch."""
    return {
        'contains_menu': any('menu' in line for line in lines),
        'contains_choice': any(re.match(r'\s*".*":', line) for line in lines),
        'contains_jump': any('jump ' in line for line in lines),
        'contains_call': any('call ' in line for line in lines),
        'contains_screen_element': any(
            re.match(r'\s*(textbutton|imagebutton|hotspot)', line) 
            for line in lines
        ),
    }
```

### Phase 3: Integration (0.5-1 day)

1. **Integrate into CMAP**
   - Replace conditional handling logic
   - Test with existing test suite
   - Verify no regressions

2. **Integrate into CSAP**
   - Simplify conditional transformers
   - Test with problematic screens
   - Verify Vinovella-style patterns work

3. **Documentation**
   - Usage guide
   - API reference
   - Migration guide for existing code

## Technical Challenges

### Challenge 1: Indentation Detection

**Problem**: Python/Ren'Py indentation is significant

**Solution**:
```python
def _detect_indentation(self, lines: List[str]) -> int:
    """Detect base indentation level."""
    for line in lines:
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            return len(line) - len(stripped)
    return 0

def _get_block_end(self, lines: List[str], start_idx: int, base_indent: int) -> int:
    """Find where indented block ends."""
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if not line.strip():  # Skip blank lines
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= base_indent:
            return i - 1
    return len(lines) - 1
```

### Challenge 2: Nested Conditionals

**Problem**: Conditionals can be nested

```python
if x:
    if y:
        jump a
    else:
        jump b
else:
    jump c
```

**Solution**: Recursive analysis
```python
def analyze_conditional(self, text: str, depth: int = 0) -> ConditionalBlock:
    """Recursively analyze conditionals."""
    if depth > 10:  # Prevent infinite recursion
        raise ValueError("Conditional nesting too deep")
    
    # Parse outer conditional
    block = self._parse_conditional_structure(text)
    
    # Check each branch for nested conditionals
    for branch in block.branches:
        if self._has_nested_conditional(branch.content_lines):
            nested = self.analyze_conditional(
                '\n'.join(branch.content_lines),
                depth=depth + 1
            )
            branch.nested_conditionals = [nested]
    
    return block
```

### Challenge 3: Ambiguous Syntax

**Problem**: Is this one conditional or two?

```python
if x:
    jump a
if y:
    jump b
```

**Solution**: Strict indentation rules
- If second `if` is at same or lower indent → separate conditional
- If second `if` is more indented → nested conditional

## Pros and Cons

### ✅ Pros

1. **DRY Principle**: Conditional logic in ONE place
2. **Consistency**: All parsers handle conditionals the same way
3. **Testability**: Test conditional parsing independently
4. **Maintainability**: Fix conditional bugs in one place
5. **Extensibility**: Easy to add conditional features (switch/case if Ren'Py adds it)
6. **Separation of Concerns**: Parser focuses on structure, not conditional logic
7. **Reusability**: Any future parser can use CSA

### ⚠️ Cons

1. **Abstraction Layer**: Adds one more layer to understand
2. **Migration Effort**: Need to update existing parsers
3. **Testing Burden**: Must test CSA + integration in each parser
4. **Potential Overhead**: Small performance cost of extra layer
5. **Learning Curve**: Team must understand CSA interface

## Is It Worth It?

### My Assessment: **YES** 🟢

**Reasoning:**

1. **Pain Point is Real**: You've struggled with conditionals in CSAP, CMAP, and mentioned labels
2. **Code Smell**: Current duplication violates DRY
3. **Moderate Effort**: 2-3 days implementation
4. **High Value**: Solves recurring problem permanently
5. **Clean Architecture**: Proper separation of concerns
6. **Future-Proof**: Any new parser benefits

### ROI Calculation

**Cost**: 2-3 days initial + 0.5 days per parser integration = ~3.5 days

**Benefit**:
- Eliminates ~4 hours of debugging per conditional edge case
- Reduces future parser development time by ~20%
- Makes codebase more maintainable
- Enables consistent "show all paths" behavior

**Break-even**: After ~3-4 conditional-related bugs or new parser implementations

### Recommendation

**Implement in stages:**

1. **Stage 1 (2 days)**: Build core CSA with basic tests
2. **Stage 2 (1 day)**: Integrate into CMAP (most complex use case)
3. **Stage 3 (0.5 day)**: Integrate into CSAP
4. **Stage 4 (as needed)**: Integrate into Label Parser

**Start with CMAP** because:
- Menu conditionals are the most problematic
- It's a well-defined use case
- Success here validates the entire approach

## Alternative Approaches

### Alternative 1: Keep Status Quo
- **Pros**: No work
- **Cons**: Duplication, inconsistency, ongoing pain

### Alternative 2: Conditional-Blind Everywhere
- **Pros**: Simple, fast
- **Cons**: Loses structural information, can't handle complex cases

### Alternative 3: Regex Pre-processor
- **Pros**: Quick to implement
- **Cons**: Fragile, hard to maintain, doesn't handle nesting

### Alternative 4: Full Grammar Integration
- **Pros**: Most powerful
- **Cons**: Complex, tightly coupled, hard to change

**Verdict**: CSA (your proposal) is the sweet spot between power and simplicity.

## Next Steps if Approved

1. Create `conditional_analyzer.py` module
2. Define `ConditionalBranch` and `ConditionalBlock` dataclasses
3. Implement core `analyze_conditional()` method
4. Write comprehensive tests (20+ test cases)
5. Document API and usage patterns
6. Integrate into CMAP as proof of concept
7. Measure before/after complexity metrics

## Questions for Discussion

1. **Scope**: Should CSA handle `while` loops? `python` blocks?
2. **Interface**: Do you want CSA to return AST nodes or simple dataclasses?
3. **Integration**: Should CSA be part of each parser or a shared utility?
4. **Content Analysis**: How deep should CSA analyze branch content?
5. **Error Handling**: How should CSA handle malformed conditionals?

---

## Verdict

**Feasibility**: 🟢 **High** - Well-defined problem, clear solution  
**Difficulty**: 🟡 **Medium** - 2-3 days for experienced developer  
**Value**: 🟢 **High** - Solves recurring pain point across all parsers  
**Recommendation**: **IMPLEMENT** - This is good software architecture

This is not just fixing a bug - it's improving the fundamental design of your parsing system. The conditional handling problem will only get worse as you add more parsers or encounter more complex Ren'Py patterns. CSA solves it permanently.

