# Flow Visualizer POC - Quick Reference

## 🚨 **CRITICAL FIXES IMPLEMENTED - DO NOT BREAK**

### **1. Container-to-Choice Connection Fix**

**File**: `renpy_data_adapter.py` - `_create_hierarchy_connections()`

```python
# CRITICAL: Create connections FROM containers TO choices
for container in containers:
    related_choices = [c for c in choices if c.node_id.startswith(container.node_id)]
    for choice in related_choices:
        connection = VisualizationConnection(
            source=container.node_id,
            target=choice.node_id,
            connection_type='container_to_choice'
        )
```

**Why**: Fixes 489+ nodes on first level (graph connectivity explosion)

### **2. Recursive Directory Search Fix**

**File**: `app/renpy-source-api/control_flow/analyze_vn_menus.py`

```python
# OLD (BROKEN): game_dir.glob('*.rpy')
# NEW (WORKS):  game_dir.rglob('*.rpy')  # recursive!
```

**Why**: Many games store scripts in subdirectories (`game/chapters/chapter1/script/`)

### **3. Smart Orphan Detection**

**File**: `vn_flow_visualizer.py` - `_filter_false_orphans()`

- Menu choices with `in_degree == 0` are NOT orphans (they're glued to containers)
- Only true orphans should appear on first level

## 🏗️ **Node Type Rules**

| Node Type          | Incoming Edges         | Outgoing Edges     | Parent Rules                   |
| ------------------ | ---------------------- | ------------------ | ------------------------------ |
| **Visual Start**   | 0 (orphan)             | 1 (to entry point) | None                           |
| **Label**          | 0+                     | 0+                 | Can parent: labels, containers |
| **Menu Container** | 1 (from label)         | 0                  | Parents: choices only          |
| **Menu Choice**    | 0 (glued to container) | 0+                 | Can parent: labels, containers |

## 🧪 **Test Games**

- **Simple**: `T:/AG/LastCall-0.4-pc/game` (subdirectories, basic menus)
- **Complex**: `T:/AG/Savior-0.16c-pc/game` (nested menus, large scale)

## 📁 **Key Files**

- `FLOW_VISUALIZER_ARCHITECTURE.md` - **Complete documentation**
- `renpy_data_adapter.py` - Container-choice connections
- `analyze_vn_menus.py` - Menu detection (recursive search)
- `vn_flow_visualizer.py` - Layout & orphan detection

## 🚨 **Before Coding**

1. Read `FLOW_VISUALIZER_ARCHITECTURE.md`
2. Test with LastCall and Savior games
3. Verify menu containers still appear
4. Check first-level node count (should be < 10)

## ⚡ **Quick Debug**

```bash
cd ideas-lab/flow-visualizer-poc
python debug_menu_detection.py      # Test menu detection
python diagnose_savior_layout_issue.py  # Test connectivity
```
