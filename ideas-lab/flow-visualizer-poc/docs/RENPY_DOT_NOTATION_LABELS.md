# Ren'Py Dot Notation in Label Names

**Document Version**: 1.0  
**Date**: September 22, 2025  
**Author**: Flow Visualizer Development Team  
**Purpose**: Understanding hierarchical label naming patterns in Ren'Py visual novels

---

## 🎯 **Overview**

This document explains the **dot notation pattern** used in Ren'Py label names, a developer-created organizational system that creates pseudo-namespaces within Ren'Py's flat label structure. This pattern is particularly common in complex visual novels with free roam mechanics, location-based navigation, and extensive branching storylines.

---

## 🔍 **What is Dot Notation in Ren'Py Labels?**

### **Basic Pattern**

```renpy
label base_name                    # Main/parent label
label base_name.sublabel1          # Child label 1
label base_name.sublabel2          # Child label 2
label base_name.sublabel3          # Child label 3
```

### **Real-World Example: Amnesia VN**

**File**: `Act 1d1 Free Roam Home.rpy`

```renpy
label act_1d1_FreeRoam_Home                    # Base free roam controller
label act_1d1_FreeRoam_Home.Hall2              # Hall location
label act_1d1_FreeRoam_Home.Bedroom_MC         # MC's bedroom
label act_1d1_FreeRoam_Home.Kitchen            # Kitchen location
label act_1d1_FreeRoam_Home.Basement           # Basement location
label act_1d1_FreeRoam_Home.Basement_Office    # Office within basement
label act_1d1_FreeRoam_Home.Basement_Library   # Library within basement
```

**Result**: 1 base label + 27 sublabels, all logically organized under one namespace.

---

## 🏗️ **Technical Implementation**

### **From Ren'Py's Perspective**

- **No special syntax** - Dots are simply part of the label name
- **Standard functionality** - `jump base_name.sublabel` works normally
- **Flat namespace** - Ren'Py treats all labels as independent entities
- **No automatic hierarchy** - Relationships are purely organizational

### **Code Examples**

```renpy
# All of these are equivalent from Ren'Py's perspective:
label simple_label:
    "This is a simple label"
    return

label namespace.sublabel:
    "This is a sublabel with dot notation"
    return

label very.deep.nested.label:
    "This works too, but is less common"
    return

# Jumping works normally:
label start:
    jump namespace.sublabel  # Standard jump syntax
```

### **What Ren'Py Does NOT Do**

- ❌ **No automatic parent-child relationships**
- ❌ **No namespace-based scoping**
- ❌ **No inheritance or shared variables**
- ❌ **No automatic navigation between related labels**

---

## 🎮 **Common Use Cases**

### **1. Free Roam Navigation Systems**

**Pattern**: `system_name.location_name`

```renpy
label home_exploration                    # Main exploration controller
label home_exploration.living_room       # Individual locations
label home_exploration.kitchen
label home_exploration.bedroom
label home_exploration.basement
```

**Benefits**:

- Clear separation of locations
- Easy to identify all locations in a system
- Prevents naming conflicts with other systems

### **2. Character Route Organization**

**Pattern**: `character_name.route_section`

```renpy
label sarah_route                        # Main character route
label sarah_route.introduction           # Route sections
label sarah_route.first_date
label sarah_route.confession
label sarah_route.good_ending
label sarah_route.bad_ending
```

**Benefits**:

- Groups all content for a specific character
- Makes route structure immediately visible
- Simplifies content management

### **3. Chapter/Act Structure**

**Pattern**: `chapter_name.scene_name`

```renpy
label chapter1                          # Chapter controller
label chapter1.opening                  # Individual scenes
label chapter1.school_scene
label chapter1.home_scene
label chapter1.climax
label chapter1.resolution
```

**Benefits**:

- Clear story progression structure
- Easy to reorganize content
- Helps with save game organization

### **4. Mini-Game Systems**

**Pattern**: `minigame_name.game_state`

```renpy
label poker_game                        # Main game controller
label poker_game.deal_cards             # Game states
label poker_game.player_turn
label poker_game.ai_turn
label poker_game.show_results
label poker_game.game_over
```

**Benefits**:

- Isolates complex game logic
- Makes state management clearer
- Easier debugging and maintenance

---

## 📊 **Analysis: Amnesia VN Case Study**

### **Structure Breakdown**

**Base System**: `act_1d1_FreeRoam_Home`

- **Total Labels**: 28 (1 base + 27 sublabels)
- **Organization**: Location-based free roam system
- **Naming Convention**: Descriptive location names

### **Location Categories**

```
act_1d1_FreeRoam_Home                   # Main controller
├── General Areas
│   ├── .Hall1, .Hall2                 # Hallways
│   ├── .Living, .Dinning, .Kitchen    # Common areas
│   └── .Bathoom, .Bathoom_Girls       # Bathrooms
├── Bedrooms
│   ├── .Bedroom_MC                    # Main character
│   ├── .Bedroom_Elena                 # Other characters
│   ├── .Bedroom_Kate
│   └── .Bedroom_Alexandra
├── Basement Areas
│   ├── .Basement                      # Main basement
│   ├── .Basement_Office               # Basement rooms
│   ├── .Basement_Library
│   ├── .Basement_Gym
│   └── .Basement_Auto
└── Interactive Objects
    ├── .Bedroom_MC_TV                 # Room-specific objects
    ├── .Bedroom_MC_Bed
    └── .Bedroom_MC_Wardrobe
```

### **Design Insights**

1. **Hierarchical thinking** - Developers organized content logically
2. **Scalable structure** - Easy to add new locations
3. **Clear relationships** - Related content is visually grouped
4. **Maintenance friendly** - Changes affect clearly defined areas

---

## 🛠️ **Best Practices**

### **✅ Recommended Patterns**

#### **1. Consistent Naming Convention**

```renpy
# Good: Consistent pattern
label exploration.bedroom
label exploration.kitchen
label exploration.basement

# Bad: Inconsistent pattern
label bedroom_explore
label kitchen_navigation
label basement_area
```

#### **2. Logical Grouping**

```renpy
# Good: Grouped by system/purpose
label combat.attack
label combat.defend
label combat.escape

label dialogue.greeting
label dialogue.question
label dialogue.goodbye

# Bad: Mixed purposes
label combat.attack
label dialogue.greeting
label combat.defend
```

#### **3. Descriptive Names**

```renpy
# Good: Clear purpose
label date_system.restaurant_scene
label date_system.movie_theater
label date_system.park_walk

# Bad: Unclear purpose
label date_system.scene1
label date_system.scene2
label date_system.scene3
```

### **❌ Anti-Patterns to Avoid**

#### **1. Overly Deep Nesting**

```renpy
# Bad: Too many levels
label game.chapter1.act1.scene1.subsection1.part1

# Better: Flatter structure
label ch1_act1_scene1
label ch1_act1_scene2
```

#### **2. Inconsistent Depth**

```renpy
# Bad: Inconsistent hierarchy levels
label system.level1
label system.category.level2.sublevel
label system.other

# Better: Consistent depth
label system.level1_option1
label system.level1_option2
label system.level1_option3
```

#### **3. Meaningless Grouping**

```renpy
# Bad: Arbitrary grouping
label misc.important_scene
label misc.character_introduction
label misc.ending

# Better: Meaningful grouping
label story.introduction
label story.climax
label story.ending
```

---

## 🔧 **Implementation Guidelines**

### **Planning Your Namespace Structure**

#### **1. Identify Major Systems**

- Story progression (chapters, acts)
- Character interactions (routes, relationships)
- Gameplay mechanics (mini-games, exploration)
- UI/Menu systems (settings, save/load)

#### **2. Design Hierarchy**

```
System Level 1: Major game components
├── System Level 2: Sub-components
│   ├── Content Level 1: Individual scenes/states
│   └── Content Level 2: Specific interactions
```

#### **3. Establish Naming Conventions**

- **Use underscores** for multi-word names: `bedroom_mc` not `bedroommc`
- **Be descriptive** but concise: `kitchen` not `k`, but also not `kitchen_where_cooking_happens`
- **Stay consistent** with tense, capitalization, and abbreviations

### **Development Workflow**

#### **1. Start Simple**

```renpy
# Begin with basic structure
label chapter1
label chapter1.scene1
label chapter1.scene2
```

#### **2. Expand Gradually**

```renpy
# Add detail as needed
label chapter1
label chapter1.intro
label chapter1.school_scene
label chapter1.home_scene
label chapter1.resolution
```

#### **3. Refactor When Necessary**

- **Monitor complexity** - If finding labels becomes difficult, reorganize
- **Group related content** - Move scattered related labels together
- **Update documentation** - Keep track of your namespace structure

---

## 📈 **Benefits and Drawbacks**

### **✅ Benefits**

#### **Code Organization**

- **Visual grouping** - Related labels appear together in file lists
- **Logical structure** - Clear relationships between game components
- **Reduced conflicts** - Namespace prevents accidental name collisions

#### **Development Efficiency**

- **Easier navigation** - IDEs can collapse/expand namespaces
- **Faster debugging** - Problems are isolated to specific systems
- **Team collaboration** - Clear ownership of different game areas

#### **Maintenance**

- **Scalable architecture** - Easy to add new content to existing systems
- **Refactoring support** - Can rename entire namespaces at once
- **Documentation** - Structure is self-documenting

### **❌ Potential Drawbacks**

#### **Complexity**

- **Learning curve** - New developers need to understand the system
- **Over-engineering** - Can become unnecessarily complex for simple games
- **Inconsistency risk** - Requires discipline to maintain patterns

#### **Technical Limitations**

- **No automatic benefits** - Ren'Py doesn't provide namespace features
- **Longer names** - More typing required for jumps/calls
- **IDE limitations** - Not all editors support namespace folding

---

## 🎯 **Flow Visualizer Implications**

### **Visualization Challenges**

- **Namespace relationships** - How to show hierarchical relationships in flat graphs
- **Grouping visualization** - Whether to cluster related labels visually
- **Navigation complexity** - Handling many sublabels without cluttering

### **Potential Solutions**

1. **Hierarchical clustering** - Group sublabels under parent nodes
2. **Namespace filtering** - Allow users to focus on specific namespaces
3. **Color coding** - Use colors to indicate namespace membership
4. **Collapsible groups** - Let users expand/collapse namespace clusters

### **Current Behavior**

The flow visualizer currently treats all labels as independent entities, which may not optimally represent the developer's intended organization for games using extensive dot notation.

---

## 🔮 **Future Considerations**

### **Enhanced Parser Support**

- **Namespace detection** - Automatically identify namespace patterns
- **Hierarchical analysis** - Understand parent-child relationships
- **Smart grouping** - Suggest logical visualizations based on naming patterns

### **Visualization Improvements**

- **Namespace-aware layouts** - Position related labels together
- **Interactive exploration** - Allow drilling down into namespace hierarchies
- **Relationship highlighting** - Show connections between namespace levels

### **Developer Tools**

- **Namespace validation** - Check for consistent naming patterns
- **Refactoring support** - Help rename entire namespaces
- **Documentation generation** - Auto-generate namespace documentation

---

## 📚 **Examples from Popular VNs**

### **Free Roam Games**

- **Amnesia**: Location-based exploration (`act_1d1_FreeRoam_Home.Kitchen`)
- **Dating Sims**: Character route organization (`sarah_route.confession`)
- **RPG Elements**: Skill/stat systems (`character_stats.strength_training`)

### **Story-Driven Games**

- **Chapter Organization**: (`chapter1.opening_scene`)
- **Route Branching**: (`true_ending.final_choice`)
- **Flashback Systems**: (`memories.childhood_scene`)

### **Complex Mechanics**

- **Mini-Games**: (`poker_game.deal_cards`)
- **Combat Systems**: (`battle.player_turn`)
- **Inventory Management**: (`inventory.use_item`)

---

## 📋 **Quick Reference**

### **Common Patterns**

| Pattern           | Use Case             | Example            |
| ----------------- | -------------------- | ------------------ |
| `system.location` | Free roam navigation | `home.kitchen`     |
| `character.scene` | Character routes     | `sarah.confession` |
| `chapter.section` | Story organization   | `ch1.opening`      |
| `minigame.state`  | Game mechanics       | `poker.deal_cards` |
| `menu.option`     | UI organization      | `settings.audio`   |

### **Naming Guidelines**

- ✅ **Use underscores** for multi-word names
- ✅ **Be descriptive** but concise
- ✅ **Stay consistent** across the project
- ✅ **Group logically** by function or location
- ❌ **Avoid deep nesting** (more than 2-3 levels)
- ❌ **Don't mix naming conventions**

### **Flow Visualizer Tips**

- Labels with dot notation may appear as separate nodes
- Look for patterns in label names to understand game structure
- Consider namespace relationships when analyzing flow connections
- Use filtering to focus on specific namespace groups

---

## 🏆 **Conclusion**

Dot notation in Ren'Py label names is a **powerful organizational pattern** that helps developers manage complex visual novel projects. While Ren'Py doesn't provide built-in namespace support, this developer-created convention offers significant benefits for code organization, maintenance, and team collaboration.

Understanding this pattern is crucial for:

- **VN developers** creating complex, multi-system games
- **Flow visualization tools** that need to represent hierarchical relationships
- **Code analysis** that seeks to understand developer intent and game structure

The pattern represents **developer intelligence** - a systematic approach to managing complexity that goes beyond the basic capabilities of the Ren'Py language itself.

---

**Document Status**: ✅ **Complete**  
**Based on Analysis**: Real-world VN examination (Amnesia v0.95b)  
**Validation**: Pattern confirmed across 28 labels in single file  
**Next Steps**: Consider enhanced visualization support for namespace patterns

---

_"Dot notation in Ren'Py labels represents the evolution of visual novel development from simple linear stories to complex, multi-system interactive experiences. Understanding these patterns is key to creating tools that support modern VN development practices."_

**Documentation Complete** 🎉
