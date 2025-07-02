# Label Flow Analysis Statistics Guide

## 📋 Overview

Label Flow Analysis examines how scenes (labels) connect to each other in a visual novel, creating a complete map of the narrative structure. This guide explains what each statistic means and how you can use them to improve your storytelling.

---

## 🔗 Basic Flow Concepts

### **Labels**

- **What it is**: Scene markers in Ren'Py (e.g., `label start:`, `label chapter1:`)
- **Why it matters**: Each label represents a distinct scene or story moment
- **Example**: `694 labels` means your VN has 694 different scenes

### **Flows**

- **What it is**: Connections between scenes (jumps, calls, menu choices)
- **Why it matters**: Shows how players can navigate through your story
- **Example**: `34,383 total flows` means there are 34,383 possible ways to move between scenes

### **Flow Types**

- **Jump**: Direct movement to another scene (`jump next_scene`)
- **Call**: Temporary visit to another scene with return (`call flashback`)
- **Menu Choice**: Player decision leading to different scenes
- **Return**: Going back to the calling scene

---

## 📊 Connectivity Metrics

### **Connectivity Ratio**

- **Formula**: Total Flows ÷ Total Labels
- **What it means**: Average number of connections per scene
- **Interpretation**:
  - `< 1.0`: Linear story with few branches
  - `1.0-3.0`: Moderate branching
  - `> 3.0`: Highly branching, complex narrative
- **Example**: `49.54` means each scene averages ~50 connections (very high!)

### **Average Complexity**

- **What it is**: Average number of outgoing paths from each scene
- **Why it matters**: Indicates how much choice players have
- **Interpretation**:
  - `< 2.0`: Mostly linear progression
  - `2.0-5.0`: Good balance of choice and direction
  - `> 5.0`: Very complex, potentially overwhelming

---

## 🎯 Reachability Analysis

### **Reachable Labels**

- **What it is**: Scenes players can actually reach during gameplay
- **Why it matters**: Unreachable content is wasted effort
- **Example**: `669/694 reachable (96%)` means 25 scenes are unreachable

### **Unreachable Labels**

- **What it is**: Scenes with no path from any entry point
- **Common causes**:
  - Orphaned scenes from old code
  - Test scenes never connected
  - Conditional content with impossible conditions
- **Action needed**: Review and either connect or remove

### **Entry Points**

- **What it is**: Scenes with no incoming connections (starting points)
- **Ideal number**: 1-3 (main story, side stories)
- **High numbers**: May indicate fragmented narrative structure
- **Example**: `91 entry points` suggests many disconnected scene groups

### **Dead End Labels**

- **What it is**: Scenes with no outgoing connections (endings)
- **Why it matters**: Players get stuck unless intentional endings
- **Good ratio**: 5-15% of total scenes
- **Example**: `10 dead ends` from 694 scenes = 1.4% (very good!)

---

## ⭐ Quality Assessment

### **Overall Quality Score** (0-100)

- **80-100**: Excellent - Well-connected, accessible story
- **60-79**: Good - Minor connectivity issues
- **40-59**: Fair - Noticeable structural problems
- **< 40**: Poor - Major navigation issues

### **Reachability Score** (0-80 points)

- **What it measures**: Percentage of reachable content
- **Why 80 points**: Core component of good narrative flow
- **Example**: `76.8/80` means 96% reachability (excellent)

### **Connectivity Score** (0-20 points)

- **What it measures**: Richness of scene interconnections
- **Ideal range**: 1.5-3.0 connectivity ratio
- **Example**: `20/20` means optimal connectivity

---

## 🔍 Flow Patterns

### **Cycles** 🔄

- **What it is**: Circular paths that return to the starting scene
- **Examples**:
  - Daily routine loops
  - Dialogue trees that can repeat
  - "Try again" mechanics
- **Good uses**: Replay value, natural conversation flow
- **Potential issues**: Infinite loops, confusing navigation
- **Example**: `21,553 cycles` indicates extensive replay mechanics

### **Bridges** 🌉

- **What it is**: Critical scenes that connect major story sections
- **Identification**: High incoming AND outgoing connections
- **Why important**: Removing breaks story flow
- **Examples**:
  - Hub locations (school, home, town center)
  - Transition scenes between chapters
  - Decision consolidation points
- **Example**: `364 bridges` shows well-structured narrative flow

### **Hubs** 🎯

- **What it is**: Scenes with many total connections (incoming + outgoing)
- **Characteristics**: High traffic, central importance
- **Common types**:
  - Main character's room (base location)
  - Central meeting areas
  - Major decision points
- **Usage**: Focus polish efforts on these high-impact scenes
- **Example**: `451 hubs` indicates rich, interconnected world

---

## 🛤️ Path Analysis

### **Narrative Paths**

- **What it is**: Sequences of scenes players can experience
- **Example**: `start → character_creation → first_day → school`
- **Uses**:
  - Testing story routes
  - Balancing path lengths
  - Finding optimal story flows

### **Path Depth**

- **What it is**: How many scenes deep a path goes
- **Interpretation**:
  - Depth 0-2: Opening/setup scenes
  - Depth 3-10: Main story progression
  - Depth 10+: Deep branching or side content

---

## 📅 Timeline Analysis

### **Scene Timeline**

- **What it is**: Chronological ordering of scenes based on narrative flow
- **Starting points**: `start`, `main`, `intro`, etc.
- **Benefits**:
  - Visualize story progression
  - Identify pacing issues
  - Plan content distribution

### **Depth Distribution**

- **What it shows**: How many scenes exist at each story depth
- **Ideal shape**: Gradual narrowing (funnel shape)
- **Warning signs**:
  - Too many scenes at depth 0 (multiple disconnected starts)
  - Sudden drops (missing content bridges)

---

## 🎮 Practical Applications

### **For Game Developers**

#### **Quality Assurance**

- **Check reachability**: Ensure all content is accessible
- **Find dead ends**: Add navigation options or mark as intentional endings
- **Identify orphaned scenes**: Connect or remove unreachable content

#### **Story Structure**

- **Hub optimization**: Polish high-traffic scenes first
- **Bridge reinforcement**: Ensure critical connection scenes are solid
- **Cycle management**: Balance replay value vs. player confusion

#### **Player Experience**

- **Path balancing**: Ensure major routes have similar depth/content
- **Choice clarity**: High-complexity scenes need clear options
- **Navigation aids**: Add help for complex hub areas

### **For The Plot Thickens**

#### **Visualization Priorities**

- **Hub scenes**: Highlight central importance in timeline view
- **Bridge scenes**: Show as critical connection points
- **Cycles**: Indicate replay/loop opportunities

#### **Analysis Features**

- **Quality scoring**: Help users identify improvement areas
- **Unreachable detection**: Flag content that needs connection
- **Path exploration**: Show player journey possibilities

#### **Import Optimization**

- **Focus on hubs**: Import detailed data for high-traffic scenes first
- **Bridge mapping**: Ensure critical connections are preserved
- **Timeline building**: Use flow analysis for automatic scene ordering

---

## 🎯 Understanding Your Results

### **"Savior" VN Example Analysis**

| Metric                 | Value          | Interpretation                   |
| ---------------------- | -------------- | -------------------------------- |
| **694 labels**         | Very large     | Major commercial VN scope        |
| **34,383 flows**       | Extremely high | Highly interactive, choice-rich  |
| **96% reachable**      | Excellent      | Well-connected content           |
| **49.54 connectivity** | Very high      | Complex, non-linear storytelling |
| **96.8/100 quality**   | Excellent      | Professional-level structure     |
| **2,313 paths**        | High           | Rich player choice variety       |
| **21,553 cycles**      | Very high      | Extensive replay mechanics       |

### **What This Tells Us**

- **Professional quality**: High standards of connectivity and accessibility
- **Player-centric design**: Extensive choice and replay value
- **Complex narrative**: Non-linear, interactive storytelling approach
- **Polished structure**: Minimal dead ends and unreachable content

---

## 🔧 Improvement Recommendations

### **Based on Common Issues**

#### **High Entry Points** (like "Savior's" 91)

- **Problem**: Fragmented story structure
- **Solutions**:
  - Create central hub connecting story branches
  - Add introductory sequence linking sections
  - Consider if all entry points are intentional

#### **Low Reachability** (< 90%)

- **Problem**: Wasted content, confused players
- **Solutions**:
  - Review unreachable scenes for connection opportunities
  - Remove or repurpose orphaned content
  - Add navigation aids or hints

#### **High Complexity** (> 10 avg)

- **Problem**: Player overwhelm, analysis paralysis
- **Solutions**:
  - Group related choices
  - Add preview text for choice outcomes
  - Consider progressive disclosure of options

#### **Few Cycles** (< 100)

- **Problem**: Limited replay value
- **Solutions**:
  - Add dialogue variation systems
  - Create optional side activities
  - Design meaningful choice consequences

---

## 📈 Using Statistics for Development

### **Planning Phase**

- **Set target metrics**: Aim for 90%+ reachability, 2-5 connectivity ratio
- **Design hub structure**: Plan 3-5 major hub scenes
- **Map critical paths**: Ensure main story routes are well-connected

### **Development Phase**

- **Regular analysis**: Check flow statistics during development
- **Progressive connection**: Connect scenes as you build them
- **Balance testing**: Use path analysis to verify route balance

### **Polish Phase**

- **Hub optimization**: Focus effort on high-traffic scenes
- **Dead end resolution**: Add navigation options or content
- **Quality validation**: Aim for 85+ quality score before release

---

## 🎓 Advanced Concepts

### **Flow Clustering**

- **What it is**: Groups of highly interconnected scenes
- **Uses**: Identify story modules, plan development phases
- **Ideal**: 3-7 major clusters with bridge connections

### **Centrality Measures**

- **Betweenness**: Scenes that lie on many paths (bridges)
- **Degree**: Scenes with many direct connections (hubs)
- **Closeness**: Scenes easily reachable from others

### **Network Density**

- **Formula**: Actual connections ÷ Possible connections
- **Interpretation**: How interconnected your story really is
- **Balance**: Too dense = overwhelming, too sparse = linear

---

This analysis provides powerful insights into your narrative structure, helping you create more engaging, well-connected stories that give players meaningful choices while maintaining clear direction.
