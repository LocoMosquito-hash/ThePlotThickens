# Ren'Py GraphViz Analysis

An in-depth analysis of EwenQuim's renpy-graphviz tool - a Go-based narrative flow visualizer for Ren'Py visual novels.

## Project Overview

**Repository**: [EwenQuim/renpy-graphviz](https://github.com/EwenQuim/renpy-graphviz)  
**Language**: Go  
**Purpose**: Generate flowchart visualizations of Ren'Py story branches and narrative flow  
**Output**: GraphViz DOT files and PNG images showing story structure  
**License**: AGPLv3 (requires attribution in games)

### Core Concept

The tool parses Ren'Py `.rpy` files using regex patterns to extract labels, jumps, calls, menus, and screens, then generates a directed graph showing the narrative flow and decision points.

## Technical Architecture

### Parsing Strategy

The tool uses a **regex-based line-by-line parser** with context tracking:

```go
// Core regex patterns for parsing
screen:            regexp.MustCompile(`^\\s*(?:init\\s+[-\\w]*\\s+)?screen\\s+([\\p{Han}a-zA-Z0-9._-]+).*\\s*:\\s*(?:#.*)?$`)
label:             regexp.MustCompile(`^\\s*label\\s+([\\p{Han}a-zA-Z0-9._-]+)(?:\\([\\p{Han}a-zA-Z0-9,_= \\-\"']*\\))?\\s*:\\s*(?:#.*)?$`)
jump:              regexp.MustCompile(`^\\s*jump\\s+([\\p{Han}a-zA-Z0-9_.]+)\\s*(?:#.*)?$`)
call:              regexp.MustCompile(`^\\s*call\\s+(([\\p{Han}a-zA-Z0-9_-]+)(?:\\([\\p{Han}a-zA-Z0-9,_= \\-\"']*\\))?)\\s*(?:#.*)?$`)
menu:              regexp.MustCompile(`^\\s*menu.*:\\s*(?:#.*)?$`)
choice:            regexp.MustCompile(`^\\s*(?:\"(.*?[^\\\\])\"|'(.*?[^\\\\])').*:\\s*(?:#.*)?$`)
```

### Context Management

Maintains parsing state through a `Context` struct:

```go
type Context struct {
    currentSituation   situation // jump, call, label, screen, etc.
    indent             int       // indentation level tracking
    currentLabel       string    // current label being processed
    labelStack         []labelStack // stack of nested labels
    currentScreen      string    // current screen context
    menuIndent         int       // menu nesting level
    lastChoice         string    // last menu choice text
    tags               Tag       // special directive tags
}
```

### Graph Generation

- Uses the `emicklei/dot` library for GraphViz generation
- Tracks nodes (labels/screens) and edges (jumps/calls/choices)
- Applies visual styling based on tags and node types
- Outputs DOT format converted to PNG via GraphViz

## Parsing Capabilities

### What It Successfully Handles

1. **Basic Narrative Flow**

   - Label definitions and jumps between labels
   - Call statements with return flow
   - Implicit jumps (sequential execution)

2. **Menu Systems**

   - Menu definitions and choice extraction
   - Choice text as edge labels
   - Branching paths from menu choices

3. **Screen Integration**

   - Screen definitions and usage
   - Screen-to-label jumps (`action Jump()`)
   - Screen-to-screen navigation (`action Show()`)
   - Nested screen usage (`use` keyword)

4. **Advanced Features**
   - Indentation-based scope tracking
   - Return statement flow breaking
   - Multiple file processing with auto-discovery

### Tag System for Manual Control

When regex parsing fails, the tool provides a comprehensive tag system:

```renpy
# renpy-graphviz: TITLE
label chapter_1:
    "Chapter begins"

# renpy-graphviz: BREAK
label disconnected_scene:
    "This won't show implicit connection"

# renpy-graphviz: IGNORE
label debug_label:
    "This label won't appear in graph"

# renpy-graphviz: SKIPLINK
jump distant_label  # Creates shortcut instead of long arrow

# renpy-graphviz: FAKE_LABEL(custom_node)
# renpy-graphviz: FAKE_JUMP(from_node, to_node)
# Virtual nodes/connections not in actual script

# renpy-graphviz: INGAME_LABEL(4, virtual_label)
# renpy-graphviz: INGAME_JUMP(8, destination)
# Simulates script elements at specific indentation levels
```

## Strengths

### 1. **Practical Focus**

- Solves a real problem: visualizing complex VN story structures
- Provides immediate visual feedback for narrative flow
- Useful for debugging story logic and dead ends

### 2. **Robust File Handling**

- Recursively processes entire Ren'Py projects
- Handles UTF-8 BOM and encoding issues
- Configurable file filtering with regex patterns

### 3. **Visual Customization**

- Different node shapes/colors for different element types
- Configurable display options (show/hide screens, atoms, edge labels)
- Custom styling through tags

### 4. **Extensive Tag System**

- Comprehensive manual override capabilities
- Handles edge cases where automatic parsing fails
- Style and layout control options

### 5. **Production Ready**

- CLI tool with configuration files
- Error handling and user-friendly diagnostics
- Multiple output formats (DOT, PNG)

## Critical Limitations

### 1. **Fundamentally Regex-Limited Parsing**

The core weakness: **regex patterns cannot understand Ren'Py's context-sensitive syntax**.

```renpy
# This confuses the parser:
if complex_condition:
    if nested_condition:
        menu:
            "Complex choice":
                $ complex_python_code()
                call dynamic_label_name
```

**Problems:**

- Cannot parse complex Python expressions in conditionals
- Fails on dynamic label names (variables, expressions)
- Misses nested menu structures in complex indentation
- Cannot understand Python blocks that affect flow

### 2. **Limited Python Integration Understanding**

```renpy
# Parser misses these flow patterns:
$ label_name = "chapter_" + str(current_chapter)
$ renpy.call(label_name)

python:
    if player.karma > 50:
        renpy.jump("good_path")
    else:
        renpy.jump("bad_path")
```

**Missing:**

- Variable-based label references
- Dynamic flow control through Python
- Computed jumps and calls
- State-dependent branching logic

### 3. **Screen System Oversimplification**

```renpy
# Only catches basic patterns:
screen simple_menu:
    textbutton "Continue" action Jump("next_scene")  # ✓ Detected

# Misses complex screen logic:
screen inventory:
    for item in inventory_items:
        textbutton "[item.name]" action [
            SetVariable("selected_item", item),
            Call("use_item_sequence")
        ]  # ✗ Not detected
```

### 4. **No Semantic Understanding**

The parser treats Ren'Py as a flat text format rather than understanding:

- Variable scope and lifetime
- Character definitions and dialogue attribution
- Asset references and dependencies
- Game state and progression logic

### 5. **Maintenance and Brittleness**

The regex approach requires constant updates for:

- New Ren'Py syntax features
- Edge cases in existing syntax
- Complex formatting variations
- Multi-language character sets

## Real-World Failure Cases

Based on the author's own admission of limitations and common VN patterns:

### 1. **Modern VN Complexity**

```renpy
# Complex choice systems with computed options
menu:
    "What to do?" if player.energy > 0:

    "Fight [enemy.name]" if "sword" in inventory:
        call combat_system(enemy, "sword")

    "Cast [available_spells[0]]" if magic_available():
        $ spell_result = cast_spell(available_spells[0])
        if spell_result.success:
            jump victory_sequence
        else:
            jump spell_failure
```

### 2. **Dynamic Story Generation**

```renpy
# Common in modern VNs
python:
    story_branches = generate_available_paths(player_state)
    for branch in story_branches:
        create_dynamic_scene(branch.name, branch.content)

# Parser cannot follow programmatically generated content
```

### 3. **Advanced Screen Interactions**

```renpy
screen character_creator:
    for stat in ["strength", "magic", "charm"]:
        bar value StatVariable(stat) range 100:
            released Play("sound", "click.wav")
            released If(sum_stats() <= max_points,
                       true=Call("continue_creation"),
                       false=Call("stat_error"))
```

## What The Plot Thickens Can Learn

### 1. **Avoid Pure Regex Parsing**

**Lesson**: Regex-based parsing hits fundamental limits with Ren'Py's complexity.

**TPT Approach**: Use proper AST parsing with Ren'Py's own lexer/parser principles:

- Understand indentation and scope properly
- Parse Python expressions within Ren'Py context
- Handle dynamic content through static analysis

### 2. **Focus on Semantic Understanding**

**renpy-graphviz** maps syntax → visualization  
**TPT** should map semantic meaning → analysis

```python
# TPT should understand this semantically:
define mary = Character("Mary", color="#ff6b9d")  # Character definition
label mary_introduction:                           # Story sequence
    mary "Hello there!"                           # Character dialogue
    menu:                                         # Decision point
        "Be friendly":                            # Choice option
            $ mary.affection += 1                 # State change
            jump mary_friendship_path             # Narrative branch
```

### 3. **Embrace Multi-Pass Analysis**

**renpy-graphviz**: Single-pass line-by-line parsing  
**TPT**: Multi-pass analysis for completeness

1. **Structure Pass**: Labels, screens, characters, assets
2. **Flow Pass**: Jumps, calls, returns, menu choices
3. **State Pass**: Variable usage, character interactions
4. **Dependency Pass**: Asset references, nested calls

### 4. **Handle Dynamic Content Intelligently**

```python
# Static analysis strategies for dynamic content:

# Pattern 1: Detect variable-based jumps
$ destination = "chapter_" + str(chapter_num)
jump destination  # → Track as "dynamic jump to chapter_*"

# Pattern 2: Analyze Python blocks for flow control
python:
    if condition:
        renpy.jump("path_a")  # → Extract conditional branches

# Pattern 3: Understand loops and iteration
for character in party_members:
    call character_dialogue(character.name)  # → Detect repeated patterns
```

### 5. **Comprehensive Error Recovery**

**renpy-graphviz weakness**: Fails hard on unexpected syntax  
**TPT strength**: Graceful degradation and partial analysis

- Continue analysis when specific patterns fail
- Provide confidence levels for extracted information
- Offer suggestions for manual annotation where needed

### 6. **Integrate with Ren'Py Ecosystem**

**Learn from limitations**:

- Use Ren'Py's own parsing libraries where possible
- Understand Ren'Py's execution model, not just syntax
- Support modern Ren'Py features (layered images, screens language evolution)

## Technical Debt Analysis

### Architecture Issues

1. **Monolithic Parser**: Single massive function handling all syntax types
2. **Global State**: Context management through global structures
3. **Regex Brittleness**: Hard-coded patterns difficult to extend
4. **Limited Error Context**: Poor error reporting for malformed files

### Scalability Problems

1. **Memory Usage**: Loads entire project into memory at once
2. **Performance**: Regex evaluation on every line is expensive
3. **File Size Limits**: No handling of very large script files
4. **Project Size**: No optimization for large multi-file projects

## Integration Opportunities for TPT

### 1. **Complement, Don't Replace**

Use renpy-graphviz for:

- Quick visual overviews of story structure
- Verification of TPT's more complex analysis
- User-facing simple flowcharts

Use TPT for:

- Deep semantic analysis
- Character relationship tracking
- Asset dependency management
- Complex story state analysis

### 2. **Data Exchange**

TPT could:

- Export simplified structure data to renpy-graphviz format
- Import graphviz annotations back into TPT analysis
- Use graphviz for quick visualization of TPT's detailed analysis

### 3. **Hybrid Approach**

- **TPT**: Comprehensive semantic analysis with proper parsing
- **renpy-graphviz**: Quick visualization and user-friendly diagrams
- **Integration**: TPT exports simplified data for graphviz rendering

## Recommendations for TPT Development

### 1. **Parser Architecture**

```python
# Recommended TPT parser structure:
class RenpySemanticParser:
    def __init__(self):
        self.lexer = RenpyLexer()           # Proper tokenization
        self.syntax_parser = RenpySyntaxParser()  # AST generation
        self.semantic_analyzer = SemanticAnalyzer()  # Meaning extraction
        self.flow_analyzer = FlowAnalyzer()  # Control flow understanding

    def parse_project(self, project_path):
        # Multi-pass analysis with proper error recovery
        ast = self.syntax_parser.parse_files(project_path)
        semantic_model = self.semantic_analyzer.analyze(ast)
        flow_model = self.flow_analyzer.analyze(semantic_model)
        return CompleteAnalysis(ast, semantic_model, flow_model)
```

### 2. **Avoid renpy-graphviz Pitfalls**

**Don't:**

- Rely solely on regex for parsing Ren'Py syntax
- Ignore Python blocks and dynamic content
- Parse files in isolation without project context
- Fail completely on unexpected syntax

**Do:**

- Use proper lexical analysis and AST parsing
- Understand Ren'Py's execution model and scoping
- Maintain project-wide context and dependencies
- Provide graceful degradation and partial results

### 3. **Focus Areas for TPT**

1. **Advanced Flow Analysis**: Handle complex conditional branching, loops, Python integration
2. **Character Relationship Tracking**: Understand character interactions across the story
3. **Asset Management**: Track images, audio, and other media dependencies
4. **State Analysis**: Understand game state, variables, and progression systems
5. **Narrative Analysis**: Scene progression, dialogue patterns, choice consequences

## Conclusion

**renpy-graphviz** is a useful tool for basic story flow visualization but hits fundamental limits due to its regex-based parsing approach. It provides valuable insights into:

- **What works**: Basic label/jump flow tracking, menu visualization, screen integration
- **What fails**: Complex Python integration, dynamic content, modern VN patterns
- **What's needed**: Semantic understanding, proper parsing, project-wide analysis

**For The Plot Thickens**: Use renpy-graphviz as inspiration for visual presentation while building far more sophisticated semantic analysis capabilities. The goal should be comprehensive understanding of VN projects, not just syntax-level parsing.

The lesson is clear: **surface-level regex parsing isn't sufficient for modern Ren'Py projects**. TPT should aim higher - true semantic understanding of visual novel structure, content, and meaning.

## Implementation Recommendations

### Phase 1: Foundation

- Build proper Ren'Py lexer/parser based on Ren'Py's own syntax rules
- Implement multi-pass analysis architecture
- Establish project-wide context management

### Phase 2: Semantic Analysis

- Character definition and dialogue tracking
- Asset reference and dependency mapping
- Variable and state analysis across scripts

### Phase 3: Advanced Features

- Dynamic content pattern recognition
- Complex flow control understanding
- Integration with renpy-graphviz for visualization

The renpy-graphviz project shows both the possibilities and limitations of Ren'Py analysis tools. TPT should learn from both to build something far more capable.
