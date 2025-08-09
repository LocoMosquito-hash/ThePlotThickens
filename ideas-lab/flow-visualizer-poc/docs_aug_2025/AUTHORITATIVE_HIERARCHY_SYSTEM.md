# Authoritative Hierarchy System Documentation

## 🎯 **Executive Summary**

The **Authoritative Hierarchy System** is a comprehensive solution to eliminate the fragile string-based node relationship detection that plagued the flow visualizer. This system replaces pattern-matching with semantic object relationships and content-based stable node identification.

**Key Innovation**: Instead of reconstructing parent-child relationships from auto-generated string IDs, the system uses direct object references from the original `MenuStructure` semantic data.

---

## 📋 **Table of Contents**

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Content-Based Node IDs](#content-based-node-ids)
4. [Integration Status](#integration-status)
5. [Usage Guide](#usage-guide)
6. [Troubleshooting](#troubleshooting)

---

## 🏗️ **System Overview** {#system-overview}

### **Problem Solved**

**Before**: Fragile string pattern matching

```python
# OLD: Brittle pattern-based hierarchy detection
if orphan_id.endswith('_menu_1'):
    expected_parent_choice_id = orphan_id[:-7]  # Remove "_menu_1"
```

**After**: Direct semantic relationships

```python
# NEW: Object-based hierarchy traversal
for child in node.children:
    connection = self._create_hierarchy_connection(node, child)
```

### **Architecture Position**

```
Parser → AuthoritativeHierarchy → Visualization
         ↑ SINGLE SOURCE OF TRUTH
```

The hierarchy sits between the parser (which extracts semantic data) and visualization (which needs stable node relationships).

### **Key Benefits**

- ✅ **Eliminates rogue nodes** (phantom containers/choices)
- ✅ **Stable content-based IDs** (immune to index changes)
- ✅ **O(1) relationship lookups** (no string parsing)
- ✅ **Self-validating structure** (catches orphan nodes)
- ✅ **Semantic-first design** (uses existing MenuStructure data)

---

## 🔧 **Core Components** {#core-components}

### **1. HierarchyNode Class**

The fundamental building block that replaces string-based node identification:

```python
@dataclass
class HierarchyNode:
    content_hash: str                    # 🔑 Stable content-based ID
    semantic_id: str                     # 📝 Human-readable identifier
    node_type: str                       # 🏷️ 'label', 'menu_container', 'choice'

    # Content data
    display_name: str
    content: Dict[str, Any]

    # 🎯 KEY IMPROVEMENT: Direct object relationships
    parent: Optional['HierarchyNode']
    children: List['HierarchyNode']

    # Additional metadata
    source_file: Optional[str]
    source_line: Optional[int]
    jump_targets: List[str]
```

**Key Methods**:

- `add_child()` / `remove_child()`: Bidirectional relationship management
- `get_ancestors()` / `get_descendants()`: Tree traversal
- `find_child_by_type()`: Typed child lookup

### **2. AuthoritativeHierarchy Class**

The main orchestrator that builds and manages the hierarchy:

```python
class AuthoritativeHierarchy:
    def __init__(self):
        self.root_nodes: List[HierarchyNode] = []
        self.node_index: Dict[str, HierarchyNode] = {}      # content_hash → node
        self.semantic_index: Dict[str, HierarchyNode] = {}  # semantic_id → node
```

**Core Methods**:

- `build_from_flow_graph()`: Build hierarchy from parser data
- `get_visualization_data()`: Convert to visualization format
- `get_node()`: O(1) node lookup by ID
- `find_parent()` / `find_children()`: O(1) relationship queries

### **3. Content Hash Generation**

Replaces fragile index-based IDs with stable content addressing:

```python
def _generate_content_hash(self, content: Dict[str, Any]) -> str:
    """Generate stable content-based hash for a node."""
    content_str = json.dumps(content, sort_keys=True, ensure_ascii=True)
    hash_obj = hashlib.sha256(content_str.encode('utf-8'))
    return hash_obj.hexdigest()[:16]  # First 16 chars for brevity
```

**Hash Input Examples**:

```python
# Label node
{
    'type': 'label',
    'name': 'ep2cont5',
    'file': 'ep2.rpy',
    'line': 1400
}

# Menu container
{
    'type': 'menu_container',
    'parent_label': 'label_ep2cont5',
    'menu_index': 0,
    'prompt': '',
    'choices': ['Goodnight.', 'Kiss her...']
}

# Choice node
{
    'type': 'choice',
    'parent_menu': 'abc123def456',  # Parent container's hash
    'choice_index': 1,
    'text': 'Kiss her[abgreen] [absandrasroute]',
    'destination': 'ep2cont6'
}
```

---

## 🔐 **Content-Based Node IDs** {#content-based-node-ids}

### **The "Cryptic Names" Issue**

When other LLMs see node IDs like `abc123def456`, they call them "cryptic" because they don't understand the content-hashing system.

**Example Node IDs**:

```
# OLD (Index-based, fragile)
ep2cont5_menu_0_choice_1_nested_menu_1_choice_1_menu_1

# NEW (Content-based, stable)
a1b2c3d4e5f6  # Hash of choice content
```

### **Why Content Hashing?**

1. **Stability**: Content changes → ID changes, but structural changes don't affect unrelated nodes
2. **Uniqueness**: Identical content → identical ID (deduplication)
3. **Brevity**: 16-char hash vs 50+ char string patterns
4. **Performance**: O(1) lookups vs O(n) string matching

### **Semantic ID Bridge**

For human readability, nodes also have semantic IDs:

```python
# Content hash: "a1b2c3d4e5f6"
# Semantic ID: "label_ep2cont5_menu_goodnight_vs_kiss#a1b2c3d4"
semantic_id = f"{parent.semantic_id}_choice_{text_suffix}#{content_hash[:8]}"
```

**Lookup Strategy**:

```python
# Both work for node retrieval
node = hierarchy.get_node("a1b2c3d4e5f6")  # By content hash
node = hierarchy.get_node("label_ep2cont5_menu_goodnight_vs_kiss#a1b2c3d4")  # By semantic ID
```

---

## 📊 **Integration Status** {#integration-status}

### **Current Implementation State**

✅ **Fully Implemented**:

- `AuthoritativeHierarchy` class with complete API
- Content-based hash generation
- Semantic relationship extraction from `MenuStructure`
- Integration with `RenpyFlowDataAdapter`
- Visualization node/connection conversion
- Hierarchy validation and debugging

✅ **Working Features**:

- Eliminates rogue nodes in simple games (The Question, Last Call)
- Proper nested menu hierarchy detection
- O(1) parent/child relationship queries
- Content-addressable node identification

⚠️ **Partial Integration**:

- **Dual system approach**: Old string-based system runs alongside new hierarchy
- **Fallback logic**: If hierarchy fails, system reverts to old approach
- **Debug comparison**: Both systems generate data for validation

### **Integration Points in Code**

#### **1. RenpyFlowDataAdapter.analyze_project()**

```python
# Phase 1: Build authoritative hierarchy
hierarchy = AuthoritativeHierarchy()
hierarchy.build_from_flow_graph(flow_graph)
self._authoritative_hierarchy = hierarchy

# Phase 2: Use hierarchy for visualization if available
if hasattr(self, '_authoritative_hierarchy'):
    menu_nodes, menu_connections = self._create_menu_containers_from_hierarchy()
    label_to_menu_connections = self._create_label_to_menu_connections_from_hierarchy()
    choice_destination_connections = self._create_choice_destination_connections_from_hierarchy()
else:
    # Fallback to old string-based system
```

#### **2. Hierarchy-to-Visualization Conversion**

```python
def _create_menu_containers_from_hierarchy(self):
    """Create visualization nodes from authoritative hierarchy."""
    for node in self._authoritative_hierarchy.node_index.values():
        if node.node_type in ['menu_container', 'choice']:
            viz_node = self._convert_hierarchy_node_to_visualization(node)
            visualization_nodes.append(viz_node)
```

#### **3. Visual Containment Handling**

```python
# CRITICAL: Container-to-choice connections for layout but invisible for rendering
if parent_node.node_type == 'menu_container' and child_node.node_type == 'choice':
    connection.metadata['visual_containment'] = True
    connection.line_style = 'none'  # Invisible edge
```

### **What Needs to Be Kept**

🔒 **CRITICAL - Do Not Remove**:

- `AuthoritativeHierarchy` class and all its methods
- Content hash generation logic (`_generate_content_hash`)
- Hierarchy building from `flow_graph` (`build_from_flow_graph`)
- Visualization conversion methods (`_convert_hierarchy_node_to_visualization`)
- Visual containment metadata (`visual_containment = True`)

⚠️ **TRANSITIONAL - Handle Carefully**:

- Dual system logic in `analyze_project()` (needed for fallback)
- `_compare_hierarchy_systems()` (useful for debugging)
- Old string-based methods (needed until full migration)

🧹 **SAFE TO REMOVE Eventually**:

- Debug comparison output (once system is stable)
- Old string pattern matching logic (after verification)
- Orphan detection based on string parsing

---

## 🪙 **Nested Menu Implementation** {#nested-menu-implementation}

### **The Nested Menu Challenge**

Nested menus were the primary source of rogue nodes in the old string-based system. The authoritative hierarchy solves this by using direct semantic relationships from the parser.

### **How Nested Menus Work Now**

#### **1. Semantic Detection**

```python
# OLD: String pattern-based detection (fragile)
if orphan_id.endswith('_menu_1'):
    expected_parent_choice_id = orphan_id[:-7]  # Remove "_menu_1"

# NEW: Direct semantic relationship (reliable)
for choice in menu_node.choices:
    for nested_menu in choice.nested_menu_structures:  # Direct from parser!
        nested_container = self._create_nested_menu_container(nested_menu, choice_node, nested_idx)
        choice_node.add_child(nested_container)  # Direct object relationship
```

#### **2. Content-Based Nested IDs**

```python
# OLD: Index-fragile nested ID
"ep2cont5_menu_0_choice_1_nested_menu_1_choice_1_menu_1"  # Breaks easily

# NEW: Content-stable nested ID
content_hash = self._generate_content_hash({
    'type': 'nested_menu_container',
    'parent_choice': parent_choice.content_hash,  # Stable parent reference
    'nested_index': nested_idx,
    'prompt': nested_menu.prompt,
    'choices': [choice.text for choice in nested_menu.choices]  # Content-based
})
# Result: "3m2n1o0p" (stable, unique, immune to index changes)
```

#### **3. Hierarchy Traversal**

```python
# Find all nested menus for a choice (O(1))
choice_node = hierarchy.get_node("9x8y7z6w")
nested_containers = choice_node.find_children_by_type('menu_container')

# Get parent choice for a nested menu (O(1))
nested_container = hierarchy.get_node("3m2n1o0p")
parent_choice = nested_container.parent
```

### **Before vs After: Haley's Story ep2cont5**

**🚨 OLD SYSTEM (String-based with rogue nodes)**:

```
Problem: 9 nodes instead of 7, wrong hierarchy
ep2cont5_menu_0_choice_0 → ep2cont5_nested_menu_1 (ROGUE!)
ep2cont5_nested_menu_1 → ep2cont5_nested_menu_1_choice_1 (ROGUE!)
ep2cont5_nested_menu_1_choice_1 → ep2cont5_nested_menu_1_choice_1_menu_1 (weird long name)
```

**✅ NEW SYSTEM (Authoritative hierarchy)**:

```python
# Build from semantic data
label_node = HierarchyNode(content_hash="a1b2c3d4", semantic_id="label_ep2cont5", node_type="label")
menu_container = HierarchyNode(content_hash="f6e5d4c3", semantic_id="label_ep2cont5_menu_0#f6e5d4c3", node_type="menu_container")
choice_1 = HierarchyNode(content_hash="9x8y7z6w", semantic_id="label_ep2cont5_menu_0_choice_kiss#9x8y7z6w", node_type="choice")
nested_container = HierarchyNode(content_hash="3m2n1o0p", semantic_id="label_ep2cont5_menu_0_choice_kiss_nested_0#3m2n1o0p", node_type="menu_container")

# Direct object relationships (no string parsing!)
label_node.add_child(menu_container)
menu_container.add_child(choice_1)
choice_1.add_child(nested_container)  # Direct semantic relationship from MenuChoice.nested_menu_structures
```

**Result**: 7 nodes total, correct hierarchy, no rogue nodes!

### **Nested Menu Visual Containment**

#### **Edge Policy for Nested Menus**

```python
# Container → Choice connections (invisible, for layout only)
if parent_node.node_type == 'menu_container' and child_node.node_type == 'choice':
    connection.metadata['visual_containment'] = True
    connection.line_style = 'none'  # Invisible edge

# Choice → Nested Container connections (visible, shows narrative flow)
elif parent_node.node_type == 'choice' and child_node.node_type == 'menu_container':
    connection.metadata['visual_containment'] = False
    connection.line_style = 'solid'  # Visible edge showing choice leads to nested menu
```

#### **Why This Matters**

- **Visual containment**: Choices appear "inside" their menu containers
- **Narrative flow**: Visible edges show which choices lead to nested menus
- **Layout hierarchy**: Invisible edges provide `in_degree` for proper positioning

### **Implementation in Code**

#### **AuthoritativeHierarchy.\_create_nested_menu_container()**

```python
def _create_nested_menu_container(self, nested_menu: Any, parent_choice: HierarchyNode, nested_idx: int) -> Optional[HierarchyNode]:
    """
    Create nested menu container using semantic parent relationship.

    KEY: Uses MenuStructure.parent_choice relationship directly instead of
    trying to infer it from string patterns.
    """
    # Generate content-based ID (stable!)
    content_hash = self._generate_content_hash({
        'type': 'nested_menu_container',
        'parent_choice': parent_choice.content_hash,  # Direct parent reference
        'nested_index': nested_idx,
        'prompt': getattr(nested_menu, 'prompt', ''),
        'nesting_level': getattr(nested_menu, 'nesting_level', 1),
        'choices': [getattr(choice, 'text', '') for choice in getattr(nested_menu, 'choices', [])]
    })

    # Create semantic ID that clearly shows hierarchy
    semantic_id = f"{parent_choice.semantic_id}_nested_{nested_idx}#{content_hash[:8]}"

    nested_container = HierarchyNode(
        content_hash=content_hash,
        semantic_id=semantic_id,
        node_type='menu_container',
        display_name=f"↳ {getattr(nested_menu, 'prompt', f'Nested Menu {nested_idx}')}",
        content={
            'is_nested': True,
            'nesting_level': getattr(nested_menu, 'nesting_level', 1),
            'parent_choice_id': parent_choice.content_hash  # Authoritative parent reference
        }
    )

    return nested_container
```

#### **Integration in RenpyFlowDataAdapter**

```python
# In _process_menu_choices()
nested_structures = getattr(choice, 'nested_menu_structures', [])  # Direct from parser!
for nested_idx, nested_menu in enumerate(nested_structures):
    nested_container = self._create_nested_menu_container(nested_menu, choice_node, nested_idx)

    if nested_container:
        choice_node.add_child(nested_container)  # Direct object relationship

        # Recursively process nested choices (supports unlimited depth!)
        choice_count += self._process_menu_choices(nested_menu, nested_container)
```

---

## 📖 **Usage Guide** {#usage-guide}

### **For Developers Working on Flow Visualizer**

#### **Reading Node Relationships**

```python
# Get a node by either ID type
node = hierarchy.get_node("a1b2c3d4e5f6")  # Content hash
node = hierarchy.get_node("label_start_menu_0#a1b2c3d4")  # Semantic ID

# Direct relationship queries (O(1))
parent = node.parent
children = node.children

# Find specific child types
menu_containers = node.find_children_by_type('menu_container')
choice_buttons = node.find_children_by_type('choice')
```

#### **Creating New Hierarchy Nodes**

```python
# Generate stable content hash
content_hash = hierarchy._generate_content_hash({
    'type': 'choice',
    'parent_menu': parent_container.content_hash,
    'choice_index': 0,
    'text': 'Continue story',
    'destination': 'next_scene'
})

# Create hierarchy node
choice_node = HierarchyNode(
    content_hash=content_hash,
    semantic_id=f"{parent.semantic_id}_choice_continue#{content_hash[:8]}",
    node_type='choice',
    display_name='Continue story',
    content={'choice_index': 0, 'full_text': 'Continue story'}
)

# Establish relationship
parent_container.add_child(choice_node)
```

#### **Debugging Hierarchy Issues**

```python
# Print full hierarchy structure
hierarchy.print_hierarchy()

# Validate hierarchy consistency
hierarchy._validate_hierarchy()

# Find orphan nodes
orphans = [node for node in hierarchy.node_index.values()
          if node.parent is None and node not in hierarchy.root_nodes]
```

### **For LLMs Working on Visualizer Code**

⚠️ **Important Guidelines**:

1. **Never remove content hashes**: Node IDs like `a1b2c3d4e5f6` are NOT cryptic - they're stable content addresses
2. **Use hierarchy.get_node()**: Don't parse string IDs manually
3. **Respect visual containment**: Don't remove `visual_containment = True` metadata
4. **Check both systems**: Current code runs dual systems - modify both if needed
5. **Validate relationships**: Use `node.parent` and `node.children` instead of string pattern matching

**Common Mistakes to Avoid**:

```python
# ❌ DON'T: Try to "fix" content hashes by making them readable
node_id = "ep2cont5_menu_0_choice_1"  # This breaks content addressing

# ✅ DO: Use semantic IDs for readability, content hashes for stability
content_hash = "a1b2c3d4e5f6"
semantic_id = "label_ep2cont5_menu_0#a1b2c3d4"

# ❌ DON'T: Parse node IDs with string operations
if node_id.endswith('_menu_1'):
    parent_id = node_id[:-7]

# ✅ DO: Use direct object relationships
if node.node_type == 'menu_container':
    parent = node.parent
```

---

## 🐛 **Troubleshooting** {#troubleshooting}

### **Issue: "Zero nodes generated by hierarchy"**

**Symptoms**:

```
[HIERARCHY] Built hierarchy with 0 nodes
```

**Cause**: `flow_graph` structure mismatch

**Solution**: Check `flow_graph` iteration logic:

```python
# ❌ WRONG: flow_graph['labels']
for label_name, label_data in flow_graph['labels'].items():

# ✅ CORRECT: flow_graph direct iteration
for label_name, label_data in flow_graph.items():
```

### **Issue: "Label-to-menu connections missing"**

**Symptoms**: Menu containers appear disconnected from labels

**Cause**: `source_node_id` mismatch between hierarchy and visualization systems

**Solution**: Use simple label names for connections:

```python
# ❌ WRONG: Using content hash as source
source_node_id = label_node.semantic_id.replace('label_', '')  # Content hash

# ✅ CORRECT: Using simple label name
source_node_id = label_name  # Simple string like "start", "ep2cont5"
```

### **Issue: "Choice buttons appearing as orphans"**

**Symptoms**: Choice buttons show up in top-tier instead of inside containers

**Cause**: Missing `container_to_choice` connections for layout algorithm

**Solution**: Ensure invisible connections are created:

```python
if parent_node.node_type == 'menu_container' and child_node.node_type == 'choice':
    connection.metadata['visual_containment'] = True
    connection.line_style = 'none'  # Invisible but provides in_degree
```

### **Issue: "Hierarchy validation fails"**

**Symptoms**:

```
[HIERARCHY WARNING] Orphan node detected: choice_xyz#a1b2c3d4
```

**Cause**: Node created but not added to parent's children list

**Solution**: Always use `add_child()` method:

```python
# ❌ WRONG: Manual relationship assignment
child.parent = parent
parent.children.append(child)

# ✅ CORRECT: Use bidirectional method
parent.add_child(child)  # Sets both parent and children automatically
```

---

## 📞 **Related Documentation**

- **WEAK_PARENTHOOD_NAMING_SYSTEM.md**: Original problem analysis
- **NODE_ID_IMPROVEMENT_PROPOSAL.md**: Content-hashing design
- **FLOW_VISUALIZER_ARCHITECTURE.md**: Overall system architecture
- **CHOICE_OBJECTS_ARCHITECTURE.md**: MenuStructure semantic data

---

## 🚨 **Critical Reminders**

### **For Current Development**

1. **Dual System Active**: Both old and new systems run simultaneously - modify both
2. **Content Hashes Are Not Cryptic**: They're stable content addresses, not random strings
3. **Visual Containment Required**: Container-to-choice connections must be invisible but present
4. **Semantic Data Available**: Use `MenuStructure.parent_choice` instead of string parsing

### **For Future Migration**

1. **Phase Out String Patterns**: Replace all `startswith()`, `endswith()` logic with hierarchy queries
2. **Remove Orphan Detection**: Current orphan logic is artifact of string-based system
3. **Simplify Visualization**: Direct hierarchy-to-visualization conversion eliminates complex fallback logic

---

**System Status**: ✅ **Implemented and Working**  
**Migration Status**: 🔄 **Dual System Active**  
**Stability**: 🟢 **Stable in Simple Games, Testing Complex Games**

---

_Last Updated: January 2025_  
_Implementation: Phase 2 Complete - Dual System Integration_
