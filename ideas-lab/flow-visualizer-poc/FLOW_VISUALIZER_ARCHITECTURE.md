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
  - ✅ Can have children: labels, nested menu containers, **nested labels**
  - ❌ **NEVER** treated as orphans (even if `in_degree == 0`)

### **Nested Labels**

- **Type**: `nested_label`
- **Purpose**: Labels defined within menu choice blocks
- **Rules**:
  - ✅ **EXACTLY ONE incoming edge** from parent choice
  - ✅ **Visually distinct** with `↳` prefix and light cyan color
  - ✅ **Purple connections** from choice to nested label
  - ✅ **Semantic ownership** by specific choice (not parent label)
  - ❌ **NEVER** appear as regular labels in flow graph

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

This section formalizes how nested menus are modeled and rendered using the **Authoritative Hierarchy System**.

- **Definition**: A nested menu occurs when the block of a choice contains a `menu`. Nesting depth is theoretically unbounded in Ren'Py; we do not impose a depth limit.

- **Authoritative Hierarchy Implementation**:

  - Uses `MenuStructure.nested_menu_structures` and `MenuChoice.nested_menu_structures` for semantic relationships
  - `HierarchyNode` with `node_type='menu_container'` → parents only `choice` nodes (visual containment)
  - `HierarchyNode` with `node_type='choice'` → may parent nested `menu_container` nodes and/or connect to labels
  - Nested menus use **content-based IDs** (e.g., `a1b2c3d4e5f6`) instead of fragile string patterns
  - Direct parent/child object references eliminate string parsing: `choice_node.children` contains nested containers

- **Visual rules**:

  - Menu containers have **no visible outgoing edges** to their choices; choices are visually contained ("glued") inside
  - When a choice contains a nested menu, we draw a **visible edge** from the `choice` to the nested `menu_container`
  - Choices continue to handle narrative flow from there (to labels and deeper menus)

- **Edge visibility policy**:

  - Container → Choice: internal layout aid only (invisible, `visual_containment=True`, `line_style='none'`)
  - Choice → Nested menu container: **visible** (shows narrative hierarchy)
  - Choice → Label (or other destination): **visible** (shows narrative flow)

- **Content-Based Node Creation**:

  ```python
  # Nested container ID generation using content hashing
  content_hash = self._generate_content_hash({
      'type': 'nested_menu_container',
      'parent_choice': parent_choice.content_hash,
      'nested_index': nested_idx,
      'prompt': getattr(nested_menu, 'prompt', ''),
      'choices': [choice.text for choice in nested_menu.choices]
  })

  # Semantic ID for human readability
  semantic_id = f"{parent_choice.semantic_id}_nested_{prompt_suffix}#{content_hash[:8]}"
  ```

- **Layout (dot-like only)**:

  - Place nested menu containers on a deeper tier than their parent choice
  - Use `hierarchy.find_children_by_type('menu_container')` for positioning
  - Preserve strict parent-before-child ordering using object relationships
  - **No orphan detection needed** - hierarchy provides authoritative parent information

- **Example (Haley's Story, `ep2cont5`) - Before vs After**:

  **OLD (String-based, created rogue nodes)**:

  ```
  ep2cont5 → ep2cont5_menu_0 → choices
  ep2cont5_menu_0_choice_0 → ep2cont5_nested_menu_1 (ROGUE!)
  ep2cont5_nested_menu_1 → ep2cont5_nested_menu_1_choice_1 (ROGUE!)
  ```

  **NEW (Authoritative hierarchy)**:

  ```
  HierarchyNode(label) → HierarchyNode(menu_container) → HierarchyNode(choice) → HierarchyNode(nested_menu_container)
  Direct object relationships: choice_node.children[0] = nested_container_node
  Content IDs: a1b2c3d4 → f6e5d4c3 → 9x8y7z6w → 3m2n1o0p
  ```

**🔑 Key Improvement**: The authoritative hierarchy **eliminates rogue nodes** by using semantic relationships from `MenuStructure` instead of reconstructing hierarchy from string patterns. Nested menus are detected via `choice.nested_menu_structures` and created with stable content-based IDs.

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
- **MenuAnalyzer**: Handles complex menu detection with improved nested menu preservation
- **SDK Integration**: Authoritative entry point detection

#### **Recent Improvements (August 2025)**

✅ **Enhanced Nested Menu Parsing**: The parser now correctly preserves `nested_menu_structures` data when converting from MenuStructure to MenuNode, ensuring nested menus maintain their hierarchical relationships instead of being flattened into separate top-level menus.

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
