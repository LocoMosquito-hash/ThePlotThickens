# Renpy Flow Visualizer - Proof of Concept

A standalone interactive visualization tool for mapping the narrative branching structure of Renpy visual novels.

## Features

- **Interactive Node Graph**: Visual representation of story labels as connected nodes
- **Multiple Layout Algorithms**: Spring, circular, and hierarchical layouts
- **Node Interaction**:
  - Left-click to select nodes
  - Right-click for context menus with label details
  - Mouse wheel to zoom
  - Drag to pan
- **Color-coded Nodes**:
  - 🟢 Green: Start label
  - 🔵 Blue: Regular story labels
  - 🟡 Yellow: Menu choice points
  - 🔴 Red: Ending labels
- **Control Panel**: Project stats, layout controls, and selected node details

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r visualizer_requirements.txt

# Or install manually:
pip install PyQt6 networkx
```

### Running

```bash
python run_visualizer.py
```

### Usage

1. **Load a Project**:

   - Click "Browse..." to select a Renpy game folder
   - Must contain `.rpy` files (decompiled if needed)
   - Click "Load & Analyze"

2. **Interact with the Graph**:

   - Zoom with mouse wheel
   - Pan by dragging empty space
   - Select nodes by clicking
   - Right-click nodes for details

3. **Try Different Layouts**:
   - Use the Layout Controls panel
   - Switch between spring, circular, and hierarchical
   - Click "Apply Layout" to refresh

## Current Status: POC

This is a proof-of-concept implementation with:

✅ **Working:**

- Basic GUI with file loading
- Interactive node visualization
- Multiple layout algorithms
- Node selection and context menus
- Project statistics display

🚧 **Mock Data:**

- Currently uses mock/demo data for testing
- Real Renpy integration planned for next phase

🔄 **Planned Features:**

- Integration with existing renpy-source-api
- Path highlighting (breadcrumb trails)
- Export capabilities
- Advanced filtering options
- Performance optimizations for large VNs

## Architecture

```
renpy_flow_visualizer.py    # Main application window
├── vn_flow_visualizer.py   # Interactive graph visualization
└── vn_control_panel.py     # Side panel controls
```

**Technology Stack:**

- **PyQt6** - Native GUI framework
- **QGraphicsView/QGraphicsScene** - Hardware-accelerated 2D graphics
- **NetworkX** - Graph algorithms and layout calculations
- **Custom QGraphicsItems** - Interactive nodes and connections

## Integration Ready

The POC is designed with clean separation of concerns:

- Backend: Data analysis (your existing renpy-source-api)
- Frontend: Interactive visualization (this POC)

When ready, simply replace the mock data in `analyze_renpy_project()` with:

```python
from app.renpy_source_api.core import RenpyProject
project = RenpyProject(path)
return project.get_flow_graph()
```

## Testing

Try with any Renpy game folder. The POC will show a warning if no `.rpy` files are found but will continue with demo data for testing the interface.

---

**Next Steps**: Once the visualization works well with mock data, we'll integrate your existing renpy-source-api for real VN analysis.
