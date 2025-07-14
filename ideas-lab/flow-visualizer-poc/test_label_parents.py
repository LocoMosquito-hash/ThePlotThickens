import sys
import os
from pathlib import Path

# Add the main app directory to path for renpy-source-api imports
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent / "app"
renpy_api_dir = app_dir / "renpy-source-api"
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(renpy_api_dir))

from core import RenpyProject

# Path to the game's 'game' directory
project_path = r'T:/AG/MySisterMyRoommateV1.69-pc/game'
print(f"Loading project: {project_path}")

project = RenpyProject(project_path)
flow_graph = project.get_flow_graph()
print("Flow graph loaded.")

def get_parents(label_name):
    node = flow_graph.get(label_name)
    if not node:
        return []
    return [flow['source_label'] for flow in node['incoming_flows']]

labels_to_check = ['choice3corygym2c', 'v11ignore']
for label in labels_to_check:
    parents = get_parents(label)
    print(f"Parents of '{label}': {parents if parents else 'None (no incoming flows)'}") 