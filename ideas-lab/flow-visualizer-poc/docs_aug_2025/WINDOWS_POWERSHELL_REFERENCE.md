# Windows PowerShell Reference - The Plot Thickens

## Environment Context

**Operating System**: Windows 11  
**Shell**: PowerShell (NOT Command Prompt or Bash)  
**Project Root**: `C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens`

## Common Command Translations

### File Operations

| Unix/Bash          | PowerShell                                 | Description                  |
| ------------------ | ------------------------------------------ | ---------------------------- |
| `rm -rf directory` | `Remove-Item -Recurse -Force directory`    | Delete directory recursively |
| `rm file.txt`      | `Remove-Item file.txt`                     | Delete file                  |
| `cp source dest`   | `Copy-Item source dest`                    | Copy file                    |
| `mv old new`       | `Move-Item old new`                        | Move/rename file             |
| `ls`               | `Get-ChildItem` or `dir`                   | List directory contents      |
| `cat file.txt`     | `Get-Content file.txt`                     | Display file contents        |
| `which command`    | `Get-Command command`                      | Find command location        |
| `pwd`              | `Get-Location` or `pwd`                    | Current directory            |
| `cd directory`     | `Set-Location directory` or `cd directory` | Change directory             |

### Text Operations

| Unix/Bash             | PowerShell                              | Description           |
| --------------------- | --------------------------------------- | --------------------- |
| `grep pattern file`   | `Select-String pattern file`            | Search text in file   |
| `find . -name "*.py"` | `Get-ChildItem -Recurse -Filter "*.py"` | Find files by pattern |
| `head -n 10 file`     | `Get-Content file -Head 10`             | First 10 lines        |
| `tail -n 10 file`     | `Get-Content file -Tail 10`             | Last 10 lines         |

### Process Operations

| Unix/Bash         | PowerShell                    | Description    |
| ----------------- | ----------------------------- | -------------- |
| `ps aux`          | `Get-Process`                 | List processes |
| `kill -9 PID`     | `Stop-Process -Id PID -Force` | Kill process   |
| `killall process` | `Stop-Process -Name process`  | Kill by name   |

### Environment Variables

| Unix/Bash          | PowerShell                            | Description              |
| ------------------ | ------------------------------------- | ------------------------ |
| `export VAR=value` | `$env:VAR = "value"`                  | Set environment variable |
| `echo $VAR`        | `$env:VAR` or `Write-Output $env:VAR` | Display variable         |

### Package Management

| Unix/Bash             | PowerShell            | Description |
| --------------------- | --------------------- | ----------- |
| `pip install package` | `pip install package` | ✅ Same     |
| `npm install package` | `npm install package` | ✅ Same     |
| `python script.py`    | `python script.py`    | ✅ Same     |

### Command Chaining

| Unix/Bash      | PowerShell     | Description               |
| -------------- | -------------- | ------------------------- |
| `cmd1 && cmd2` | `cmd1; cmd2`   | Run commands sequentially |
| `cmd1 \| cmd2` | `cmd1 \| cmd2` | ✅ Pipe works the same    |

## PowerShell-Specific Features

### Path Handling

```powershell
# PowerShell uses backslashes for paths
C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens

# But forward slashes work too in most contexts
C:/Users/juanc/PycharmProjects/TPT3/ThePlotThickens
```

### Execution Policy

```powershell
# Check execution policy
Get-ExecutionPolicy

# Set execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Virtual Environment Activation

```powershell
# Activate Python virtual environment
.\venv\Scripts\Activate.ps1

# NOT: source venv/bin/activate (Unix)
```

## Common Project Commands

### Python Development

```powershell
# Run the main application
python run.py

# Run tests
python -m pytest

# Install requirements
pip install -r requirements.txt
```

### Node.js/NPM Commands

```powershell
# Install packages globally
npm install -g package-name

# Install project dependencies
npm install

# Run npm scripts
npm run build
npm start
```

### Git Operations

```powershell
# All git commands work the same
git status
git add .
git commit -m "message"
git push
```

## Application Launch Strategy

**IMPORTANT**: For The Plot Thickens project:

- Always use `python run.py` to start the application
- Use PowerShell syntax: `;` for command chaining (NOT `&&`)
- Present "Run" button instead of "open terminal" for user-friendly experience

## Directory Structure Commands

```powershell
# Navigate to project root
Set-Location "C:\Users\juanc\PycharmProjects\TPT3\ThePlotThickens"

# List project structure
Get-ChildItem -Recurse -Directory | Select-Object FullName

# Find Python files
Get-ChildItem -Recurse -Filter "*.py" | Select-Object Name, FullName
```

## Error Handling

### Common PowerShell Errors and Solutions

1. **"Execution of scripts is disabled"**

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **"Command not found"**

   ```powershell
   # Check if command exists
   Get-Command command-name

   # Add to PATH if needed
   $env:PATH += ";C:\path\to\command"
   ```

3. **"Access Denied"**
   ```powershell
   # Run as administrator or check permissions
   # Use -Force parameter for file operations when needed
   ```

## Best Practices for AI Assistants

1. **Always assume PowerShell syntax** for this project
2. **Use full cmdlet names** for clarity (e.g., `Remove-Item` not `rm`)
3. **Test commands** before suggesting complex operations
4. **Provide PowerShell alternatives** when suggesting Unix commands
5. **Remember the virtual environment path**: `.\venv\Scripts\Activate.ps1`

---

_This reference document helps ensure consistent PowerShell usage for The Plot Thickens development on Windows 11._
