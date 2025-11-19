# Flow Visualizer Configuration

## Purpose

Some VNs ship helper `.rpy` files (codex data, bundled engines, community add-ons)
that we never want to parse when building the narrative flow. The new
`flowviz_config.json` file lets each project describe those exceptions without
hard-coding them in the visualizer.

## Location

Place the config file next to the rest of the VN scripts:

```
<game root>\game\flowviz_config.json
```

## Format

- **JSON** (UTF‑8).
- All paths are **relative to the `game/` folder** unless an absolute path is
  provided.
- Trailing commas are **not allowed** (standard JSON).

## Schema (first setting)

```json
{
  "ignore_files": [
    "codexvariables.rpy",
    "SCENES/Chapter2/gameplay/c2aca_exp_auroraevent.rpy"
  ],
  "force_rpyc_files": ["day8.rpy"]
}
```

## Behavior

- `ignore_files`: temporarily removes the `.rpy` and `.rpyc` files before
  bootstrapping. The SDK never imports them and they do not appear in the flow
  graph.
- `force_rpyc_files`: temporarily hides only the `.rpy` so that Ren'Py loads the
  compiled `.rpyc` instead. Those files _do_ appear in the final flow graph, but
  their source code is never parsed, which avoids syntax traps in “protected”
  builds.
- The host process now retries the SDK worker in a **fresh Ren'Py interpreter**
  whenever a parse error bubbles up. Offending `.rpy` files are moved aside—only
  if their `.rpyc` counterparts exist—so the subsequent attempt loads the
  compiled bytecode without touching the source.
- If the compiled file is missing or the same error repeats, the retry loop
  stops immediately and the error message identifies the blocking script. We
  never ship a partial graph when Ren'Py refuses to load a module.
- All hidden files (ignored, forced, or auto-hidden) are restored immediately
  after analysis, even when the run fails.

## Notes

- Only `.rpy` scripts need to be listed for now.
- Paths are case-insensitive on Windows, but it is still best to match the
  exact casing.
- Future settings can be added to the same JSON object; unknown keys are ignored
  today.
