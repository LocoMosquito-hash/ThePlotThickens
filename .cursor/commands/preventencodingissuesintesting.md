# Prevent Encoding Issues in Testing

## Problem

Windows PowerShell defaults to legacy encodings (cp1252/cp437) which cannot handle Unicode characters like emojis (✅, ❌, 📊) or special symbols (→, •, etc.), causing `UnicodeEncodeError` crashes.

## Solution for Python Test Scripts

Always add this encoding fix at the top of any standalone test/diagnostic script:

```python
import sys

# Fix encoding for Windows to prevent Unicode crashes
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
```

## Solution for PowerShell Commands

When running Python scripts from PowerShell that use Unicode output:

```powershell
$env:PYTHONIOENCODING='utf-8'; python script_name.py
```

## Why This Matters

- **Prevents crashes** when test output includes emojis or Unicode
- **Essential for Windows development** (not needed on Linux/Mac)
- **Must be added BEFORE** any print statements that use Unicode
- **Applies to**: diagnostic scripts, test runners, CLI tools

## When to Apply

✅ **Always use in:**

- Standalone test scripts (test*\*.py, diagnose*\_.py, verify\_\_.py)
- Scripts with status indicators (✅ ❌ ⚠️)
- Scripts with progress bars or visual output
- Any script run directly from PowerShell

❌ **Not needed for:**

- Regular application code (handled by the app's initialization)
- Scripts that only output ASCII
- Linux/Mac environments
