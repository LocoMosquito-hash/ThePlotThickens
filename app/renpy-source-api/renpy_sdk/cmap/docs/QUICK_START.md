# CMAP Quick Start Guide

## What is CMAP?

**CMAP (Custom Menu AST Parser)** is a Lark-based AST parser that provides true semantic understanding of Ren'Py menu structures without requiring Ren'Py SDK dependencies. It was created to replace brittle regex-based parsing with robust AST analysis.

## 🚀 Quick Setup

### 1. Check if CMAP is Available

```python
try:
    from renpy_sdk.cmap import CMAPParser
    print("✅ CMAP is available!")
except ImportError:
    print("❌ CMAP not available - check Lark installation")
```

### 2. Basic Usage

```python
from renpy_sdk.cmap import CMAPParser

# Initialize parser
parser = CMAPParser()

# Parse a menu
menu_text = '''menu:
    "Go to park":
        jump park_scene
    "Stay home" if tired:
        call rest_function
    "Study magic" if has_magic and score > 10:
        jump magic_school'''

result = parser.parse_menu(menu_text)

if result:
    print(f"✅ Parsed menu with {len(result.choices)} choices")
    for choice in result.choices:
        status = "conditional" if choice.is_conditional else "simple"
        print(f"  - '{choice.text}' ({status})")
else:
    print("❌ Parsing failed")
```

### 3. Integration (Automatic)

```python
from renpy_sdk.ast_menu_parser import ASTMenuParser

# CMAP is automatically used when available
parser = ASTMenuParser()
menus = parser.parse_file_menus("your_script.rpy")

# CMAP provides better accuracy than regex parsing
```

## 🎯 Key Benefits

### ✅ **True AST Parsing**

- Semantic understanding, not pattern matching
- Handles complex nested structures correctly
- Robust against syntax variations

### ✅ **Static Flow Analysis**

- Recognizes conditionals without evaluating them
- Captures all possible narrative paths
- Perfect for flow visualization

### ✅ **No Dependencies**

- Works without Ren'Py SDK
- No `renpy.cslots` or other compiled modules needed
- Pure Python with Lark parser

### ✅ **Regression Prevention**

- Comprehensive test suite
- Graceful fallback to regex
- Maintains backward compatibility

## 📋 What CMAP Handles

### ✅ **Supported Patterns**

```renpy
# Simple menus
menu:
    "Choice 1":
        jump scene1
    "Choice 2":
        call function1

# Conditional choices
menu:
    "Use magic" if has_magic:
        jump magic_scene
    "Fight" if strength > 5:
        jump battle_scene
    "Run away":
        jump escape_scene

# Named menus
menu main_menu:
    "Start Game":
        jump start
    "Load Game":
        call load_screen

# Various statements
menu:
    "Jump somewhere":
        jump target_label
    "Call function":
        call my_function
    "Return":
        return
    "Do nothing":
        pass
```

### ⚠️ **Current Limitations**

```renpy
# Complex conditionals (planned for v1.1)
menu:
    "Complex choice" if (flag and not other_flag) or score > 100:
        pass

# Multi-line statements (planned for v1.2)
menu:
    "Multi-line":
        $ complex_variable = some_long_expression \
            + another_part
        jump next
```

## 🔧 Regression Prevention

CMAP includes comprehensive regression prevention:

### **Before Making Changes**

```bash
# Run full test suite
python -m pytest cmap/tests/ -v

# Test real-world compatibility
python test_real_games.py
```

### **Change Process**

1. **Write failing test** for new feature
2. **Implement minimal change** to pass test
3. **Run regression tests** to ensure no breakage
4. **Validate with real games** before deployment

### **Test Categories**

- **Unit Tests**: Core parsing functionality
- **Integration Tests**: System-level compatibility
- **Regression Tests**: Real-world game compatibility
- **Performance Tests**: Speed and memory benchmarks

## 📚 Documentation Structure

```
cmap/docs/
├── README.md           # Overview and architecture
├── QUICK_START.md      # This file - get started fast
├── API_REFERENCE.md    # Complete API documentation
├── GRAMMAR_GUIDE.md    # Grammar development guide
├── TESTING_GUIDE.md    # Regression prevention methodology
├── INTEGRATION_GUIDE.md # System integration patterns
└── CHANGELOG.md        # Version history and changes
```

## 🐛 Troubleshooting

### **CMAP Not Working?**

```python
# Check CMAP health
def check_cmap_health():
    try:
        from renpy_sdk.cmap import CMAPParser
        parser = CMAPParser()

        # Test basic parsing
        result = parser.parse_menu('menu:\n    "Test":\n        pass')

        if result and len(result.choices) == 1:
            print("✅ CMAP is working correctly")
            return True
        else:
            print("❌ CMAP parsing failed")
            return False

    except Exception as e:
        print(f"❌ CMAP error: {e}")
        return False

check_cmap_health()
```

### **Parsing Failures?**

- CMAP automatically falls back to enhanced regex
- Check logs for specific error messages
- Validate menu syntax is standard Ren'Py
- Report complex cases for future grammar expansion

### **Performance Issues?**

- CMAP is optimized for typical use cases
- Large files (>1MB) may need chunking
- Enable result caching for repeated parsing
- Monitor memory usage with very large projects

## 🚀 Next Steps

1. **Try CMAP**: Test with your Ren'Py projects
2. **Check Results**: Compare with previous regex parsing
3. **Report Issues**: Help improve CMAP with real-world feedback
4. **Contribute**: Add test cases for your specific patterns

## 💡 Pro Tips

### **Best Practices**

- Let CMAP handle parsing automatically through AST Menu Parser
- Use validation methods to check parsing quality
- Monitor fallback rates to identify improvement opportunities
- Keep grammar files in version control

### **Performance Optimization**

- Cache parsing results for repeated operations
- Use file modification time to avoid re-parsing unchanged files
- Process files in parallel for large projects
- Monitor memory usage with profiling tools

### **Integration Patterns**

- Always provide fallback mechanisms
- Validate data at integration boundaries
- Use consistent error handling across systems
- Log parsing statistics for monitoring

---

**Ready to get started?** CMAP is designed to work seamlessly with your existing code. Just ensure Lark is installed and CMAP will automatically enhance your menu parsing capabilities! 🎉
