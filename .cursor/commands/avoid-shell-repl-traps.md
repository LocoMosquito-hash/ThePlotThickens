# Avoid Accidental REPL Sessions

Context: When running inline Python from PowerShell on Windows (e.g., via `run_terminal_cmd`), passing heredoc syntax such as `python <<'PY'` isn’t supported. PowerShell interprets that differently and launches the Python REPL, causing subsequent commands to be fed into the REPL instead of the shell.

## Guidelines
1. **Use PowerShell-friendly forms**  
   - Run inline snippets with `python -c "…"`.  
   - For multi-line scripts, drop them into a temporary `.py` file or use `python -c "…"`.

2. **One command per invocation**  
   - Don’t chain `cd …; python …` inside the same `run_terminal_cmd` unless necessary. The terminal retains the working directory, so a single `.venv\\Scripts\\python.exe …` call is enough.

3. **Detect REPL entry immediately**  
   - If a `>>>` prompt appears or the command hangs, assume we’re in the REPL. Send `exit()` right away before issuing other commands.

4. **Document when it happens**  
   - Note in the conversation that the REPL was opened accidentally, then confirm that we exited before running new commands.

Following these steps prevents the shell from getting “stuck” in Python and ensures scripted commands run deterministically.***

