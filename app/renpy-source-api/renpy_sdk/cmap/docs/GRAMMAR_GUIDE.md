# CMAP Grammar Guide

## Overview

CMAP uses Lark parser with custom grammars to parse Ren'Py menu structures. This guide explains the grammar design, evolution, and best practices for modifications.

## Grammar Architecture

### Two-Tier Grammar System

CMAP implements a two-tier grammar approach for maximum reliability:

1. **Simple Grammar** (`menu_grammar_simple.lark`) - **Current Production**
2. **Complex Grammar** (`menu_grammar.lark`) - **Future Expansion**

### Design Philosophy

- **Robustness over Features**: Prefer simple, reliable parsing over complex edge cases
- **Graceful Degradation**: When complex parsing fails, fall back to simpler approaches
- **Static Analysis Focus**: Parse for flow analysis, not runtime execution
- **Ren'Py Compatibility**: Support standard Ren'Py syntax patterns

## Current Grammar (Simple)

### Structure Overview

```lark
start: menu_definition

menu_definition: "menu" menu_name? ":" menu_body

menu_body: menu_item+

menu_item: conditional_choice | simple_choice

simple_choice: STRING ":" choice_body?

conditional_choice: STRING "if" conditional_expression ":" choice_body?
```

### Key Design Decisions

#### 1. Simplified Conditionals

```lark
conditional_expression: IDENTIFIER
                      | IDENTIFIER comparison_operator condition_value

comparison_operator: "==" | "!=" | "<" | ">" | "<=" | ">="
condition_value: STRING | NUMBER | IDENTIFIER
```

**Rationale**: Handles 90% of real-world cases while maintaining parsing reliability.

#### 2. Generic Statement Handling

```lark
statement: jump_statement
         | call_statement
         | return_statement
         | pass_statement
         | generic_statement

generic_statement: /[^\n\r]+/
```

**Rationale**: Catches any statement type, preventing parse failures on unknown syntax.

#### 3. No Indentation Handling

**Current**: Uses standard Lark whitespace handling  
**Rationale**: Simplified grammar avoids complex indentation edge cases

### Supported Patterns

#### Basic Menus

```renpy
menu:
    "Choice 1":
        jump label1
    "Choice 2":
        call function1
```

#### Conditional Menus

```renpy
menu:
    "Choice 1" if flag:
        pass
    "Choice 2" if score > 10:
        jump next_scene
```

#### Named Menus

```renpy
menu main_menu:
    "Start Game":
        jump start
    "Load Game":
        call load_screen
```

### Limitations

1. **Complex Conditionals**: `if (flag and not other_flag) or score > 100`
2. **Nested Parentheses**: `if ((a > b) and (c < d))`
3. **Multi-line Statements**: Statements spanning multiple lines
4. **Custom Syntax**: Non-standard Ren'Py extensions

## Future Grammar (Complex)

### Planned Enhancements

#### 1. Advanced Conditionals

```lark
conditional_expression: condition_part (logical_operator condition_part)*

condition_part: IDENTIFIER comparison_operator condition_value
              | "not" IDENTIFIER
              | IDENTIFIER  // Boolean variable
              | "(" conditional_expression ")"

logical_operator: "and" | "or"
```

#### 2. Indentation Handling

```lark
// Using Lark's indentation processor
%import common.NEWLINE
%declare _INDENT _DEDENT

menu_body: _INDENT menu_item+ _DEDENT
choice_body: _INDENT statement+ _DEDENT
```

#### 3. Multi-line Support

```lark
statement: jump_statement
         | call_statement
         | python_block
         | dialogue_block

python_block: "$" python_code
dialogue_block: speaker? dialogue_text
```

## Grammar Evolution Strategy

### Phase 1: Simple Grammar (Current) ✅

- Basic menu parsing
- Simple conditionals (`if flag`, `if score > 10`)
- Standard statements (`jump`, `call`, `return`, `pass`)
- Fallback to regex for complex cases

### Phase 2: Enhanced Conditionals (Planned)

- Complex logical expressions
- Parenthetical grouping
- Compound conditions
- Better error recovery

### Phase 3: Full Ren'Py Support (Future)

- Complete indentation handling
- Multi-line statements
- Custom syntax extensions
- Performance optimizations

## Grammar Modification Guidelines

### 1. Backward Compatibility

**Rule**: New grammar changes must not break existing parsing.

```python
# Before modifying grammar, create compatibility test
def test_grammar_backward_compatibility():
    old_test_cases = load_existing_test_cases()

    for test_case in old_test_cases:
        old_result = test_case.expected_result
        new_result = new_parser.parse_menu(test_case.menu_text)

        assert_equivalent_results(old_result, new_result)
```

### 2. Incremental Changes

**Approach**: Add new rules without removing existing ones.

```lark
# Good: Add new alternative
conditional_expression: simple_condition
                      | complex_condition  # New addition

# Bad: Replace existing rule
conditional_expression: complex_condition  # Breaks existing parsing
```

### 3. Graceful Degradation

**Pattern**: New features should degrade gracefully when they fail.

```lark
# Use optional rules for new features
menu_choice: conditional_choice | simple_choice

conditional_choice: STRING "if" conditional_expression ":" choice_body?
                  | STRING "if" fallback_condition ":" choice_body?  # Fallback

fallback_condition: /[^:\n\r]+/  # Catch-all for complex conditions
```

## Testing Grammar Changes

### 1. Unit Tests for Grammar Rules

```python
def test_new_grammar_rule():
    """Test specific grammar rule in isolation."""
    grammar_fragment = '''
    start: conditional_expression
    conditional_expression: IDENTIFIER comparison_operator condition_value
    // ... rest of grammar
    '''

    parser = Lark(grammar_fragment)

    # Test valid cases
    assert parser.parse("flag == True")
    assert parser.parse("score > 10")

    # Test invalid cases should fail gracefully
    with pytest.raises(LarkError):
        parser.parse("invalid syntax")
```

### 2. Integration Tests

```python
def test_grammar_integration():
    """Test new grammar rules work with complete parser."""
    menu_text = '''menu:
        "Choice" if new_complex_condition:
            pass'''

    result = parser.parse_menu(menu_text)
    assert result is not None
    assert len(result.choices) == 1
```

### 3. Performance Impact Testing

```python
def test_grammar_performance():
    """Ensure grammar changes don't degrade performance."""
    large_menu = create_large_test_menu(100)  # 100 choices

    start_time = time.time()
    result = parser.parse_menu(large_menu)
    elapsed = time.time() - start_time

    assert elapsed < MAX_ACCEPTABLE_PARSE_TIME
```

## Common Grammar Patterns

### 1. Optional Elements

```lark
menu_definition: "menu" menu_name? ":" menu_body
//                      ^^^^^^^^^^ Optional menu name
```

### 2. Alternative Rules

```lark
menu_item: conditional_choice | simple_choice
//         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Try conditional first, then simple
```

### 3. Repetition

```lark
menu_body: menu_item+
//                  ^ One or more menu items
```

### 4. Grouping

```lark
condition_value: STRING | NUMBER | IDENTIFIER
//               ^^^^^^^^^^^^^^^^^^^^^^^^^^^ Any of these types
```

## Error Handling in Grammar

### 1. Permissive Parsing

```lark
# Allow various statement types
statement: jump_statement
         | call_statement
         | generic_statement  # Catch-all

generic_statement: /[^\n\r]+/  # Match any line
```

### 2. Error Recovery

```lark
# Use optional elements to continue parsing after errors
choice_body: statement*  # Zero or more statements (continues if one fails)
```

### 3. Validation in Transformer

```python
def validate_parsed_menu(menu_node):
    """Validate parsed menu after grammar processing."""
    if not menu_node.choices:
        warnings.warn("Menu has no choices")

    for choice in menu_node.choices:
        if not choice.text.strip():
            warnings.warn(f"Empty choice text at line {choice.line_number}")
```

## Grammar Debugging

### 1. Parse Tree Inspection

```python
def debug_parse_tree(menu_text):
    """Inspect parse tree for debugging."""
    tree = parser.parse(menu_text)
    print(tree.pretty())  # Shows parse tree structure
```

### 2. Token Analysis

```python
def analyze_tokens(menu_text):
    """Analyze tokenization for debugging."""
    lexer = parser.lexer
    tokens = list(lexer.lex(menu_text))

    for token in tokens:
        print(f"{token.type}: {token.value} (line {token.line})")
```

### 3. Grammar Validation

```python
def validate_grammar_file():
    """Validate grammar file syntax."""
    try:
        Lark.open("menu_grammar_simple.lark")
        print("Grammar file is valid")
    except LarkError as e:
        print(f"Grammar error: {e}")
```

## Best Practices

### 1. Grammar Design

- **Start Simple**: Begin with minimal rules, expand gradually
- **Test Early**: Test each rule addition immediately
- **Document Changes**: Comment complex rules thoroughly
- **Performance Aware**: Consider parsing performance impact

### 2. Rule Naming

```lark
// Good: Descriptive names
conditional_choice: STRING "if" conditional_expression ":" choice_body?

// Bad: Cryptic names
cc: STRING "if" ce ":" cb?
```

### 3. Rule Organization

```lark
// Group related rules together
// ============================================================================
// MENU STRUCTURE
// ============================================================================

menu_definition: "menu" menu_name? ":" menu_body
menu_body: menu_item+

// ============================================================================
// CHOICE DEFINITIONS
// ============================================================================

menu_item: conditional_choice | simple_choice
```

### 4. Terminal Definitions

```lark
// Define terminals at the end
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
STRING: /"([^"\\]|\\.)*"/
NUMBER: /\d+/
```

## Migration Strategy

When upgrading from simple to complex grammar:

### 1. Feature Flags

```python
class CMAPParser:
    def __init__(self, use_complex_grammar=False):
        if use_complex_grammar:
            self.grammar_file = "menu_grammar.lark"
        else:
            self.grammar_file = "menu_grammar_simple.lark"
```

### 2. A/B Testing

```python
def parse_with_both_grammars(menu_text):
    """Compare results from both grammars."""
    simple_result = simple_parser.parse_menu(menu_text)
    complex_result = complex_parser.parse_menu(menu_text)

    if simple_result and complex_result:
        compare_results(simple_result, complex_result)
```

### 3. Gradual Rollout

1. Deploy complex grammar alongside simple grammar
2. Test with subset of real-world files
3. Compare results and performance
4. Gradually increase usage percentage
5. Full migration when confidence is high

---

**Remember**: Grammar changes should enhance CMAP's capabilities while maintaining the reliability that makes it superior to regex-based parsing.
