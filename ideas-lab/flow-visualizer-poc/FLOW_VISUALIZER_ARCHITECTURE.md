# Flow Visualizer POC - Architecture & Design Rules

## 🎯 **CRITICAL REFERENCE DOCUMENT**

**This document contains the core architectural principles and rules for the Flow Visualizer POC.**  
**📖 READ THIS FIRST when working on any flow visualization components.**  
**🚨 Breaking these rules will cause major layout and connectivity issues.**

---

## 📋 **Table of Contents**

1. [Node Type Hierarchy](#node-types)
2. [Menu System Architecture](#menu-system)
3. [SDK Parsing Strategy](#sdk-parsing)
4. [Layout Principles](#layout-principles)
5. [Key Files & Responsibilities](#key-files)
6. [Common Pitfalls & Fixes](#pitfalls)
7. [Testing Guidelines](#testing)

---

## 🏗️ **Node Types & Hierarchy** {#node-types}

### **Visual Start Node**

- **Type**: `__VISUAL_START__`
- **Purpose**: Visual anchor point for the entire flow
- **Rules**:
  - ✅ Always orphaned by definition (no incoming edges)
  - ✅ Always positioned at the top level
  - ✅ Connects ONLY to the actual SDK-detected entry point
  - ✅ Green colored for visual distinction

### **Label Nodes**

- **Type**: Regular story labels (`start`, `ch1scene1`, etc.)
- **Purpose**: Represent story sections and narrative beats
- **Rules**:
  - ✅ Orphaned ONLY when `in_degree == 0` from other nodes
  - ✅ Can be parents to: other labels, menu containers (NOT directly to choices)
  - ✅ SDK-detected entry point gets special treatment
  - ✅ Positioned based on narrative hierarchy

### **Menu Containers**

- **Type**: `menu_container`
- **Purpose**: Visual grouping of menu choices
- **Rules**:
  - ✅ **EXACTLY ONE** incoming edge from parent label
  - ✅ **NO outgoing edges** (choices handle the flow)
  - ✅ **MUST contain** all choices for that menu
  - ✅ Yellow colored for visual distinction
  - ❌ **NEVER** appear as orphans

### **Menu Choices**

- **Type**: `choice`
- **Purpose**: Individual selectable options within a menu
- **Rules**:
  - ✅ **NO incoming edges** (parent is the container, not an edge)
  - ✅ **ALWAYS "glued"** to their menu container
  - ✅ **NEVER presented alone** - always with container
  - ✅ Can have children: labels, nested menu containers
  - ❌ **NEVER** treated as orphans (even if `in_degree == 0`)

---

## 🎛️ **Menu System Architecture** {#menu-system}

### **Critical Container-to-Choice Connection Fix**

```python
# ESSENTIAL: Create connections FROM containers TO choices
def _create_hierarchy_connections(self, flow_graph, container_nodes, choice_connections):
    # Phase 1: Container-to-choice connections (CRITICAL FIX)
    containers = [n for n in container_nodes if n.node_type == 'menu_container']
    choices = [n for n in container_nodes if n.node_type == 'choice']

    for container in containers:
        related_choices = [c for c in choices if c.node_id.startswith(container.node_id)]
        for choice in related_choices:
            # CREATE THE MISSING CONNECTION
            connection = VisualizationConnection(
                source=container.node_id,
                target=choice.node_id,
                connection_type='container_to_choice'
            )
```

### **Menu Hierarchy Rules**

- **Top-level menus**: Direct children of labels
- **Nested menus**: Children of choice nodes
- **Container naming**: `{label_name}_menu_{index}`
- **Choice naming**: `{container_id}_choice_{index}`

### **Nested Menu Architecture**

This section formalizes how nested menus are modeled and rendered.

- **Definition**: A nested menu occurs when the block of a choice contains a `menu`. Nesting depth is theoretically unbounded in Ren'Py; we do not impose a depth limit.
- **Authoritative hierarchy**:
  - `menu_container` → parents only `choice_button` nodes (visual containment; no visible edges)
  - `choice_button` → may parent a `menu_container` (nested menu) and/or connect to labels
  - A nested menu is simply another `menu_container` node whose parent is a `choice_button`
- **Visual rules**:
  - Menu containers have **no visible outgoing edges** to their choices; choices are visually contained (“glued”) inside
  - When a choice contains a nested menu, we draw a **visible edge** from the `choice_button` to the nested `menu_container`
  - Choices continue to handle narrative flow from there (to labels and deeper menus)
- **Edge visibility policy**:
  - Container → Choice: internal layout aid only (invisible, `visual_containment=True`, `line_style='none'`)
  - Choice → Nested menu container: visible
  - Choice → Label (or other destination): visible
- **Layout (dot-like only)**:
  - Place nested menu containers on a deeper tier than their parent choice, slightly offset to avoid overlaps
  - Preserve strict parent-before-child ordering where possible; nested menus must never appear at the top tier
- **Example (Haley’s Story, `ep2cont5`)**:
  - Label `ep2cont5` → Menu container `ep2cont5_menu_1`
  - Choice "Kiss her[…]": edge to nested menu container `ep2cont5_nested_menu_1`
  - Nested container holds its own choices, which then connect to destinations (e.g., `ep2cont6`)

Note: Current behavior in some views may still show nested menus as direct children of the label. The **target design** is strictly: `label → menu_container → choice_button → menu_container → …` with edges from choices to their nested menus.

### **Flow Filtering Rules**

```python
# Skip menu choice flows - they're handled by containers
if flow.context == "menu_choice":
    print(f"[FLOW FILTER] Skipping menu_choice flow: {source} → {target}")
    continue
```

---

## 🔍 **SDK Parsing Strategy** {#sdk-parsing}

### **Why SDK-Based Parsing**

> **"Developers can get very creative when it comes to taking advantage of Renpy's flexibility"**

- **Accuracy**: SDK sees exactly what Renpy sees
- **Completeness**: Handles complex nested structures
- **Future-proof**: Works with any Renpy version

### **Recursive Directory Search Fix**

```python
# CRITICAL FIX: Search recursively for .rpy files
# OLD (BROKEN): game_dir.glob('*.rpy')
# NEW (WORKS):  game_dir.rglob('*.rpy')  # recursive!

# WHY: Many games organize scripts in subdirectories:
# T:/AG/LastCall-0.4-pc/game/chapters/chapter1/script/ch1s22mckellycar.rpy
```

### **Hybrid Parser Approach**

- **HybridRenpyParser**: Wraps RenpyParser for compatibility
- **MenuAnalyzer**: Handles complex menu detection
- **SDK Integration**: Authoritative entry point detection

---

## 📐 **Layout Principles** {#layout-principles}

### **Hierarchical Narrative Flow**

- **Top Level**: Start node + orphan labels
- **Subsequent Levels**: Positioned based on narrative progression
- **Algorithm**: Dot-like layout with SCC-aware hierarchy
- **High-Connectivity Clusters**: When a layer contains a highly interconnected set of nodes (e.g., a large SCC or dense decision cluster), the dot-like layout may temporarily arrange that subset in a compact circular/clustered formation to reduce overlap and improve readability. Once outside the cluster, standard dot-like tiering resumes.

### **Visual Hierarchy Rules**

1. **Start node at top** (always)
2. **Orphan labels** join top level (when truly orphaned)
3. **Menu containers** positioned near parent labels
4. **Choices** visually grouped within containers
5. **Nested structures** maintain parent-child relationships

### **Edge Coloring & Styling**

- **Yellow edges**: Menu flow
- **Red edges**: Story flow
- **Container edges**: Internal menu structure

---

## 📁 **Key Files & Responsibilities** {#key-files}

### **Core Architecture**

```
renpy_data_adapter.py
├── analyze_project()           # Main entry point
├── _create_menu_containers()   # Menu system creation
├── _create_hierarchy_connections()  # CRITICAL: Container-choice links
└── _convert_flows_to_connections()  # Flow filtering logic
```

### **Menu Detection**

```
control_flow/analyze_vn_menus.py
├── MenuAnalyzer.analyze_vn_menus()  # Project-wide menu detection
├── _analyze_file_menus()           # Per-file analysis
└── rglob() usage                   # CRITICAL: Recursive search
```

### **Flow Graph Building**

```
parser.py
├── build_flow_graph()              # Main graph construction
├── find_rpy_files()               # Recursive file discovery
└── MenuAnalyzer integration        # Menu structure creation
```

### **Visualization Engine**

```
vn_flow_visualizer.py
├── _find_start_nodes()            # Smart orphan detection
├── _filter_false_orphans()        # Prevents layout explosion
└── dot_like layout                # Hierarchical positioning
```

---

## ⚠️ **Common Pitfalls & Fixes** {#pitfalls}

### **1. The Graph Connectivity Explosion**

**Problem**: Menu choices appear as orphans → 489+ nodes on first level  
**Root Cause**: Missing container-to-choice connections  
**Solution**: `_create_hierarchy_connections()` fix  
**Files**: `renpy_data_adapter.py`

### **2. Missing Menu Detection**

**Problem**: Zero menus detected in games with obvious menus  
**Root Cause**: Non-recursive directory search  
**Solution**: `glob('*.rpy')` → `rglob('*.rpy')`  
**Files**: `analyze_vn_menus.py`

### **3. False Orphan Detection**

**Problem**: Connected nodes treated as start nodes  
**Root Cause**: Naive `in_degree == 0` check  
**Solution**: `_filter_false_orphans()` intelligent filtering  
**Files**: `vn_flow_visualizer.py`

### **4. Menu Choice Isolation**

**Problem**: Choice buttons disconnected from containers  
**Root Cause**: Flow filtering removes menu choice connections  
**Solution**: Explicit container-to-choice connection creation  
**Files**: `renpy_data_adapter.py`

---

## 🧪 **Testing Guidelines** {#testing}

### **Test Games**

- **Simple**: `T:/AG/LastCall-0.4-pc/game` (basic menus, subdirectories)
- **Complex**: `T:/AG/Savior-0.16c-pc/game` (nested menus, large scale)
- **Challenging**: `F:/Bin/Games/SL-1.0-ExtraScenesEdition(PC)/game` (advanced structures)

### **Validation Checklist**

- [ ] Menu containers appear (not zero)
- [ ] Choices are grouped within containers
- [ ] No massive first-level row (check < 10 start nodes)
- [ ] Hierarchical flow preserved
- [ ] SDK entry point detected correctly

### **Debug Scripts**

```bash
# Menu detection testing
python debug_menu_detection.py

# Graph connectivity analysis
python diagnose_savior_layout_issue.py

# File search verification
python debug_file_search.py
```

---

## 🔗 **Architecture Dependencies**

### **Critical Integration Points**

```
SDK Detection → Menu Analysis → Graph Building → Layout → Visualization
      ↓              ↓             ↓           ↓          ↓
Entry point    Menu containers  Flow graph  Hierarchy  Final render
detection      & choices        creation    assignment
```

### **Data Flow**

```
Raw .rpy files → MenuAnalyzer → MenuStructures → VisualizationNodes → Layout
                              ↘                ↗
                               Flow connections
```

---

## 📝 **Version History**

### **Major Fixes Applied**

1. **Container-Choice Connection Fix** - Solved graph connectivity explosion
2. **Recursive Directory Search** - Fixed missing menu detection
3. **Smart Orphan Detection** - Prevented false start node identification
4. **Flow Filtering Enhancement** - Proper menu choice handling

### **Architecture Evolution**

- Started with regex-only parsing
- Added SDK integration for accuracy
- Implemented hierarchical menu support
- Enhanced layout algorithms for complex games

---

## 🚨 **CRITICAL REMINDERS**

### **When Adding New Features**

1. **Read this document first**
2. **Test with all reference games**
3. **Verify menu containers still work**
4. **Check that orphan detection is correct**
5. **Ensure SDK parsing compatibility**

### **When Debugging Issues**

1. **Check if nodes are properly connected**
2. **Verify menu detection is working**
3. **Test with both simple and complex games**
4. **Use the provided debug scripts**

---

## 📞 **Contact & References**

**Key Architectural Decisions Made**: December 2024  
**Primary Test Games**: LastCall, Savior, SL-ExtraScenes  
**Core Principle**: _"SDK accuracy with hierarchical visual clarity"_

**For questions about this architecture, refer to:**

- Flow visualization test results
- Menu detection debug output
- Graph connectivity analysis
- Layout algorithm behavior

---

_This document should be updated whenever core architectural decisions are made._
