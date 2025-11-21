# Issue: Hidden `_call_*` Helper Labels Break Downstream Flows

**Status**: 🟠 Open  
**Priority**: Medium  
**Reported**: November 2025  
**Source**: Isabella C03.3 (`game/scripts/c1/c01.rpy`)

---

## Summary

When the SDK parses Ren’Py’s auto-generated helper labels (e.g., `_call_saveend`) they appear in the flow graph exactly as expected, carrying the implicit fallthrough from a label that issued `call ... from _call_helper` to the next real label. However, our visualization/AHS layers hide every label whose name starts with `_call_` to reduce noise. That filter drops the only edge leading into the “real” follow-up label, so the follow-up is rendered as an orphan even though the raw graph is connected.

**Observed example**

- Game: `T:\AG\Isabella-C03.3-pc`
- Script: `game/scripts/c1/c01.rpy`
- Label `c01bo` calls `saveend (...) from _call_saveend` and then flows into label `c01end`.
- SDK graph edges:
  - `c01bo → (call) saveend`
  - `c01bo → (fallthrough) _call_saveend`
  - `_call_saveend → (fallthrough) c01end`
- UI graph: `_call_saveend` is hidden, so `c01end` loses its incoming edge and displays as an orphan even though the runtime fallthrough is intact.

## Impact

- False orphan detection for any label that is only reached through a `_call_*` helper.
- Missing flow edges in the visualizer when developers intentionally use `call ... from` patterns.
- Debug time wasted because the SDK output looks correct (e.g., `temp_label84.json` shows the edge), but the rendered graph does not.

## Root Cause

1. Ren’Py emits helper labels (named `_call_<labelname>`) to wrap any code after a `call ... from` statement.
2. The SDK worker faithfully emits these helpers plus the fallthrough edges.
3. The visualization/AHS code suppresses helper labels by name prefix to avoid clutter, without re-wiring their edges.

## Proposed Direction

1. Either keep `_call_*` labels visible (perhaps with a lighter styling) or
2. Collapse helper nodes during ingestion: if a hidden `_call_*` node only has one outgoing fallthrough, redirect its parents directly to that destination before filtering.

Until we do one of these, legitimate fallthroughs will continue to disappear whenever the Ren’Py runtime injects helper labels.


