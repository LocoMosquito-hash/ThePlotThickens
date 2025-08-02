# 🚨 ENVIRONMENT CONTEXT - The Plot Thickens 🚨

**⚠️ BEFORE ANY TERMINAL COMMAND - CHECK THIS:**

- **Windows 11** (NOT Linux/Mac)
- **PowerShell** (NOT Bash/Zsh)
- **Use PowerShell Cmdlets** (Remove-Item, NOT rm)

## 🔒 CRITICAL GIT WORKFLOW RULE

**⛔ NEVER TOUCH GIT WITHOUT EXPLICIT USER PERMISSION ⛔**

- **NO automatic staging, committing, or any git operations**
- **USER controls ALL git workflow decisions**
- **Ask permission before ANY git-related actions**
- See `🚨_GIT_CONTROL_WARNING.md` for full details

## System Information

- **OS**: Windows 11
- **Shell**: PowerShell 5.1+ (NOT Command Prompt, NOT Bash)
- **Python**: Virtual environment at `.\venv\Scripts\Activate.ps1`
- **Project Root**: `C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens`

## Command Syntax Rules

- Use PowerShell cmdlets: `Remove-Item` NOT `rm`
- Command chaining: Use `;` NOT `&&`
- Path separators: `\` or `/` (both work)
- Application launcher: `python run.py`

## Quick Reference

```powershell
# Delete files/folders
Remove-Item -Recurse -Force folder_name

# Chain commands
command1; command2

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Start application
python run.py
```
