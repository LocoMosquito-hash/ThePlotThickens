"""
Menu Container Prototype - Visual demonstration of menu node container concept

This prototype shows how menu nodes could be visualized as actual menu containers
with individual choice connectors, using ch4ashbagdone as an example.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_menu_container_prototype():
    """Create a prototype visualization of the menu container concept."""
    
    # Create figure with two subplots for comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))
    fig.suptitle('Menu Node Container Prototype: ch4ashbagdone', fontsize=16, fontweight='bold')
    
    # === LEFT SIDE: Current Approach ===
    ax1.set_title('Current Approach\n(Direct connections from label)', fontsize=14)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis('off')
    
    # Main label node (current)
    main_node = FancyBboxPatch((3, 4), 4, 2, 
                              boxstyle="round,pad=0.1",
                              facecolor='lightblue',
                              edgecolor='blue',
                              linewidth=2)
    ax1.add_patch(main_node)
    ax1.text(5, 5, 'ch4ashbagdone', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Destination nodes (current)
    destinations = [
        {'name': 'ch4ashfashion', 'pos': (1, 8), 'color': 'lightgreen'},
        {'name': 'ch4ashdrink', 'pos': (9, 8), 'color': 'lightcoral'},
        {'name': 'ch4ashanimal', 'pos': (1, 2), 'color': 'lightyellow'},
        {'name': 'ch4ashveg', 'pos': (9, 2), 'color': 'lightpink'}
    ]
    
    for dest in destinations:
        dest_node = FancyBboxPatch((dest['pos'][0]-0.8, dest['pos'][1]-0.5), 1.6, 1,
                                  boxstyle="round,pad=0.1",
                                  facecolor=dest['color'],
                                  edgecolor='gray',
                                  linewidth=1)
        ax1.add_patch(dest_node)
        ax1.text(dest['pos'][0], dest['pos'][1], dest['name'].replace('ch4ash', ''), 
                ha='center', va='center', fontsize=10)
        
        # Direct connection lines (current approach)
        ax1.arrow(5, 5, dest['pos'][0]-5, dest['pos'][1]-5, 
                 head_width=0.2, head_length=0.2, fc='red', ec='red', alpha=0.7)
    
    ax1.text(5, 1, 'Problem: 4 lines cluttering the main node', 
            ha='center', va='center', fontsize=11, color='red', style='italic')
    
    # === RIGHT SIDE: Proposed Menu Container ===
    ax2.set_title('Proposed Menu Container\n(Individual choice connectors)', fontsize=14)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis('off')
    
    # Main label node (proposed)
    main_node_new = FancyBboxPatch((3, 7), 4, 1.5, 
                                  boxstyle="round,pad=0.1",
                                  facecolor='lightblue',
                                  edgecolor='blue',
                                  linewidth=2)
    ax2.add_patch(main_node_new)
    ax2.text(5, 7.75, 'ch4ashbagdone', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Menu container (NEW!)
    menu_container = FancyBboxPatch((2, 3.5), 6, 3, 
                                   boxstyle="round,pad=0.2",
                                   facecolor='gold',
                                   edgecolor='orange',
                                   linewidth=2,
                                   alpha=0.8)
    ax2.add_patch(menu_container)
    ax2.text(5, 6, 'MENU', ha='center', va='center', fontsize=14, fontweight='bold')
    
    # Individual menu choices inside container
    choices = [
        {'name': 'Fashion', 'pos': (3, 5), 'dest_pos': (1, 8)},
        {'name': 'Drinking', 'pos': (7, 5), 'dest_pos': (9, 8)},
        {'name': 'Animals', 'pos': (3, 4), 'dest_pos': (1, 2)},
        {'name': 'Vegetables', 'pos': (7, 4), 'dest_pos': (9, 2)}
    ]
    
    for i, choice in enumerate(choices):
        # Choice button inside menu container
        choice_btn = FancyBboxPatch((choice['pos'][0]-0.6, choice['pos'][1]-0.3), 1.2, 0.6,
                                   boxstyle="round,pad=0.05",
                                   facecolor='white',
                                   edgecolor='darkgray',
                                   linewidth=1)
        ax2.add_patch(choice_btn)
        ax2.text(choice['pos'][0], choice['pos'][1], choice['name'], 
                ha='center', va='center', fontsize=9)
        
        # Destination node
        dest_node = FancyBboxPatch((choice['dest_pos'][0]-0.8, choice['dest_pos'][1]-0.5), 1.6, 1,
                                  boxstyle="round,pad=0.1",
                                  facecolor=destinations[i]['color'],
                                  edgecolor='gray',
                                  linewidth=1)
        ax2.add_patch(dest_node)
        ax2.text(choice['dest_pos'][0], choice['dest_pos'][1], choice['name'].lower(), 
                ha='center', va='center', fontsize=10)
        
        # Connection from choice to destination (NEW!)
        ax2.arrow(choice['pos'][0], choice['pos'][1], 
                 choice['dest_pos'][0]-choice['pos'][0], 
                 choice['dest_pos'][1]-choice['pos'][1], 
                 head_width=0.1, head_length=0.15, fc='darkgreen', ec='darkgreen', 
                 alpha=0.8, linewidth=2)
    
    # Single connection from main label to menu container
    ax2.arrow(5, 7, 0, -0.3, head_width=0.2, head_length=0.2, fc='blue', ec='blue', linewidth=3)
    
    ax2.text(5, 1, 'Solution: 1 line to menu + individual choice connectors', 
            ha='center', va='center', fontsize=11, color='green', style='italic')
    
    plt.tight_layout()
    plt.savefig('menu_container_prototype.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("🎨 Menu Container Prototype Created!")
    print("="*50)
    print("KEY BENEFITS:")
    print("• Reduces visual clutter on main label nodes")
    print("• Clearly shows menu structure and choices")
    print("• Each choice has its own connection line")
    print("• Menu container acts as a visual grouping element")
    print("• Maintains clear flow hierarchy: Label → Menu → Choices → Destinations")
    print()
    print("TECHNICAL IMPLEMENTATION:")
    print("• Menu container: Gold/orange rounded rectangle")
    print("• Individual choices: White buttons inside container")
    print("• Choice connections: Dark green arrows to destinations")
    print("• Label-to-menu: Single blue arrow connection")

def demonstrate_data_structure():
    """Show how the data structure would change for menu containers."""
    
    print("\n🔧 DATA STRUCTURE CHANGES:")
    print("="*50)
    
    print("CURRENT STRUCTURE:")
    print("ch4ashbagdone:")
    print("  - successors: ['ch4ashfashion', 'ch4ashdrink', 'ch4ashanimal', 'ch4ashveg']")
    print("  - has_menu: True")
    print("  - menu_nodes: [MenuNode objects]")
    print()
    
    print("PROPOSED STRUCTURE:")
    print("ch4ashbagdone:")
    print("  - successors: ['ch4ashbagdone_menu_1']")
    print("  - has_menu: True")
    print("  - menu_nodes: [MenuNode objects]")
    print()
    print("ch4ashbagdone_menu_1 (MenuContainerNode):")
    print("  - type: 'menu_container'")
    print("  - parent_label: 'ch4ashbagdone'")
    print("  - choices: [")
    print("    {'text': 'Fashion', 'destination': 'ch4ashfashion'},")
    print("    {'text': 'Drinking', 'destination': 'ch4ashdrink'},")
    print("    {'text': 'Animals', 'destination': 'ch4ashanimal'},")
    print("    {'text': 'Vegetables', 'destination': 'ch4ashveg'}")
    print("  ]")
    print("  - successors: ['ch4ashfashion', 'ch4ashdrink', 'ch4ashanimal', 'ch4ashveg']")

if __name__ == "__main__":
    create_menu_container_prototype()
    demonstrate_data_structure() 