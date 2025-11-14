# Prevent Python Cache Issues

**Use this when**: Running tests after making code changes, especially in test-heavy development sessions.

---

## 🚨 Critical Rule

**When in doubt, use a FRESH Python process. It's 2 seconds vs 20 minutes of debugging.**

---

## 📋 Pre-Test Checklist

Before running tests after code changes:

### 1. **Save All Files**

```
Ctrl+S (current file)
Ctrl+K S (all files in Cursor)
```

### 2. **Clear Python Cache**

```powershell
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### 3. **Close Running Instances**

- [ ] Close GUI applications (Flow Analyzer, etc.)
- [ ] Exit Python REPLs/interactive sessions
- [ ] Stop Jupyter kernels
- [ ] Kill any background Python processes

### 4. **Verify File Actually Changed**

```powershell
# Quick check: view last modified time
Get-Item path\to\file.py | Select-Object Name, LastWriteTime
```

---

## 🔧 Quick Cache Clear Commands

### Basic Clear (Usually Sufficient)

```powershell
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### Aggressive Clear (If Basic Doesn't Work)

```powershell
# Clear both __pycache__ directories and .pyc files
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### Nuclear Option (Cache Still Persisting)

```powershell
# 1. Clear cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 2. Kill all Python processes
Get-Process python* | Stop-Process -Force

# 3. Restart Cursor
# (Close and reopen manually)

# 4. Fresh terminal session
# (Close PowerShell, open new one)
```

---

## ✅ Reliable Testing Workflow

### Standard Flow (Recommended)

```powershell
# 1. Make code changes in IDE
# (edit your files)

# 2. Save all changes
# Ctrl+K S

# 3. Clear cache
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 4. Run tests (fresh process)
python tests/test_your_module.py

# Or with pytest:
pytest tests/ --cache-clear
```

### Paranoid Flow (When Changes Are Critical)

```powershell
# 1. Save all files
# Ctrl+K S

# 2. Close all Python instances
Get-Process python* | Stop-Process -Force

# 3. Clear cache aggressively
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force

# 4. Open NEW terminal (close current one)
# 5. Navigate to project
cd C:\Users\juanc\.cursor\worktrees\ThePlotThickens\GzpEu

# 6. Run tests
python tests/test_your_module.py
```

---

## 🐍 Python-Level Solutions

### Force Module Reload in Test Scripts

```python
# Add at top of test file (before other imports):
import sys

# Clear specific module from cache
if 'your_module' in sys.modules:
    del sys.modules['your_module']

# Now import fresh
import your_module
```

### Use importlib.reload() in Development

```python
import importlib
import your_module

# After changing code:
importlib.reload(your_module)

# ⚠️ Warning: Doesn't always work if:
# - Other modules already imported old version
# - Classes/instances already created
# - Complex dependency chains
```

### Add Cache Clear to Test Script

```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

# Clear cache before running tests
def clear_cache():
    """Clear Python cache directories."""
    cache_dirs = Path(__file__).parent.parent.rglob('__pycache__')
    for cache_dir in cache_dirs:
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"Cleared: {cache_dir}")
        except Exception as e:
            print(f"Could not clear {cache_dir}: {e}")

# Call at start of test
if __name__ == "__main__":
    clear_cache()
    # ... rest of tests
```

---

## 🔍 How to Detect Cache Issues

### Symptoms of Stale Cache:

- ✗ Changes don't appear in test output
- ✗ Old error messages still showing
- ✗ Tests fail with "undefined" errors for new code
- ✗ IDE autocomplete shows old signatures
- ✗ Import errors for recently added modules
- ✗ Tests pass locally but fail in new environment

### Quick Diagnostic:

```powershell
# Check if module is actually changed:
Get-Content path\to\module.py | Select-String "your_new_code"

# Check cache timestamp:
Get-ChildItem -Recurse __pycache__ | Select-Object Name, LastWriteTime

# Check running Python processes:
Get-Process python*
```

---

## 🎯 When to Use Each Strategy

| Situation                | Strategy               | Command                                                                       |
| ------------------------ | ---------------------- | ----------------------------------------------------------------------------- |
| **Normal development**   | Basic clear            | `Get-ChildItem -Recurse -Filter "__pycache__" \| Remove-Item -Recurse -Force` |
| **After multiple edits** | Clear + fresh terminal | Clear cache, close terminal, reopen                                           |
| **Still not working**    | Kill processes + clear | `Get-Process python* \| Stop-Process -Force`                                  |
| **Completely stuck**     | Nuclear option         | Kill processes, clear cache, restart IDE                                      |
| **Critical changes**     | Paranoid flow          | Fresh everything (terminal, IDE, processes)                                   |

---

## 💡 Prevention Best Practices

### 1. **Use Fresh Python Process Per Test**

```powershell
# DON'T do this:
python
>>> import module
>>> # test
>>> # change file
>>> import module  # STILL OLD!

# DO this:
python test.py  # Fresh process
# change file
python test.py  # Fresh process again
```

### 2. **Close Long-Running Processes**

Before testing changes:

- Close GUI apps using your code
- Exit Python REPLs
- Stop Jupyter notebooks
- Restart IDE if autocomplete is wrong

### 3. **Use Virtual Environments**

```powershell
# Isolated environment = isolated cache
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Now cache issues are contained
# Deactivate and recreate if stuck
```

### 4. **Use pytest with --cache-clear**

```powershell
pytest tests/ --cache-clear -v
```

### 5. **Add Pre-Test Hook**

Create `pre-test.ps1`:

```powershell
#!/usr/bin/env pwsh
# Clear cache before running tests
Write-Host "Clearing Python cache..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Write-Host "Cache cleared. Running tests..." -ForegroundColor Green
python tests/test_suite.py
```

Then just run:

```powershell
.\pre-test.ps1
```

---

## ⚡ Quick Command Reference

```powershell
# Save this as an alias in your PowerShell profile
# (C:\Users\juanc\Documents\PowerShell\Microsoft.PowerShell_profile.ps1)

# Quick cache clear
function Clear-PyCache {
    Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
    Write-Host "Python cache cleared!" -ForegroundColor Green
}

# Clear cache and run tests
function Test-Fresh {
    param([string]$TestFile)
    Clear-PyCache
    python $TestFile
}

# Nuclear option
function Reset-Python {
    Get-Process python* | Stop-Process -Force
    Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
    Write-Host "All Python processes killed and cache cleared!" -ForegroundColor Green
}

# Usage:
# Clear-PyCache
# Test-Fresh tests/test_integration.py
# Reset-Python
```

---

## 🛠️ Windows-Specific Issues

### File Locking

Windows may lock `.pyc` files:

```powershell
# If you get "file in use" errors:
# 1. Close all Python processes
Get-Process python* | Stop-Process -Force

# 2. Wait a moment (Windows file system delay)
Start-Sleep -Seconds 1

# 3. Try clear again
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### Timestamp Resolution

Windows file timestamps can be imprecise:

```powershell
# If rapid edits aren't detected:
# 1. Wait 2 seconds between save and test
# 2. Or force recompile by deleting .pyc
```

---

## 📝 Summary

### Golden Rules:

1. ✅ **Fresh Python process = Fresh imports**
2. ✅ **Clear cache when suspicious**
3. ✅ **Close running instances before testing**
4. ✅ **Save all files explicitly**
5. ✅ **When stuck, go nuclear (kill processes + restart IDE)**

### Most Common Fix:

```powershell
# This solves 80% of cache issues:
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
python your_test.py
```

### When All Else Fails:

```powershell
# Nuclear option (solves 99% of remaining issues):
Get-Process python* | Stop-Process -Force
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
# Close terminal
# Restart IDE
# Open new terminal
# Run tests
```

---

**Remember**: 2 seconds to clear cache vs 20 minutes debugging phantom errors. Always err on the side of caution!
