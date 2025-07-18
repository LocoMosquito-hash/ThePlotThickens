# Ren'Py SDK Integration Tests

This directory contains tests and utilities for integrating the official Ren'Py SDK into the existing parsing system.

## Structure

```
renpy_sdk/
├── renpy-8.4.0-sdk/     # Official Ren'Py SDK (pristine, no modifications)
├── src/                 # SDK integration utilities
│   ├── __init__.py
│   └── sdk_utils.py     # Main SDK wrapper and utilities
├── tests/               # Test scripts
│   ├── __init__.py
│   └── test_basic_sdk.py  # Basic SDK integration tests
├── run_tests.py         # Test runner script
└── README.md           # This file
```

## Quick Start

1. **Run the basic test**:

   ```bash
   cd app/renpy-source-api/renpy_sdk
   python run_tests.py
   ```

2. **Expected output** (if successful):

   ```
   Ren'Py SDK Integration Test Runner
   ==================================================
   ============================================================
   TESTING SDK INITIALIZATION
   ============================================================
   ✅ SDK path added: .../renpy-8.4.0-sdk
   ✅ Successfully imported Ren'Py SDK components

   ============================================================
   TESTING SIMPLE SCRIPT PARSING
   ============================================================
   ✅ Parsing successful!
   Number of AST nodes: 4

   🎉 All tests completed successfully!
   ```

## What the Tests Do

### SDK Initialization Test

- Verifies SDK path detection
- Tests import of `renpy.parser` and `renpy.ast` modules
- Confirms SDK components are available

### Simple Parsing Test

- Parses basic Ren'Py script with labels, dialogue, and menus
- Analyzes AST node structure
- Validates basic functionality

### Complex Parsing Test

- Tests Python expressions (`$ variable = value`)
- Tests conditional menu choices (`"Choice" if condition:`)
- Tests complex control flow structures

## Integration with Existing Parser

Once tests pass, the `sdk_utils.RenpySDKManager` can be integrated into the existing `RenpyParser` class to provide:

1. **Fallback parsing** - Use SDK for complex cases where regex fails
2. **Python expression evaluation** - Handle dynamic content properly
3. **Complete AST access** - Get full syntax tree information
4. **Future-proof parsing** - Stay current with Ren'Py language updates

## Troubleshooting

### SDK Not Found

- Verify the SDK was extracted to `renpy-8.4.0-sdk/`
- Check the folder name matches exactly

### Import Errors

- Ensure you're running from the correct directory
- Try running with `python -v` to see import details

### Permission Errors

- Make sure the SDK directory is readable
- Check file permissions on Windows

## Next Steps

After basic tests pass:

1. Test on real VN script files
2. Compare results with existing regex parser
3. Design integration strategy for hybrid approach
