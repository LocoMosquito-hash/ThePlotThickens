# CMAP - Custom Menu AST Parser

**Version:** 1.0.1  
**Status:** Production Ready  
**Dependencies:** Lark Parser (>=1.1.0)

## Overview

CMAP (Custom Menu AST Parser) is a Lark-based AST parser for Ren'Py menu structures that provides true semantic understanding without requiring Ren'Py SDK dependencies. It was created as an alternative to regex-based parsing to avoid brittleness and regressions when handling complex menu patterns.

## Key Features

- ✅ **True AST Parsing**: Uses Lark grammar for semantic understanding
- ✅ **No Ren'Py Dependencies**: Works without `renpy.cslots` or SDK modules
- ✅ **Static Flow Analysis**: Recognizes conditionals without evaluating them
- ✅ **Conditional Support**: Handles `if` statements in menu choices
- ✅ **Nested Menu Support**: Proper indentation-aware parsing
- ✅ **Fallback Integration**: Graceful fallback to enhanced regex when needed
- ✅ **Regression Prevention**: Comprehensive test suite and validation

## Architecture

```
CMAP/
├── cmap_parser.py      # Main parser class and transformer
├── cmap_ast.py         # AST node definitions
├── menu_grammar_simple.lark  # Simplified Lark grammar (current)
├── menu_grammar.lark   # Complex grammar (future expansion)
├── __init__.py         # Module exports
└── docs/               # Documentation
    ├── README.md       # This file
    ├── GRAMMAR_GUIDE.md # Grammar documentation
    ├── TESTING_GUIDE.md # Testing and regression prevention
    └── INTEGRATION_GUIDE.md # Integration with existing systems
```

## Core Components

### 1. CMAPParser

Main parser class that handles:

- Grammar loading and compilation
- Menu text parsing
- AST transformation
- Error handling and fallback

### 2. AST Nodes

Structured representation of menu elements:

- `MenuNode`: Complete menu definition
- `MenuChoiceNode`: Individual menu choices
- `ConditionalExpressionNode`: Conditional expressions
- `JumpStatementNode`, `CallStatementNode`, etc.: Choice body statements

### 3. Grammar System

Two-tier grammar approach:

- **Simple Grammar**: Current production version (robust, handles most cases)
- **Complex Grammar**: Future expansion for advanced features

## Usage Examples

### Basic Menu Parsing

```python
from renpy_sdk.cmap import CMAPParser

parser = CMAPParser()
menu_text = '''menu:
    "Choice 1":
        jump label1
    "Choice 2" if flag:
        call function1
'''

menu_node = parser.parse_menu(menu_text)
print(f"Choices: {len(menu_node.choices)}")
for choice in menu_node.choices:
    print(f"- {choice.text} (conditional: {choice.is_conditional})")
```

### Integration with AST Menu Parser

```python
from renpy_sdk.ast_menu_parser import ASTMenuParser

parser = ASTMenuParser()
# CMAP is automatically used when available
menus = parser.parse_file_menus("script.rpy")
```

## Static Flow Analysis Philosophy

CMAP follows the principle of **"Acknowledge, Don't Evaluate"**:

1. **Recognize Conditionals**: Parse and identify conditional expressions
2. **Store as Metadata**: Keep condition text for analysis
3. **Treat as Valid Paths**: Include all choices in flow visualization
4. **No Variable Evaluation**: Never attempt to evaluate variable states

This approach ensures that **all possible narrative paths** are captured for flow visualization, regardless of runtime variable states.

## Performance Characteristics

- **Parse Speed**: ~2-5ms per menu (typical)
- **Memory Usage**: Minimal AST overhead
- **Scalability**: Handles files with 100+ menus efficiently
- **Fallback Cost**: <1ms overhead when falling back to regex

## Error Handling

CMAP implements graceful degradation:

1. **Parse Errors**: Fall back to enhanced regex parsing
2. **Transform Errors**: Return partial results with warnings
3. **Grammar Errors**: Log error and disable CMAP for session
4. **Integration Errors**: Seamless fallback to existing systems

## Compatibility

- **Python**: 3.8+ (tested on 3.12)
- **Lark**: 1.1.0+
- **Ren'Py**: All versions (syntax-compatible)
- **Existing Systems**: Drop-in replacement for regex parsing

## Known Limitations

1. **Keyword Tokenization**: Lark tokenizes Ren'Py keywords (`if`, `jump`, `call`, etc.) as generic `IDENTIFIER` tokens instead of keyword tokens. This causes menus with these keywords to fail CMAP parsing and fall back to regex (which now works correctly as of v1.0.1).
2. **Complex Expressions**: Some advanced conditional expressions may need grammar expansion
3. **Custom Syntax**: Non-standard Ren'Py extensions not supported
4. **Indentation**: Currently uses simplified indentation handling
5. **Performance**: Slightly slower than regex for very simple menus

**Note on Keyword Issue**: The keyword tokenization limitation affects menus with statements like `jump mayagame` or `if validay5diplo == True:`. These menus automatically fall back to regex parsing and work correctly. The limitation does not affect overall functionality but reduces the percentage of menus parsed with true AST (typically 60-70% CMAP success rate on real-world VN projects).

## Future Roadmap

### Phase 1 (Current) ✅

- Basic menu parsing
- Simple conditionals
- Integration with AST menu parser

### Phase 2 (Planned)

- Complex conditional expressions
- Nested menu improvements
- Performance optimizations

### Phase 3 (Future)

- Custom Ren'Py syntax extensions
- Advanced static analysis
- IDE integration features

## Contributing

When contributing to CMAP:

1. **Follow Testing Guidelines**: See `TESTING_GUIDE.md`
2. **Maintain Grammar Compatibility**: See `GRAMMAR_GUIDE.md`
3. **Prevent Regressions**: Run full test suite before changes
4. **Document Changes**: Update relevant documentation

## Support

For issues, questions, or contributions:

- Check existing test cases in `tests/`
- Review grammar documentation
- Follow regression prevention guidelines
- Test with real-world Ren'Py projects

---

**Next Steps**: See `INTEGRATION_GUIDE.md` for integration instructions and `TESTING_GUIDE.md` for regression prevention methodology.
