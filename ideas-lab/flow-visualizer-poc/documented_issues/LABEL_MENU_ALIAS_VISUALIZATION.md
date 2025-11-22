# Label Menu Aliases Rendered as Duplicate Label+Menu Nodes

**Status**: ⚠️ **Deferred (user is temporarily living with it)**  
**Priority**: Medium – required for accurate menu topology  
**Investigation Window**: November 2025  
**Source Project**: `T:\AG\BecomeARockStar-0.90-pc\game\script.rpy` (`label sms01`, `menu selina_sms01`, `menu selina_sms01a`)  

---

## Executive Summary

Certain Ren’Py “label menus” (labels immediately followed by `menu` on the same line) are surfaced twice in the visualization pipeline: once as a standalone `LabelNode` and once as the `MenuNode` they alias. The helper label then incorrectly parents unrelated downstream statements, creating misleading graphs. The user confirmed they want these constructs rendered as **a single menu node** that inherits all incoming edges; the alias label may exist as metadata for debugging but must never appear in the visual hierarchy. Work on the fix was started (alias tagging, adapter filtering) but was stashed at the user’s request. This document captures the requirements, partial solutions, and remaining gaps so the effort can be resumed without re-discovery.

---

## What Is a Label Menu?

```renpy
label sms01:
    "Incoming SMS!"
    menu selina_sms01:   # label+menu share line/file metadata
        "Read it now":
            jump after_repetition01
        "Later":
            return
```

Key characteristics:
1. `label X:` is immediately followed by `menu X:` (often on the same logical line in AST terms).
2. The label block is otherwise empty; execution flows directly into the menu container.
3. Other parts of the script `jump`/`call` `X`, expecting the menu to run.

---

## Observed vs Expected Behavior

| Aspect | Current Output (bug) | Desired Output |
| --- | --- | --- |
| Node roster | Both `label selina_sms01` **and** `menu selina_sms01` render | Only the `MenuNode` renders |
| Incoming edges | Other labels connect to the helper label | Edges terminate on the `MenuNode` |
| Downstream edges | Helper label continues following its `next` pointer, stealing unrelated targets | Only menu choices own children; helper label is hidden |
| Metadata | No record that the label is an alias | Menu keeps `alias_labels=[...]` for inspector/debug view |

This mismatch makes flows (e.g., `sms01 → selina_sms01 → after_repetition01`) look nonsensical because the helper label appears to parent siblings outside its scope.

---

## Detection Heuristics (Confirmed Safe)

To classify a label as a menu alias:

1. `Label` AST node has an empty block (no statements).
2. `label.next` points to a `Menu` node.
3. Label and menu share the same filename & line number.

The user verified there are no known mixed cases where a label menu also contains additional statements; if such cases appear later, we should keep the label as a real node.

---

## Pipeline Insights

### SDK Worker (`sdk_flow_builder_worker.py`)
- Needs a deterministic registry (`MENU_AST_NODE_REGISTRY`) keyed by AST identities so the worker can tag label payloads with `is_menu_alias=True` and `alias_menu_id=<menu_id>`.
- Alias detection must occur *after* menus are recorded to avoid missing IDs.
- `build_payload()` should clear the registry at the start (not the end) to avoid cross-run contamination.

### Flow Graph Builder (`sdk_flow_builder.py`)
- During `_construct_flow_graph`, filter alias labels out of the main label list, build `menu_id → alias_labels`, and attach aliases to `MenuNode.alias_labels`.
- Keep alias labels in the raw JSON for inspector tooling, but never emit them as graph-level nodes.

### Authoritative Hierarchy (`authoritative_hierarchy.py`)
- Must skip any Hierarchy label entry flagged as `is_menu_alias`.
- `get_node_by_label_name()` should resolve alias lookups to the owning menu so edges stay valid.
- When creating connections, re-target any source/target references that mentioned the helper label to the canonical menu container.

### Visual Adapter (`renpy_data_adapter.py`)
- Honor `include_helper_labels` but treat `is_menu_alias` as a stronger filter: even when helper labels are shown, alias labels should remain hidden.
- Connections (`LabelFlow`, screen actions, etc.) must be rewired so the menu node receives all incoming edges without duplicating them.

---

## Debugging Notes

- Inspector export `@temp_label84.json` confirmed the SDK already emits both the alias label and the menu with identical coordinates.
- When caches were cleared and the rebuilt pipeline ran, `sms01` correctly showed `alias_menu_id='selina_sms01'`, but the visualization still rendered both nodes because downstream filtering was incomplete.
- The user stashed these code paths after verifying no visual change, so current `main` is still missing alias handling.

---

## Outstanding Work

1. **Reapply Alias Metadata**: Restore the worker/builder changes so alias payloads are available again.
2. **Hide Alias Nodes**: Update the adapter & hierarchy to drop alias labels while preserving their metadata on the menu node.
3. **Edge Re-targeting**: Ensure jumps/calls to the alias are re-bound to the menu node before visualization.
4. **Regression Pass**: Test on `Become a Rockstar`, `Letter to my Dream`, and `ARTEMIS` to confirm no helper labels disappear incorrectly.
5. **Documentation & Logging**: Surface counts of alias labels detected in `analysis_metadata` to aid future debugging.

---

## Testing Strategy (Pending Implementation)

- **Unit**: Add fixtures in `sdk_flow_builder_worker_tests` covering label+menu same-line constructs and verifying `is_menu_alias`.
- **Integration**: Extend `ideas-lab/flow-visualizer-poc/tests` with a miniature VN containing multiple alias menus; verify node roster & connection targets.
- **Inspector**: Provide a toggle to list alias labels per menu for quick sanity checks.

---

## Decision Log

- ✅ Treat label menus as single menu nodes; helper labels suppressed visually.
- ✅ Alias metadata remains accessible for debugging but not rendered.
- ✅ Detection requires empty block + same line/file + `next` menu pointer.
- ⚠️ Implementation is paused at the user’s request and must be explicitly re-enabled before further work.

---

_Documented under `@documented_issues` so future contributors can resume the label-menu alias effort without re-discovery._


