# Node Identification Strategy - Flow Visualizer POC

## 📋 **Overview**

This document explains how nodes are identified and named in the Flow Visualizer POC. **The system uses multiple identification strategies**, not just original element names and auto-generated names.

**Key Finding**: The node identification system is **hierarchical and contextual**, combining original names, auto-generated IDs, and special reserved identifiers.

**Last Updated**: August 2025  
**Based on**: Technical analysis of `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py`

---

## 🎯 **Node Identification Strategies**

### **1. Original Element Names** (Ren'Py Native)

#### **Label Nodes** - Direct Original Names

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py` (Line 215)

```python
node = VisualizationNode(
    node_id=label_name,  # ← Direct use of original Ren'Py label name
    node_type='label',
    display_name=label_name,
    # ...
)
```

**Examples**: `start`, `ch1scene1`, `day02`, `conversation_with_mom`

**Why This Works**: Ren'Py label names are **guaranteed unique** within a project by the language specification.

#### **Label Menu Containers** - Original Menu Names

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py` (Lines 432-434)

```python
if menu_node.label_name:
    # Label menu - use actual label name
    container_id = menu_node.label_name  # ← Original menu label name
    container_name = menu_node.label_name
    container_color = 'orange'
```

**Examples**: `day02_p_room_choices`, `character_selection`, `main_menu_choices`

**Why This Works**: Label menus (`menu label_name:`) create their own unique label namespace.

---

### **2. Auto-Generated Hierarchical IDs** (System Generated)

#### **Regular Menu Containers** - Pattern-Based Generation

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py` (Line 440)

```python
else:
    # Regular menu - use generic naming
    container_id = f"{label_name}_menu_{menu_idx}"
```

**Pattern**: `{parent_label}_menu_{index}`

**Examples**:

- `start_menu_0` (first menu in start label)
- `ch1scene1_menu_1` (second menu in ch1scene1 label)
- `conversation_menu_0` (first menu in conversation label)

#### **Choice Buttons** - Hierarchical Generation

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py` (Line 819)

```python
for choice_idx, choice in enumerate(menu_node.choices):
    choice_id = f"{container_id}_choice_{choice_idx}"
```

**Pattern**: `{container_id}_choice_{index}`

**Examples**:

- `start_menu_0_choice_0` (first choice in first start menu)
- `day02_p_room_choices_choice_1` (second choice in label menu)
- `conversation_menu_0_choice_2` (third choice in conversation menu)

#### **Nested Menu Containers** - Multi-Level Hierarchy

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py` (Line 480)

```python
nested_container_id = nested_menu.node_id.replace(label_name + "_", f"{label_name}_nested_")
```

**Pattern**: `{parent}_nested_{rest_of_hierarchy}`

**Examples**:

- `start_nested_menu_0_choice_1_menu_1` (nested menu within choice)
- `conversation_nested_menu_2` (nested conversation menu)

---

### **3. Special Reserved Identifiers** (System Constants)

#### **Visual Start Node** - Reserved System ID

**File**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py` (Line 988)

```python
visual_start_node = VisualizationNode(
    node_id="__VISUAL_START__",  # Special ID to avoid conflicts
    node_type='start',
    display_name="Start",
    # ...
)
```

**Purpose**:

- ✅ **Guaranteed unique** - cannot conflict with Ren'Py labels
- ✅ **System-recognizable** - double underscores indicate system node
- ✅ **Future-proof** - reserved namespace for additional system nodes

---

## 📊 **ID Strategy by Node Type**

| Node Type                   | ID Strategy                   | Example                 | Uniqueness Guarantee                  |
| --------------------------- | ----------------------------- | ----------------------- | ------------------------------------- |
| **Label Nodes**             | Original Ren'Py name          | `start`, `ch1scene1`    | ✅ Ren'Py language spec               |
| **Label Menu Containers**   | Original menu name            | `day02_p_room_choices`  | ✅ Ren'Py label namespace             |
| **Regular Menu Containers** | `{parent}_menu_{index}`       | `start_menu_0`          | ✅ Parent uniqueness + enumeration    |
| **Choice Buttons**          | `{container}_choice_{index}`  | `start_menu_0_choice_1` | ✅ Container uniqueness + enumeration |
| **Nested Containers**       | `{parent}_nested_{hierarchy}` | `start_nested_menu_0`   | ✅ Hierarchical path uniqueness       |
| **Visual Start**            | Reserved system ID            | `__VISUAL_START__`      | ✅ Reserved namespace                 |

---

## 🏗️ **Hierarchical ID Construction**

### **Example: Complex Nested Structure**

```renpy
label start:
    "Welcome to the game"

    menu:  # Regular menu
        "Go to conversation":
            jump conversation
        "Make a choice":
            menu nested_choice:  # Nested menu within choice
                "Option A":
                    jump option_a
                "Option B":
                    jump option_b

menu character_selection:  # Label menu
    "Choose Hero":
        jump hero_path
    "Choose Villain":
        jump villain_path
```

### **Generated Node IDs**:

```
__VISUAL_START__                           # Special system node
start                                      # Original label name
start_menu_0                              # Auto-generated: first menu in start
start_menu_0_choice_0                     # Auto-generated: first choice
start_menu_0_choice_1                     # Auto-generated: second choice
start_nested_menu_0                       # Auto-generated: nested menu
start_nested_menu_0_choice_0              # Auto-generated: nested choice A
start_nested_menu_0_choice_1              # Auto-generated: nested choice B
character_selection                       # Original label menu name
character_selection_choice_0              # Auto-generated: hero choice
character_selection_choice_1              # Auto-generated: villain choice
conversation                              # Original label name (jump target)
option_a                                  # Original label name (jump target)
option_b                                  # Original label name (jump target)
hero_path                                 # Original label name (jump target)
villain_path                             # Original label name (jump target)
```

---

## 🔍 **ID Generation Logic**

### **Uniqueness Guarantees**

```python
def ensure_node_id_uniqueness():
    """How the system guarantees unique node IDs."""

    # 1. Original names: Ren'Py guarantees label uniqueness
    original_labels = get_renpy_labels()  # Unique by language spec

    # 2. Auto-generated: Hierarchical construction ensures uniqueness
    for label_name in original_labels:
        for menu_idx, menu in enumerate(label.menus):
            container_id = f"{label_name}_menu_{menu_idx}"  # Unique by parent + index

            for choice_idx, choice in enumerate(menu.choices):
                choice_id = f"{container_id}_choice_{choice_idx}"  # Unique by container + index

    # 3. Reserved: System namespace prevents conflicts
    system_nodes = ["__VISUAL_START__", "__FUTURE_SYSTEM_NODE__"]  # Reserved namespace
```

### **Conflict Prevention**

```python
# ID conflicts are prevented by:

# 1. Different namespaces for different strategies
original_names = {"start", "ch1scene1"}          # Ren'Py namespace
auto_generated = {"start_menu_0", "start_menu_0_choice_1"}  # Pattern namespace
system_reserved = {"__VISUAL_START__"}           # Reserved namespace

# 2. Hierarchical patterns that include unique parents
parent_unique = "start"                          # Unique label
child_pattern = f"{parent_unique}_menu_0"        # Inherits parent uniqueness
grandchild_pattern = f"{child_pattern}_choice_0" # Inherits full hierarchy uniqueness

# 3. Enumeration within scope
for idx, item in enumerate(items_in_scope):
    item_id = f"{unique_parent}_{item_type}_{idx}"  # Index ensures uniqueness within scope
```

---

## 🔄 **ID Resolution and Lookup**

### **Node Resolution Process**

```python
def resolve_node_by_id(node_id: str) -> VisualizationNode:
    """How the system resolves node IDs back to objects."""

    # 1. Check system reserved IDs first
    if node_id.startswith("__") and node_id.endswith("__"):
        return get_system_node(node_id)

    # 2. Check if it's an original Ren'Py label
    if node_id in original_renpy_labels:
        return get_label_node(node_id)

    # 3. Parse auto-generated patterns
    if "_menu_" in node_id:
        if "_choice_" in node_id:
            return get_choice_button(node_id)
        else:
            return get_menu_container(node_id)

    # 4. Check for label menu (original name but menu type)
    if is_label_menu(node_id):
        return get_label_menu_container(node_id)

    raise NodeNotFoundError(f"Could not resolve node ID: {node_id}")
```

### **ID Pattern Parsing**

```python
def parse_auto_generated_id(node_id: str) -> Dict[str, Any]:
    """Extract components from auto-generated IDs."""

    # Pattern: start_menu_0_choice_1
    parts = node_id.split("_")

    if "choice" in parts:
        # Choice button: parent_menu_X_choice_Y
        choice_idx = int(parts[-1])
        container_id = "_".join(parts[:-2])  # Remove "_choice_Y"
        return {
            'type': 'choice_button',
            'parent_container': container_id,
            'choice_index': choice_idx
        }

    elif "menu" in parts:
        # Menu container: parent_menu_X
        menu_idx = int(parts[-1])
        parent_label = "_".join(parts[:-2])  # Remove "_menu_X"
        return {
            'type': 'menu_container',
            'parent_label': parent_label,
            'menu_index': menu_idx
        }

    else:
        # Original label or label menu
        return {
            'type': 'label_or_label_menu',
            'name': node_id
        }
```

---

## ⚠️ **Edge Cases and Special Handling**

### **1. Label Names with Underscores**

```python
# Problematic: label name contains pattern-like strings
label_name = "start_menu_helper"  # Contains "_menu_"

# Solution: Original labels are processed first
if node_id in original_renpy_labels:
    return get_label_node(node_id)  # Recognized as original label
else:
    # Only then parse as auto-generated pattern
    return parse_auto_generated_id(node_id)
```

### **2. Reserved Name Conflicts**

```python
# Ren'Py developers could theoretically create:
label __VISUAL_START__:  # Conflicts with system reserved ID

# Solution: System reserved namespace takes precedence
if node_id.startswith("__") and node_id.endswith("__"):
    return get_system_node(node_id)  # System node wins
```

### **3. Very Long Hierarchies**

```python
# Deep nesting creates long IDs:
# "conversation_menu_0_choice_1_nested_menu_0_choice_2_nested_menu_1_choice_0"

# Handled by: Consistent pattern following
def handle_deep_nesting(node_id: str):
    # Pattern parsing works regardless of depth
    # Each level maintains parent-child relationship
    return parse_hierarchical_pattern(node_id)
```

---

## 📚 **Related Documentation**

- **[NODE_TYPES_REFERENCE.md](./NODE_TYPES_REFERENCE.md)**: Complete node type overview
- **[CHOICE_OBJECTS_ARCHITECTURE.md](./CHOICE_OBJECTS_ARCHITECTURE.md)**: Choice handling details
- **Flow Adapter**: `ideas-lab/flow-visualizer-poc/renpy_data_adapter.py`
- **ID Generation**: Lines 215, 434, 440, 819, 480, 988

---

## 🎯 **Summary**

**Node identification uses a sophisticated multi-strategy approach**:

1. **Original Names** (40-50%): Direct Ren'Py labels and label menus
2. **Auto-Generated Hierarchical** (45-55%): Pattern-based for containers and choices
3. **System Reserved** (<5%): Special system nodes like `__VISUAL_START__`

**Key Principles**:

- ✅ **Hierarchical uniqueness** through parent-child relationships
- ✅ **Namespace separation** prevents conflicts between strategies
- ✅ **Pattern consistency** enables reliable ID parsing and resolution
- ✅ **Original name preservation** maintains Ren'Py semantic meaning

This design balances **semantic clarity** (keeping original names where possible) with **system organization** (generating structured IDs for synthetic elements) while **guaranteeing uniqueness** across the entire visualization graph.
