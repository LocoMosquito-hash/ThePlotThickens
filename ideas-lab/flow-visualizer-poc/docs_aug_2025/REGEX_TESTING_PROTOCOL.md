# 🚨 Screen Element Regex Testing Protocol

**Document Version:** 1.0  
**Date:** September 2025  
**Status:** MANDATORY COMPLIANCE

## ⚠️ CRITICAL REQUIREMENT

**EVERY modification to screen element regex patterns MUST be validated with the robustness test suite.**

## 📍 When This Protocol Applies

This protocol is **MANDATORY** when making changes to:

### **Files That Require Testing:**

- `app/renpy-source-api/parser.py` - All regex patterns in the `patterns` dictionary
- Any screen parsing logic modifications
- Multi-line parsing algorithm changes

### **Specific Patterns That Require Testing:**

```python
'textbutton': re.compile(...)     # ⚠️ TEST REQUIRED
'imagebutton': re.compile(...)    # ⚠️ TEST REQUIRED
'hotspot': re.compile(...)        # ⚠️ TEST REQUIRED
'screen_definition': re.compile(...) # ⚠️ TEST REQUIRED
```

### **Multi-line Parsing Logic:**

- Any changes to the multi-line imagebutton detection in `parse_screen_structure()`
- Quote handling modifications (`"` vs `'`)
- Action pattern matching (`Jump()`, `Call()`)

## 🧪 Test Execution Protocol

### **Step 1: Run the Test Suite**

```bash
cd ideas-lab/flow-visualizer-poc
python test_screen_regex_robustness.py
```

### **Step 2: Interpret Results**

- **✅ All tests pass**: Safe to commit changes
- **❌ Any test fails**: **DO NOT COMMIT** until fixed

### **Step 3: Handle Failures**

If tests fail:

1. **Identify the regression**: Which previously working pattern now fails?
2. **Fix the pattern**: Modify regex to support both old and new cases
3. **Re-run tests**: Ensure all tests pass
4. **Add new test case**: If fixing a new VN, add it to the test suite

## 📝 Adding New Test Cases

When you encounter a **new working screen syntax** from a VN:

### **Step 1: Document the Pattern**

```python
{
    "name": "Pattern description (VN Name)",
    "vn_source": "VN Name",
    "element_type": "textbutton|imagebutton|hotspot",
    "content": "actual working syntax from VN",
    "expected": {
        "text": "expected text",           # for textbuttons
        "action_type": "Jump|Call",
        "destination": "expected_destination"
    }
}
```

### **Step 2: Add to Test Suite**

Add the test case to the `_get_comprehensive_test_cases()` method in:
`ideas-lab/flow-visualizer-poc/test_screen_regex_robustness.py`

### **Step 3: Validate**

Run the test to ensure your new case passes before considering the fix complete.

## 🏗️ Current Test Coverage

### **VN Syntax Patterns Covered:**

- **Generic**: Basic patterns that should work everywhere
- **Apocalust**: Complex styled textbuttons with extensive parameters
- **Come Home**: Multi-line imagebuttons with focus_mask
- **Amnesia**: Multi-line imagebuttons with anchor positioning and single quotes
- **AoA Academy**: Hotspots with Call actions and various coordinate sizes

### **Pattern Variations Covered:**

- **Quote Types**: Both `"destination"` and `'destination'`
- **Action Types**: Both `Jump()` and `Call()` actions
- **Single-line vs Multi-line**: All parsing approaches
- **Complex Styling**: Extensive parameter lists between element and action
- **Coordinate Variations**: Different hotspot coordinate ranges

## 🔄 Continuous Improvement

### **When Adding Support for New VNs:**

1. **Document working patterns**: Add test cases for any new syntax
2. **Test existing patterns**: Ensure new changes don't break old VNs
3. **Update this documentation**: Keep the coverage list current

### **Pattern Evolution Strategy:**

- **Prefer additive changes**: Extend patterns rather than replacing them
- **Use pattern priorities**: Handle conflicts with ordered matching
- **Document breaking changes**: If a pattern must change, document the impact

## 🚨 Emergency Protocol

If you **must** commit urgent changes without full testing:

1. **Create a hotfix branch**
2. **Document the technical debt** in this file
3. **Schedule immediate testing** as the next priority task
4. **Add the urgent case** to the test suite retroactively

**Technical Debt Log:**

- None currently (maintain this section)

## 📊 Test Suite Metrics

**Current Test Coverage:**

- **Total Test Cases**: 12 comprehensive patterns
- **VNs Covered**: 5 different syntax styles
- **Pattern Types**: 3 element types (textbutton, imagebutton, hotspot)
- **Complexity Levels**: Simple, styled, multi-line, complex coordinates

**Success Criteria:**

- **100% test pass rate** required for commit approval
- **Zero regressions** in previously working patterns
- **New VN support** must include test case addition

---

## 🎯 Remember: Prevention is Better Than Debugging

**5 minutes of testing prevents hours of debugging across multiple VNs!**

This protocol exists because screen element parsing is **critical infrastructure** for the flow visualizer. A single regex change can break visualization for entire VNs, making this testing **non-negotiable**.
