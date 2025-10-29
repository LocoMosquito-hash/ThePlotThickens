# CMAP API Reference

## Overview

This document provides a complete API reference for CMAP (Custom Menu AST Parser) components, including classes, methods, and data structures.

## Core Classes

### CMAPParser

Main parser class for processing Ren'Py menu structures.

```python
class CMAPParser:
    """Custom Menu AST Parser using Lark."""
```

#### Constructor

```python
def __init__(self):
    """Initialize the CMAP parser."""
```

**Description**: Initializes the parser with the simple grammar and sets up the transformer.

**Raises**:

- `CMAPError`: If grammar loading fails

#### Methods

##### parse_menu

```python
def parse_menu(self, menu_text: str) -> Optional[MenuNode]:
    """
    Parse a menu structure from text.

    Args:
        menu_text: The menu text to parse

    Returns:
        MenuNode if successful, None if parsing fails
    """
```

**Example**:

```python
parser = CMAPParser()
menu_text = '''menu:
    "Choice 1":
        jump label1
    "Choice 2" if flag:
        pass'''

result = parser.parse_menu(menu_text)
print(f"Parsed {len(result.choices)} choices")
```

##### parse_menu_from_lines

```python
def parse_menu_from_lines(self, lines: List[str], start_line: int) -> Optional[MenuNode]:
    """
    Parse a menu from lines starting at a specific line.

    Args:
        lines: List of all lines in the file
        start_line: Line number where menu starts (1-indexed)

    Returns:
        MenuNode if successful, None if parsing fails
    """
```

##### extract_menu_from_lines

```python
def extract_menu_from_lines(self, lines: List[str], start_line: int) -> tuple[str, int]:
    """
    Extract menu text from lines starting at a specific line.

    Args:
        lines: List of all lines in the file
        start_line: Line number where menu starts (1-indexed)

    Returns:
        Tuple of (menu_text, end_line)
    """
```

## AST Node Classes

### MenuNode

Represents a complete menu definition.

```python
@dataclass
class MenuNode(CMAPNode):
    """Represents a complete menu definition."""
    name: Optional[str] = None
    params: List[str] = field(default_factory=list)
    choices: List[MenuChoiceNode] = field(default_factory=list)
    conditional_items: List[ConditionalMenuItemNode] = field(default_factory=list)
    set_variable: Optional[str] = None
```

**Attributes**:

- `name`: Optional menu name (for named menus)
- `params`: List of menu parameters
- `choices`: List of menu choices
- `conditional_items`: List of conditional menu items (if/elif/else)
- `set_variable`: Variable set by menu (if using `set` statement)
- `line_number`: Line number where menu is defined
- `column`: Column number where menu is defined

**Methods**:

```python
def validate(self) -> List[str]:
    """Validate the menu node and return list of error messages."""

def to_dict(self) -> Dict[str, Any]:
    """Convert node to dictionary representation."""
```

### MenuChoiceNode

Represents a single menu choice.

```python
@dataclass
class MenuChoiceNode(CMAPNode):
    """Represents a single menu choice."""
    text: str = ""
    condition: Optional[ConditionalExpressionNode] = None
    body: List[ChoiceStatementNode] = field(default_factory=list)
    is_conditional: bool = False
```

**Attributes**:

- `text`: Choice text displayed to user
- `condition`: Optional conditional expression
- `body`: List of statements executed when choice is selected
- `is_conditional`: Whether this choice has a condition
- `line_number`: Line number where choice is defined
- `column`: Column number where choice is defined

**Example**:

```python
# Simple choice
choice1 = MenuChoiceNode(
    text="Go to park",
    is_conditional=False,
    body=[JumpStatementNode(target="park_scene")]
)

# Conditional choice
choice2 = MenuChoiceNode(
    text="Use magic",
    is_conditional=True,
    condition=ConditionalExpressionNode(variable="has_magic"),
    body=[CallStatementNode(target="cast_spell")]
)
```

### ConditionalExpressionNode

Represents a conditional expression in menu choices.

```python
@dataclass
class ConditionalExpressionNode(CMAPNode):
    """Represents a conditional expression (variable == value, etc.)."""
    variable: str = ""
    operator: Optional[str] = None  # None for boolean variables
    value: Optional[Any] = None
    logical_operator: Optional[str] = None  # 'and', 'or'
    next_condition: Optional['ConditionalExpressionNode'] = None
    is_negated: bool = False  # For 'not variable'
```

**Attributes**:

- `variable`: Variable name or full condition text
- `operator`: Comparison operator (==, !=, <, >, <=, >=)
- `value`: Value to compare against
- `logical_operator`: Logical operator for chaining conditions
- `next_condition`: Next condition in chain (for compound conditions)
- `is_negated`: Whether condition is negated with 'not'

**Examples**:

```python
# Simple boolean condition: if flag
condition1 = ConditionalExpressionNode(variable="flag")

# Comparison condition: if score > 10
condition2 = ConditionalExpressionNode(
    variable="score",
    operator=">",
    value=10
)

# Negated condition: if not flag
condition3 = ConditionalExpressionNode(
    variable="flag",
    is_negated=True
)
```

## Statement Node Classes

### JumpStatementNode

Represents a jump statement.

```python
@dataclass
class JumpStatementNode(ChoiceStatementNode):
    """Represents a jump statement."""
    target: str = ""
```

**Attributes**:

- `target`: Label to jump to

### CallStatementNode

Represents a call statement.

```python
@dataclass
class CallStatementNode(ChoiceStatementNode):
    """Represents a call statement."""
    target: str = ""
    params: List[str] = field(default_factory=list)
```

**Attributes**:

- `target`: Label to call
- `params`: List of parameters passed to call

### ReturnStatementNode

Represents a return statement.

```python
@dataclass
class ReturnStatementNode(ChoiceStatementNode):
    """Represents a return statement."""
    value: Optional[Any] = None
```

**Attributes**:

- `value`: Optional return value

### PassStatementNode

Represents a pass statement.

```python
@dataclass
class PassStatementNode(ChoiceStatementNode):
    """Represents a pass statement."""
```

### PythonStatementNode

Represents a Python code statement.

```python
@dataclass
class PythonStatementNode(ChoiceStatementNode):
    """Represents a Python code statement."""
    code: str = ""
```

**Attributes**:

- `code`: Python code to execute

### DialogueStatementNode

Represents a dialogue statement.

```python
@dataclass
class DialogueStatementNode(ChoiceStatementNode):
    """Represents a dialogue statement."""
    speaker: Optional[str] = None
    text: str = ""
```

**Attributes**:

- `speaker`: Optional speaker name
- `text`: Dialogue text

### VariableAssignmentNode

Represents a variable assignment.

```python
@dataclass
class VariableAssignmentNode(ChoiceStatementNode):
    """Represents a variable assignment."""
    variable: str = ""
    operator: str = "="  # =, +=, -=, etc.
    value: Any = None
```

**Attributes**:

- `variable`: Variable name
- `operator`: Assignment operator
- `value`: Value to assign

## Transformer Classes

### CMAPTransformer

Transforms Lark parse tree into CMAP AST nodes.

```python
class CMAPTransformer(Transformer):
    """Transforms Lark parse tree into CMAP AST nodes."""
```

**Key Methods**:

```python
def start(self, items):
    """Transform start rule."""

def menu_definition(self, items):
    """Transform menu definition."""

def menu_choice(self, items):
    """Transform menu choice (delegates to simple_choice or conditional_choice)."""

def simple_choice(self, items):
    """Transform simple choice."""

def conditional_choice(self, items):
    """Transform conditional choice."""

def conditional_expression(self, items):
    """Transform conditional expression."""
```

## Utility Functions

### Validation Functions

```python
def validate_menu_structure(menu: MenuNode) -> List[str]:
    """
    Validate a menu structure and return list of warnings/errors.

    Args:
        menu: MenuNode to validate

    Returns:
        List of validation messages
    """
```

### Conversion Functions

```python
def convert_cmap_to_enhanced(cmap_menu: MenuNode, file_path: str) -> EnhancedMenuStructure:
    """
    Convert CMAP MenuNode to EnhancedMenuStructure for compatibility.

    Args:
        cmap_menu: CMAP MenuNode
        file_path: Source file path

    Returns:
        EnhancedMenuStructure compatible with existing systems
    """
```

## Error Classes

### CMAPError

Base exception for CMAP errors.

```python
class CMAPError(Exception):
    """Base exception for CMAP errors."""
```

### CMAPParseError

Error during menu parsing.

```python
class CMAPParseError(CMAPError):
    """Error during menu parsing."""
```

### CMAPTransformError

Error during AST transformation.

```python
class CMAPTransformError(CMAPError):
    """Error during AST transformation."""
```

## Constants and Enums

### Grammar Files

```python
SIMPLE_GRAMMAR_FILE = "menu_grammar_simple.lark"
COMPLEX_GRAMMAR_FILE = "menu_grammar.lark"
```

### Statement Types

```python
STATEMENT_TYPES = [
    "jump",
    "call",
    "return",
    "pass",
    "python",
    "dialogue",
    "assignment"
]
```

### Condition Complexity Levels

```python
CONDITION_COMPLEXITY = [
    "simple",      # Single variable or comparison
    "conditional", # Basic conditional with operator
    "complex",     # Multiple conditions with logical operators
    "dynamic"      # Complex expressions with parentheses
]
```

## Usage Patterns

### Basic Parsing

```python
from renpy_sdk.cmap import CMAPParser

# Initialize parser
parser = CMAPParser()

# Parse menu text
menu_text = '''menu:
    "Choice 1":
        jump scene1
    "Choice 2" if flag:
        call function1'''

result = parser.parse_menu(menu_text)

if result:
    print(f"Menu has {len(result.choices)} choices")
    for choice in result.choices:
        print(f"- {choice.text} ({'conditional' if choice.is_conditional else 'simple'})")
```

### File Processing

```python
def process_renpy_file(file_path: str):
    """Process a Ren'Py file and extract all menus."""
    parser = CMAPParser()

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    menus = []
    for i, line in enumerate(lines):
        if line.strip().startswith('menu'):
            menu = parser.parse_menu_from_lines(lines, i + 1)
            if menu:
                menus.append(menu)

    return menus
```

### Error Handling

```python
def safe_parse_menu(parser: CMAPParser, menu_text: str) -> Optional[MenuNode]:
    """Safely parse menu with comprehensive error handling."""
    try:
        result = parser.parse_menu(menu_text)

        if result:
            # Validate result
            errors = result.validate()
            if errors:
                print(f"Validation warnings: {errors}")

            return result
        else:
            print("Parsing returned None")
            return None

    except CMAPParseError as e:
        print(f"Parse error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### Integration with Existing Systems

```python
def integrate_with_ast_parser():
    """Example of integrating CMAP with existing AST parser."""
    from renpy_sdk.ast_menu_parser import ASTMenuParser

    # AST parser automatically uses CMAP when available
    ast_parser = ASTMenuParser()

    # Parse file - will use CMAP if available, fall back to regex otherwise
    menus = ast_parser.parse_file_menus("script.rpy")

    print(f"Parsed {len(menus)} menus")
    for menu in menus:
        print(f"Menu at line {menu.line_number}: {len(menu.choices)} choices")
```

---

**Note**: This API is designed for stability and backward compatibility. New features are added through optional parameters and new methods rather than breaking changes to existing interfaces.
