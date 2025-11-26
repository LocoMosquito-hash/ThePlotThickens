## Python 2 Bundled Runtime Rollout – Current Status

### Context
- Goal: let the flow visualizer execute inside a VN’s bundled Ren’Py 7 (Python 2.7) runtime when `use_bundled_runtimes = true`, avoiding syntax errors from Py2-era `.rpyc` files.
- Approach so far:
  - `runtime_locator.py` now reports interpreter version + launcher so the host can decide when to use a Py2 worker.
  - `SDKFlowBuilder` dispatches to a new `sdk_flow_builder_worker_py2.py` when it detects a Python 2 runtime; otherwise it keeps the existing Py3 worker.

### What works
- **Detection & dispatch**: host correctly identifies the bundled runtime and attempts to run it first, only falling back to the Ren’Py 8.4 SDK when the Py2 worker fails.
- **Py2 bootstrap**: the prototype `sdk_flow_builder_worker_py2.py` can launch Ren’Py 7, hide `.rpy` sources in `process_rpyc_only` mode, and emit a JSON payload (proved via manual CLI runs).

### Current blockers
1. **Shared analyzer module requires `pathlib2`**  
   - I introduced `sdk_flow_analyzers.py` to share the Label/Screen analyzer logic between Py3 and Py2 workers.  
   - Packaged games do not ship `pathlib2`, so the module fails to import inside Python 2 (`ImportError: No module named pathlib2`), causing the entire bundled run to abort.
2. **Analyzer implementation still incomplete**  
   - The existing Py2 worker’s built-in analyzers are extremely minimal (no action metadata, no menu destinations, no screens).  
   - Even when the shared module loads under Py3, it still returns objects the JSON encoder can’t serialize (“Object of type type is not JSON serializable”) because we haven’t finished stripping type hints / Py3‑only constructs.
3. **Visual output regressions**  
   - In SurvivalGuide, the Py2 path yields only label nodes with empty menus and zero screen nodes, so the UI shows “orphan” labels even though the AST contains valid data.

### Files removed/stashed for now
- `app/renpy-source-api/sdk_flow_builder_worker_py2.py`
- `app/renpy-source-api/sdk_flow_analyzers.py`
- `app/renpy-source-api/sdk_flow_worker_shared.py`

### Next steps (when we pick this up again)
1. **Vendor lightweight shims** (`pathlib2`, `typing` no-ops) or embed a small fallback `Path` implementation so the shared module imports successfully in Py2 runtimes.
2. **Port the full analyzer logic**  
   - Copy the Py3 `LabelAnalyzer`/`ScreenAnalyzer` implementation, remove type hints/f‑strings, and ensure every structure we emit is JSON serializable in Python 2.  
   - Unit-test the analyzer directly (feeding AST fixtures from a Py2 runtime) before wiring it back into the worker.
3. **Re-enable the Py2 worker path** once the shared module is Py2-safe, then rerun the flow visualizer on SurvivalGuide (and another Ren’Py 7 title) to confirm screen nodes, menu destinations, and helper-label collapse all match the Py3 output.

Until those steps are complete, enabling `use_bundled_runtimes` will still fall back to the 8.4 SDK whenever the game bundles a Python 2 interpreter.

