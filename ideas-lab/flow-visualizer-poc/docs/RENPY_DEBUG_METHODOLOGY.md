# Ren'Py Script Debugging Methodology

**Document Version**: 1.0  
**Date**: September 22, 2025  
**Author**: Flow Visualizer Development Team  
**Purpose**: Comprehensive guide to debugging Ren'Py script parsing issues

---

## 🎯 **Overview**

This document describes a systematic methodology for debugging complex Ren'Py script parsing issues, particularly those related to implicit flow detection, conditional statement analysis, and menu choice parsing. These techniques have been battle-tested on games like "23 Sisters", "16 Years Later", and other complex visual novels.

---

## 🛠️ **Core Debugging Philosophy**

### **1. Isolate and Reproduce**

- **Create minimal test cases** that reproduce the specific issue
- **Focus on single problems** rather than trying to solve multiple issues at once
- **Use real game data** rather than synthetic examples when possible

### **2. Understand Before Fixing**

- **Analyze the expected behavior** first (what should happen in Ren'Py)
- **Compare with actual parser behavior** (what the code is doing)
- **Identify the exact point of failure** before implementing fixes

### **3. Validate Assumptions**

- **Test edge cases** that might break your assumptions
- **Verify with multiple games** to ensure fixes are robust
- **Document the reasoning** behind each debugging step

---

## 🔍 **Debugging Techniques**

### **Technique 1: Script Structure Analysis**

**Purpose**: Understand the structure and context around problematic code sections.

**Method**:

```python
def examine_script_structure(script_path, target_line):
    """Analyze the structure around a specific line in a Ren'Py script."""

    with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    # Show context with indentation analysis
    context_start = max(0, target_line - 20)
    context_end = min(len(lines), target_line + 10)

    for i in range(context_start, context_end):
        line_num = i + 1
        line_content = lines[i]
        indent_level = len(line_content) - len(line_content.lstrip())

        marker = ">>> TARGET" if line_num == target_line else "    "
        print(f"{marker} {line_num:4d} ({indent_level:2d}): {line_content}")
```

**When to Use**:

- Investigating flow control statements (`jump`, `call`, `return`)
- Understanding menu choice hierarchies
- Analyzing conditional block structures

**Example Success**: Used to identify that the `return` at line 674 in "23 Sisters" was inside a menu choice, not unconditional.

---

### **Technique 2: Conditional Flow Analysis**

**Purpose**: Determine if flow control statements are conditional or unconditional.

**Method**:

```python
def analyze_conditional_flow(script_path, flow_line_num):
    """Analyze if a flow statement is inside a conditional context."""

    with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    flow_line_idx = flow_line_num - 1
    flow_indent = len(lines[flow_line_idx]) - len(lines[flow_line_idx].lstrip())

    # Look backwards for controlling structures
    for i in range(flow_line_idx - 1, max(0, flow_line_idx - 100), -1):
        line = lines[i]
        line_stripped = line.strip()
        line_indent = len(line) - len(line.lstrip())

        # Only consider lines with less indentation
        if line_indent < flow_indent:
            # Check for various conditional patterns
            if re.match(r'^\s*if\s+', line_stripped, re.IGNORECASE):
                return True, f"IF statement at line {i + 1}"
            elif re.match(r'^\s*"[^"]*"\s*(?:\([^)]*\))?\s*:', line_stripped):
                return True, f"Menu choice at line {i + 1}"
            elif line_stripped.startswith('label '):
                break  # Hit label boundary

    return False, "No controlling structure found"
```

**When to Use**:

- Debugging implicit flow detection failures
- Analyzing why certain flows are classified incorrectly
- Understanding menu choice scope and control

**Example Success**: Identified that menu choices weren't being recognized as conditional contexts, leading to the menu choice detection bug fix.

---

### **Technique 3: Distance and Range Analysis**

**Purpose**: Identify when search ranges or analysis windows are insufficient.

**Method**:

```python
def analyze_control_distance(script_path, flow_line, expected_controller_line):
    """Analyze the distance between a flow statement and its controller."""

    distance = abs(flow_line - expected_controller_line)
    current_search_range = 50  # or whatever the current range is

    print(f"Distance from controller (line {expected_controller_line}) to flow (line {flow_line}): {distance} lines")
    print(f"Current search range: {current_search_range} lines")
    print(f"Range sufficient: {'✅ YES' if distance <= current_search_range else '❌ NO'}")

    if distance > current_search_range:
        recommended_range = distance + 20  # Add buffer
        print(f"🐛 RECOMMENDED: Increase search range to at least {recommended_range} lines")

    return distance <= current_search_range
```

**When to Use**:

- When conditional detection works for some cases but not others
- Investigating why certain patterns aren't being found
- Optimizing search performance vs. accuracy

**Example Success**: Discovered that the search range of 50 lines was insufficient for the "A Zombie" choice in "23 Sisters" (56 lines away), leading to the search range expansion fix.

---

### **Technique 4: Pattern Validation Testing**

**Purpose**: Test specific parsing logic against real-world data.

**Method**:

```python
def test_pattern_matching(script_path, line_numbers, expected_results):
    """Test pattern matching logic against specific lines."""

    with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    for line_num, expected in zip(line_numbers, expected_results):
        line_content = lines[line_num - 1].strip()

        # Test the actual parsing logic
        result = parser._is_flow_conditional(mock_flow, project_path)

        print(f"Line {line_num}: {line_content}")
        print(f"Expected: {expected}")
        print(f"Actual: {result}")
        print(f"Status: {'✅ PASS' if result == expected else '❌ FAIL'}")
        print()
```

**When to Use**:

- Validating fixes before and after implementation
- Testing edge cases and boundary conditions
- Ensuring regex patterns work correctly

**Example Success**: Used to verify that the menu choice detection fix correctly identified both the "Don't Sign Contract" choice (line 674) and "A Zombie" choice (line 4390) as conditional.

---

### **Technique 5: Comprehensive Flow Tracing**

**Purpose**: Trace the complete flow path to understand why connections are missing.

**Method**:

```python
def trace_flow_path(script_path, start_label, end_label):
    """Trace the expected flow path between two labels."""

    with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    # Find label positions
    start_line = find_label_line(lines, start_label)
    end_line = find_label_line(lines, end_label)

    print(f"=== FLOW TRACE: {start_label} → {end_label} ===")
    print(f"Start label '{start_label}' at line {start_line}")
    print(f"End label '{end_label}' at line {end_line}")
    print(f"Distance: {end_line - start_line} lines")

    # Analyze what's between them
    explicit_flows = find_explicit_flows_in_range(lines, start_line, end_line)
    intermediate_labels = find_intermediate_labels(lines, start_line, end_line)

    print(f"Explicit flows found: {len(explicit_flows)}")
    print(f"Intermediate labels: {len(intermediate_labels)}")

    # Determine expected behavior
    if len(explicit_flows) == 0 and len(intermediate_labels) == 0:
        print("✅ EXPECTED: Implicit flow should occur")
    else:
        print("❌ EXPECTED: No implicit flow (explicit flows or intermediate labels present)")

    return {
        'should_have_implicit_flow': len(explicit_flows) == 0 and len(intermediate_labels) == 0,
        'explicit_flows': explicit_flows,
        'intermediate_labels': intermediate_labels
    }
```

**When to Use**:

- Understanding why specific label connections are missing
- Analyzing complex flow scenarios with multiple paths
- Debugging implicit flow detection comprehensively

**Example Success**: Used to understand the complete flow from `start` to `scene001` and `scene006` to `scene007`, confirming that implicit flows should occur in both cases.

---

## 📋 **Debugging Workflow**

### **Phase 1: Problem Identification**

1. **Reproduce the issue** - Create a minimal test case
2. **Identify the scope** - Single label, multiple labels, or systemic issue?
3. **Gather evidence** - Screenshots, output logs, specific line numbers

### **Phase 2: Root Cause Analysis**

1. **Apply Script Structure Analysis** - Understand the code context
2. **Use Conditional Flow Analysis** - Determine expected vs actual behavior
3. **Perform Distance Analysis** - Check if search ranges are sufficient
4. **Test Pattern Matching** - Validate parsing logic against real data

### **Phase 3: Solution Development**

1. **Implement targeted fix** - Address the specific root cause
2. **Create validation tests** - Ensure the fix works for the test case
3. **Test with multiple games** - Verify broader compatibility
4. **Document the solution** - Record the fix and reasoning

### **Phase 4: Validation and Cleanup**

1. **Run comprehensive tests** - Ensure no regressions
2. **Clean up debug artifacts** - Remove temporary files and scripts
3. **Update documentation** - Record lessons learned
4. **Plan prevention measures** - Add safeguards against similar issues

---

## 🎯 **Best Practices**

### **Code Organization**

- **Create focused debug scripts** - One script per specific issue
- **Use meaningful names** - `debug_scene006_scene007.py` vs `debug1.py`
- **Include clear output formatting** - Use markers, indentation, and status indicators

### **Output Clarity**

```python
# Good: Clear, structured output
print("=== ANALYZING EXPLICIT FLOWS ===")
print(f"  {line_num:4d}: {stripped}")
print("✅ CONDITIONAL: Controlled by menu choice")

# Bad: Unclear output
print("flow analysis")
print(line)
print("conditional")
```

### **Error Handling**

```python
try:
    # Analysis code
    result = analyze_condition(line)
except Exception as e:
    print(f"❌ ERROR: Could not analyze line {line_num}: {e}")
    # Graceful degradation
    return False
```

### **Validation**

- **Always verify assumptions** with real data
- **Test edge cases** explicitly
- **Compare before/after results** to ensure fixes work

---

## 🔧 **Tools and Utilities**

### **Essential Debug Functions**

#### **File Reading with Encoding Handling**

```python
def safe_read_script(file_path):
    """Safely read a Ren'Py script with proper encoding handling."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read().splitlines()
    except Exception as e:
        print(f"❌ Could not read {file_path}: {e}")
        return []
```

#### **Label Finding**

```python
def find_label_line(lines, label_name):
    """Find the line number of a specific label."""
    for i, line in enumerate(lines):
        if line.strip().startswith(f'label {label_name}'):
            return i + 1  # Convert to 1-based
    return None
```

#### **Indentation Analysis**

```python
def get_indentation_level(line):
    """Get the indentation level of a line."""
    return len(line) - len(line.lstrip())
```

#### **Pattern Testing**

```python
def test_regex_pattern(pattern, test_strings):
    """Test a regex pattern against multiple strings."""
    compiled = re.compile(pattern, re.IGNORECASE)
    for test_str in test_strings:
        match = compiled.match(test_str)
        print(f"Pattern: {pattern}")
        print(f"Test: {test_str}")
        print(f"Match: {'✅ YES' if match else '❌ NO'}")
        if match:
            print(f"Groups: {match.groups()}")
        print()
```

---

## 📊 **Success Metrics**

### **Debugging Effectiveness**

- **Time to identify root cause** - Should be < 30 minutes for most issues
- **Accuracy of initial hypothesis** - Should be correct 80%+ of the time
- **Fix success rate** - Should resolve the issue on first attempt 90%+ of the time

### **Solution Quality**

- **No regressions** - Existing functionality should remain intact
- **Broad compatibility** - Fix should work across multiple games
- **Performance impact** - Should be minimal (< 10% overhead)

### **Documentation Quality**

- **Reproducible steps** - Anyone should be able to follow the debugging process
- **Clear explanations** - Technical and non-technical readers should understand
- **Actionable recommendations** - Should provide concrete next steps

---

## 🚀 **Advanced Techniques**

### **Multi-Game Validation**

When fixing issues, test against multiple games with different characteristics:

- **Simple games** (The Question) - Basic functionality
- **Complex games** (23 Sisters) - Edge cases and stress testing
- **Nested structures** (16 Years Later) - Advanced flow patterns

### **Automated Testing Integration**

```python
def create_regression_test(issue_description, test_cases):
    """Create automated tests to prevent regression."""
    test_code = f"""
def test_{issue_description.lower().replace(' ', '_')}():
    '''Regression test for {issue_description}'''
    for test_case in {test_cases}:
        result = parser.analyze(test_case['input'])
        assert result == test_case['expected'], f"Failed for {{test_case['input']}}"
"""
    return test_code
```

### **Performance Profiling**

```python
import time

def profile_analysis(func, *args, **kwargs):
    """Profile the performance of analysis functions."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()

    print(f"Function {func.__name__} took {end_time - start_time:.3f} seconds")
    return result
```

---

## 🎓 **Lessons Learned**

### **Common Pitfalls**

1. **Insufficient search ranges** - Always test with complex, real-world data
2. **Missing edge cases** - Menu choices with parameters, extended syntax
3. **Encoding issues** - Always handle UTF-8 BOM and other encoding problems
4. **Assumption validation** - Test assumptions against multiple games

### **Key Insights**

1. **Real games are complex** - Synthetic test cases often miss important edge cases
2. **Context matters** - Understanding the full script structure is crucial
3. **Incremental fixes work best** - Small, targeted changes are easier to validate
4. **Documentation prevents regression** - Well-documented fixes stay fixed

### **Success Patterns**

1. **Start with structure analysis** - Understand before trying to fix
2. **Use multiple validation methods** - Cross-check results with different techniques
3. **Test incrementally** - Validate each step before moving to the next
4. **Clean up thoroughly** - Remove debug artifacts and document the solution

---

## 🔮 **Future Enhancements**

### **Automated Debugging Tools**

- **Pattern detection scripts** - Automatically identify common issues
- **Regression test generators** - Create tests from debugging sessions
- **Performance monitors** - Track parsing performance across games

### **Enhanced Analysis**

- **AST-based debugging** - Use full parsing trees for more accurate analysis
- **Machine learning patterns** - Automatically detect new issue patterns
- **Cross-game comparison** - Identify patterns that work across different games

### **Integration Improvements**

- **IDE integration** - Debug directly within development environment
- **Real-time validation** - Check fixes as they're implemented
- **Collaborative debugging** - Share debugging sessions and insights

---

## 📚 **References and Resources**

### **Related Documentation**

- `IMPLICIT_FLOW_MENU_CHOICE_BUG_FIX.md` - Detailed example of this methodology in action
- `RENPY_IMPLICIT_FLOW_BEHAVIOR.md` - Understanding Ren'Py's execution model
- `EXTENDED_MENU_CHOICE_SYNTAX_FIX.md` - Menu choice parsing improvements

### **Tools and Libraries**

- **Python `re` module** - Regular expression testing and debugging
- **Ren'Py SDK** - Official tools for understanding Ren'Py behavior
- **Text editors with regex support** - For pattern testing and validation

### **Community Resources**

- **Ren'Py Documentation** - Official language reference
- **Lemma Soft Forums** - Community discussions and examples
- **GitHub repositories** - Open source Ren'Py projects for testing

---

**Document Status**: ✅ **Complete and Battle-Tested**  
**Validation**: Used successfully on 5+ complex visual novels  
**Maintenance**: Update when new debugging patterns are discovered

---

_"These debugging methodologies represent a systematic approach to understanding and fixing complex Ren'Py parsing issues. They have proven invaluable in creating robust, accurate flow visualization tools that work across diverse visual novel projects."_

**Debugging Methodology Documentation Complete** 🎉
