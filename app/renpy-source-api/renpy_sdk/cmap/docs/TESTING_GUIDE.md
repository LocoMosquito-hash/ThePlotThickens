# CMAP Testing Guide & Regression Prevention

## Overview

This guide outlines the comprehensive testing methodology for CMAP to prevent regressions when making changes to conditional behavior, nested menus, or other parsing features.

## Testing Philosophy

**"Test First, Change Second"** - Every change to CMAP must be validated against existing functionality before implementation.

## Test Categories

### 1. Unit Tests (Core Functionality)

#### Basic Menu Parsing

```python
def test_simple_menu():
    """Test basic menu without conditionals."""
    menu_text = '''menu:
        "Choice 1":
            jump label1
        "Choice 2":
            pass'''

    result = parser.parse_menu(menu_text)
    assert len(result.choices) == 2
    assert result.choices[0].text == "Choice 1"
    assert not result.choices[0].is_conditional
```

#### Conditional Parsing

```python
def test_conditional_menu():
    """Test menu with conditional choices."""
    menu_text = '''menu:
        "Choice 1":
            pass
        "Choice 2" if flag:
            pass
        "Choice 3" if score > 10:
            jump next_scene'''

    result = parser.parse_menu(menu_text)
    assert len(result.choices) == 3
    assert not result.choices[0].is_conditional
    assert result.choices[1].is_conditional
    assert result.choices[2].is_conditional
```

#### Nested Menu Detection

```python
def test_nested_menus():
    """Test proper handling of nested menu structures."""
    menu_text = '''menu:
        "Outer Choice 1":
            menu:
                "Inner Choice 1":
                    pass
                "Inner Choice 2":
                    pass
        "Outer Choice 2":
            pass'''

    # Should detect nested structure without merging choices
    result = parser.parse_menu(menu_text)
    assert len(result.choices) == 2  # Only outer choices
```

### 2. Integration Tests (System Level)

#### AST Menu Parser Integration

```python
def test_ast_integration():
    """Test CMAP integration with AST menu parser."""
    parser = ASTMenuParser()

    # Create test file with various menu types
    test_content = create_complex_menu_file()

    menus = parser.parse_file_menus("test.rpy")

    # Validate all menu types are handled
    assert any(menu.has_complex_conditionals for menu in menus)
    assert any(menu.has_nested_menus for menu in menus)
```

#### Flow Visualizer Integration

```python
def test_flow_visualizer_integration():
    """Test CMAP results work with flow visualizer."""
    # Test that CMAP-parsed menus create valid flow connections
    pass
```

### 3. Regression Tests (Real-World Cases)

#### Known Issue Cases

```python
def test_16_years_later_menu_stealing():
    """Regression test for menu choice stealing issue."""
    # Test the specific case from "16 years later!"
    script_content = load_real_script("chloeskateboardrom")

    menus = parser.parse_file_menus(script_content)

    # Validate no choice stealing occurs
    validate_no_choice_stealing(menus)
```

#### Game-Specific Tests

```python
def test_amnesia_wardrobe():
    """Test parsing of Amnesia Wardrobe menu patterns."""
    pass

def test_apocalypse_lovers():
    """Test parsing of Apocalypse Lovers menu patterns."""
    pass

def test_babysitter_named_menus():
    """Test parsing of Babysitter named menu patterns."""
    pass
```

## Regression Prevention Methodology

### 1. Pre-Change Validation

Before making any changes to CMAP:

```bash
# 1. Run full test suite
python -m pytest cmap/tests/ -v

# 2. Run integration tests
python test_cmap_integration.py

# 3. Run real-world validation
python validate_real_games.py
```

### 2. Change Implementation Process

#### Step 1: Create Failing Test

```python
def test_new_conditional_feature():
    """Test for the new feature being implemented."""
    # This should fail initially
    menu_text = '''menu:
        "Choice" if complex_condition and (flag or not other_flag):
            pass'''

    result = parser.parse_menu(menu_text)
    assert result.choices[0].is_conditional
    # This will fail until feature is implemented
```

#### Step 2: Implement Minimal Change

- Make the smallest possible change to pass the new test
- Avoid touching unrelated code paths
- Use feature flags if necessary for gradual rollout

#### Step 3: Validate No Regressions

```bash
# Run all existing tests
python -m pytest cmap/tests/ -v

# Check specific regression areas
python test_nested_menus.py
python test_conditional_parsing.py
python test_statement_parsing.py
```

### 3. Post-Change Validation

#### Automated Validation

```python
def validate_parsing_consistency():
    """Ensure parsing results are consistent across changes."""
    test_cases = load_test_menu_library()

    for test_case in test_cases:
        old_result = test_case.expected_result
        new_result = parser.parse_menu(test_case.menu_text)

        assert_results_equivalent(old_result, new_result)
```

#### Manual Validation Checklist

- [ ] Simple menus still parse correctly
- [ ] Conditional menus maintain conditional detection
- [ ] Nested menus don't merge choices incorrectly
- [ ] Statement parsing remains accurate
- [ ] Performance hasn't degraded significantly
- [ ] Error handling still works gracefully

## Test Data Management

### Test Menu Library

Maintain a comprehensive library of test menus:

```
cmap/tests/data/
├── simple_menus/
│   ├── basic_two_choice.rpy
│   ├── single_choice.rpy
│   └── empty_menu.rpy
├── conditional_menus/
│   ├── simple_flag.rpy
│   ├── comparison_operators.rpy
│   └── complex_expressions.rpy
├── nested_menus/
│   ├── two_level_nesting.rpy
│   ├── deep_nesting.rpy
│   └── mixed_conditional_nested.rpy
└── real_world_samples/
    ├── 16_years_later_chloeskateboardrom.rpy
    ├── amnesia_wardrobe_sample.rpy
    └── babysitter_named_menu.rpy
```

### Expected Results Database

```python
# Store expected parsing results for regression detection
EXPECTED_RESULTS = {
    "simple_two_choice": {
        "choice_count": 2,
        "conditional_count": 0,
        "nested_count": 0
    },
    "conditional_flag": {
        "choice_count": 2,
        "conditional_count": 1,
        "conditions": ["flag"]
    }
    # ... more test cases
}
```

## Performance Regression Detection

### Benchmarking

```python
def benchmark_parsing_performance():
    """Ensure changes don't degrade performance."""
    test_files = load_performance_test_files()

    for file_path, expected_time in test_files:
        start_time = time.time()
        result = parser.parse_file_menus(file_path)
        elapsed = time.time() - start_time

        assert elapsed <= expected_time * 1.1  # 10% tolerance
```

### Memory Usage Monitoring

```python
def monitor_memory_usage():
    """Track memory usage for large files."""
    import psutil

    process = psutil.Process()
    initial_memory = process.memory_info().rss

    # Parse large file
    parser.parse_file_menus("large_test_file.rpy")

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    assert memory_increase < MAX_ACCEPTABLE_MEMORY_INCREASE
```

## Continuous Integration

### Automated Test Pipeline

```yaml
# .github/workflows/cmap_tests.yml
name: CMAP Regression Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.12
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run CMAP unit tests
        run: python -m pytest cmap/tests/unit/ -v
      - name: Run integration tests
        run: python -m pytest cmap/tests/integration/ -v
      - name: Run regression tests
        run: python -m pytest cmap/tests/regression/ -v
      - name: Performance benchmarks
        run: python cmap/tests/benchmark.py
```

## Error Handling Validation

### Graceful Degradation Tests

```python
def test_malformed_menu_handling():
    """Ensure malformed menus don't crash the parser."""
    malformed_menus = [
        "menu:\n    invalid syntax here",
        "menu:\n    \"Choice\" if :\n        pass",
        "menu:\n    \"Choice\":\n        invalid_statement"
    ]

    for menu_text in malformed_menus:
        result = parser.parse_menu(menu_text)
        # Should return None or partial result, not crash
        assert result is None or isinstance(result, MenuNode)
```

### Fallback Mechanism Tests

```python
def test_regex_fallback():
    """Ensure fallback to regex works when CMAP fails."""
    # Test that AST menu parser falls back gracefully
    parser = ASTMenuParser()

    # Temporarily break CMAP
    parser.has_cmap = False

    menus = parser.parse_file_menus("test.rpy")
    # Should still get results from regex parser
    assert len(menus) > 0
```

## Documentation of Changes

### Change Log Format

```markdown
## Version 1.1.0 - 2024-01-XX

### Added

- Support for complex conditional expressions with parentheses
- New grammar rules for compound logical operators

### Changed

- Improved performance for large menu files (15% faster)
- Enhanced error messages for malformed conditionals

### Fixed

- Issue #123: Nested menus incorrectly merging choices
- Regression in statement parsing for call statements

### Regression Tests Added

- test_complex_conditionals_with_parentheses()
- test_compound_logical_operators()
- test_nested_menu_choice_separation()

### Performance Impact

- Parse time: -15% (improvement)
- Memory usage: +2% (acceptable)
- Fallback overhead: No change
```

## Best Practices for Changes

1. **Isolate Changes**: Make changes to specific components without affecting others
2. **Feature Flags**: Use flags for experimental features
3. **Backward Compatibility**: Maintain compatibility with existing AST structures
4. **Comprehensive Testing**: Test both positive and negative cases
5. **Performance Monitoring**: Track performance impact of changes
6. **Documentation**: Update documentation with every change

## Emergency Rollback Procedure

If a change causes regressions:

1. **Immediate Rollback**: Revert to previous working version
2. **Identify Root Cause**: Analyze what went wrong
3. **Fix in Isolation**: Create minimal fix with comprehensive tests
4. **Gradual Redeployment**: Deploy with additional monitoring

---

**Remember**: The goal is to enhance CMAP while maintaining 100% reliability for existing functionality. When in doubt, prefer conservative changes with extensive testing.
