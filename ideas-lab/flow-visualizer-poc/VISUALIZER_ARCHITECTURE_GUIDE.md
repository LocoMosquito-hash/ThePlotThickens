# Flow Visualizer Architecture Guide

## 🚨 CRITICAL: Which File to Edit?

This guide prevents confusion about which visualizer file to modify for different purposes.

## Architecture Overview

The flow visualizer has **TWO main implementations** that serve different purposes:

### 1. **Production Visualizer** (EDIT THIS ONE) ✅

**File**: `vn_flow_visualizer.py`

- 🎯 **PRIMARY**: This is the main production visualizer
- ✅ **All fixes go here**: Authoritative hierarchy, layout algorithms, bug fixes
- 🔗 **Used by**: Control panel, main POC application, all production features
- 📊 **Status**: Fully functional with all recent improvements

### 2. **Demo/Testing Visualizer** (DON'T EDIT) ⚠️

**File**: `vn_flow_visualizer_v2_simple.py`

- 🧪 **PURPOSE**: Clean architecture demonstration and isolated testing
- ⚠️ **DO NOT EDIT**: Unless specifically testing clean interface approach
- 🔗 **Used by**: `renpy_flow_visualizer_v2_main.py` only
- 📝 **Status**: Simplified version, may not have latest fixes

## When to Edit Which File

### ✅ **Edit `vn_flow_visualizer.py` for**:

- Bug fixes (rogue nodes, layout issues, etc.)
- New features (menu containers, choice handling, etc.)
- Layout algorithm improvements
- Performance optimizations
- Any production changes

### ⚠️ **Edit `vn_flow_visualizer_v2_simple.py` only for**:

- Testing clean interface architecture
- Demonstrating simplified implementation
- Isolated experimentation

### 🚫 **NEVER edit both simultaneously**:

- Changes should go to production version first
- Simple version is kept for reference/testing only

## Recent Major Changes

### ✅ Applied to Production (`vn_flow_visualizer.py`):

- **Authoritative Hierarchy**: Replaced string-based node relationships
- **Layout Algorithm Cleanup**: Removed all algorithms except dot-like
- **Visual Containment Fix**: Menu containers properly contain choices
- **Narrative Flow Fix**: Labels properly positioned in hierarchy

### ⚠️ NOT applied to Simple version:

- Simple version may still have old layout algorithms
- Simple version may not have hierarchy fixes
- This is intentional - keeps it as a clean reference

## File Relationships

```
Production Flow:
vn_control_panel.py → vn_flow_visualizer.py (MAIN)
        ↓
    All fixes applied here

Testing/Demo Flow:
renpy_flow_visualizer_v2_main.py → vn_flow_visualizer_v2_simple.py
        ↓
    Clean architecture demo only
```

## Decision History

- **2025-01**: Attempted to archive simple version → "Epic failure with errors"
- **2025-01**: Decision made to keep both versions for safety
- **Current**: Dual architecture documented to prevent confusion

## 🎯 Quick Reference

**Need to fix a bug?** → Edit `vn_flow_visualizer.py`
**Need to add a feature?** → Edit `vn_flow_visualizer.py`
**Testing clean interface?** → Use `vn_flow_visualizer_v2_simple.py`
**Not sure?** → Default to `vn_flow_visualizer.py`

---

_Last updated: January 2025_
_This guide prevents the "which file should I edit?" confusion_
