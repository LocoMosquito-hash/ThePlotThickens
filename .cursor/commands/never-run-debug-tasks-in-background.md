# Never Run Debug Tasks in Background

**CRITICAL RULE:** Never run debugging, testing, or diagnostic tasks in the background. Always wait for output and analyze results before continuing.

## The Problem

When tasks run in the background:
- ❌ The model cannot see the output
- ❌ The model makes assumptions about success/failure
- ❌ The model continues without verifying results
- ❌ The model cuts the chat short prematurely
- ❌ The user must manually feed terminal output back

This breaks the debugging workflow and wastes time.

## Core Principle

**If you need to analyze the output, DO NOT run it in background.**

## Always Run Synchronously

### ✅ ALWAYS Foreground (Wait for Output)

Run these types of tasks synchronously:

- **Testing scripts** (`test_*.py`, `diagnose_*.py`, `verify_*.py`)
- **Diagnostic commands** (analyzing bugs, reproducing issues)
- **Parsers and validators** (checking if code parses correctly)
- **Data extraction** (extracting menu/screen/label content)
- **Debug output analysis** (any script with print statements you need to see)
- **Error reproduction** (running code to see if error occurs)
- **Verification after fixes** (confirming a fix worked)
- **Performance profiling** (timing and measuring)
- **Integration tests** (full pipeline runs)
- **Component tests** (isolated component testing)
- **Build commands** (compilation, bundling)
- **Quick checks** (any command taking < 30 seconds)

### ❌ NEVER Background for These

**DO NOT** set `is_background=true` for:

```python
# ❌ BAD - Testing in background
run_terminal_cmd(
    command="python test_menu_parsing.py",
    is_background=True  # WRONG!
)

# ✅ GOOD - Testing in foreground
run_terminal_cmd(
    command="python test_menu_parsing.py",
    is_background=False  # Wait for output
)
```

```python
# ❌ BAD - Diagnostics in background
run_terminal_cmd(
    command="python diagnose_issue.py",
    is_background=True  # Can't see results!
)

# ✅ GOOD - Diagnostics in foreground
run_terminal_cmd(
    command="python diagnose_issue.py",
    is_background=False  # Analyze output immediately
)
```

```python
# ❌ BAD - Running visualizer for testing in background
run_terminal_cmd(
    command="python run_visualizer.py --game 'T:\AG\SomeGame'",
    is_background=True  # Can't verify it worked!
)

# ✅ GOOD - Running visualizer in foreground
run_terminal_cmd(
    command="python run_visualizer.py --game 'T:\AG\SomeGame' 2>&1 | Select-String -Pattern 'ERROR|SUCCESS'",
    is_background=False  # See results immediately
)
```

## Only Background These

### ⚠️ Rarely Background (True Long-Running Processes)

Only use `is_background=true` for:

- **Development servers** (Flask, Django, web servers)
- **GUI applications** (PyQt apps that open windows)
- **Watch mode** (file watchers, auto-reload tools)
- **Daemon processes** (background services)
- **Truly long tasks** (> 5 minutes with no meaningful output)

**Even then, question if background is necessary.**

## The Workflow

### Correct Debugging Flow

```python
# 1. Run diagnostic (FOREGROUND)
result = run_terminal_cmd(
    command="python test_component.py",
    is_background=False  # ✅ Wait for output
)

# 2. ANALYZE the output that was returned
if "ERROR" in result:
    # Take corrective action based on actual output
    ...
elif "SUCCESS" in result:
    # Proceed to next step
    ...

# 3. Make decisions based on REAL output, not assumptions
```

### Incorrect Debugging Flow

```python
# ❌ WRONG - Run in background
result = run_terminal_cmd(
    command="python test_component.py",
    is_background=True  # Can't see output!
)

# ❌ Make assumptions without seeing output
# "The test probably passed, let's continue..."
# (It actually failed, but we'll never know)
```

## Filter Output If Too Verbose

If output is too long, filter it during the command:

```powershell
# ✅ GOOD - Filter but still foreground
python run_visualizer.py --game "T:\AG\Game" 2>&1 | Select-String -Pattern "ERROR|WARNING|SUCCESS"

# ✅ GOOD - Show only last 20 lines
python run_visualizer.py --game "T:\AG\Game" 2>&1 | Select-Object -Last 20

# ✅ GOOD - Show specific context
python test_menu.py 2>&1 | Select-String -Pattern "Menu|Choice|Destination" -Context 2
```

**Never sacrifice visibility for convenience.**

## Signs You're Doing It Wrong

### 🚨 Warning Signs

- You run a test and immediately say "the test passed" without seeing output
- You run a diagnostic and continue coding without analyzing results
- You assume success because no error was explicitly shown
- You ask the user to run the command and provide output
- You cut the chat short before verifying the fix worked

### ✅ Correct Behavior

- You run a test and WAIT for output
- You analyze the actual output before proceeding
- You grep/filter the output to find relevant information
- You make decisions based on what you SEE, not what you ASSUME
- You verify fixes work before declaring success

## Example Scenarios

### Scenario 1: Testing a Parser Fix

```python
# ❌ WRONG
run_terminal_cmd("python test_cmap_parser.py", is_background=True)
# "The parser is fixed! ✅" (assumed without seeing output)

# ✅ CORRECT
run_terminal_cmd("python test_cmap_parser.py", is_background=False)
# Wait for output...
# Read output: "❌ BUG: Parser failed on line 42"
# "I see the parser is still failing at line 42. Let me investigate..."
```

### Scenario 2: Verifying a Fix

```python
# ❌ WRONG
run_terminal_cmd("python verify_fix.py", is_background=True)
# "The fix is verified! Let's move on." (didn't see output)

# ✅ CORRECT
run_terminal_cmd("python verify_fix.py", is_background=False)
# Wait for output...
# Read output: "✅ SUCCESS: All tests passed"
# "Great! The fix is verified. All tests passed."
```

### Scenario 3: Reproducing a Bug

```python
# ❌ WRONG
run_terminal_cmd("python reproduce_bug.py", is_background=True)
# "I've started the reproduction script." (can't see if bug reproduced)

# ✅ CORRECT
run_terminal_cmd("python reproduce_bug.py", is_background=False)
# Wait for output...
# Read output: "❌ BUG CONFIRMED: Menu has 0 choices"
# "Bug confirmed! The menu has 0 choices. Here's what's happening..."
```

### Scenario 4: Running the Visualizer for Testing

```python
# ❌ WRONG
run_terminal_cmd("python run_visualizer.py --game path", is_background=True)
# "I've started the visualizer." (can't see if it loaded correctly)

# ✅ CORRECT
# Filter output to show relevant information
run_terminal_cmd(
    "python run_visualizer.py --game path 2>&1 | Select-String -Pattern 'ERROR|Parsed|nodes|menu'",
    is_background=False
)
# Wait for output...
# Read output: "Parsed 150 nodes, 45 menus"
# "Good! The game loaded successfully with 150 nodes and 45 menus."
```

## The Golden Rule

**If the output matters for your next action, NEVER run in background.**

## Exceptions

The ONLY valid reason to run in background:

```python
# Starting a GUI application that will open a window
run_terminal_cmd(
    "python run.py",  # Opens PyQt6 window
    is_background=True
)
# This is OK because:
# 1. The window needs to stay open
# 2. We're not analyzing terminal output
# 3. User will interact with the GUI directly
```

## Remember

- 🛑 **Stop** and think: "Do I need to see the output?"
- 👀 **If yes** → `is_background=False`
- ⏳ **Wait** for the command to complete
- 📊 **Analyze** the actual output
- ✅ **Decide** based on real data, not assumptions
- 🔄 **Continue** only after verifying results

---

**Bottom Line:** When debugging, testing, or diagnosing - ALWAYS foreground, ALWAYS wait, ALWAYS analyze output before continuing.

**Mantra:** "See first, decide second."

