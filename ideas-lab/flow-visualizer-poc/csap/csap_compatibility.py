#!/usr/bin/env python3
"""
CSAP Compatibility Layer

Converts CSAP AST objects to existing ScreenElement/ScreenStructure objects
for seamless integration with the flow visualizer.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add paths for existing classes
current_dir = Path(__file__).parent
app_dir = current_dir.parent.parent.parent / "app" / "renpy-source-api"
sys.path.insert(0, str(app_dir))

try:
    from parser import ScreenElement, ScreenStructure
except ImportError:
    # Fallback definitions for testing
    from dataclasses import dataclass, field
    from typing import Tuple
    
    @dataclass
    class ScreenElement:
        element_type: str
        text: Optional[str] = None
        coordinates: Optional[Tuple[int, int, int, int]] = None
        destination: Optional[str] = None
        action_type: Optional[str] = None
        file_path: str = ""
        line_number: int = 0
        element_index: int = 0
        has_condition: bool = False
        condition: Optional[str] = None
    
    @dataclass
    class ScreenStructure:
        screen_name: str
        file_path: str
        line_number: int
        elements: List[ScreenElement] = field(default_factory=list)
        screen_type: str = "standard"
        has_imagemap: bool = False
        imagemap_ground: Optional[str] = None
        imagemap_hover: Optional[str] = None
        label_context: Optional[str] = None
        total_elements: int = 0
        interactive_elements: int = 0

try:
    from .csap_ast import ScreenNode, ScreenElementNode, TextButtonNode, ImageButtonNode, ButtonNode, HotspotNode, ImageMapNode, LayoutNode, ConditionalElementNode
except ImportError:
    from csap_ast import ScreenNode, ScreenElementNode, TextButtonNode, ImageButtonNode, ButtonNode, HotspotNode, ImageMapNode, LayoutNode, ConditionalElementNode
try:
    from .csap_exceptions import CSAPError
except ImportError:
    from csap_exceptions import CSAPError


class CSAPCompatibilityAdapter:
    """Converts CSAP AST objects to existing ScreenElement/ScreenStructure format."""
    
    def __init__(self):
        """Initialize the compatibility adapter."""
        pass
    
    def convert_screen_node_to_structure(self, screen_node: ScreenNode, file_path: str = "") -> ScreenStructure:
        """
        Convert a CSAP ScreenNode to a ScreenStructure.
        
        Args:
            screen_node: CSAP ScreenNode from parsing
            file_path: Path to the source file
            
        Returns:
            ScreenStructure compatible with existing flow visualizer
        """
        # Convert all screen elements (including those in conditionals)
        screen_elements = []
        element_index = 0
        
        for element in screen_node.elements:
            converted_elements = self._convert_screen_element(element, file_path, element_index)
            if converted_elements:
                # Handle both single elements and lists of elements
                if isinstance(converted_elements, list):
                    screen_elements.extend(converted_elements)
                    element_index += len(converted_elements)
                else:
                    screen_elements.append(converted_elements)
                    element_index += 1
        
        # Determine screen type based on elements
        screen_type = "standard"
        has_imagemap = False
        imagemap_ground = None
        imagemap_hover = None
        
        # Check for imagemap
        for element in screen_node.elements:
            if isinstance(element, ImageMapNode):
                screen_type = "imagemap"
                has_imagemap = True
                imagemap_ground = element.ground_image
                imagemap_hover = element.hover_image
                break
            elif isinstance(element, HotspotNode):
                # Hotspots usually indicate imagemap
                screen_type = "imagemap"
                has_imagemap = True
                break
        
        # Check for complex layouts
        if any(isinstance(e, LayoutNode) for e in screen_node.elements):
            screen_type = "complex"
        
        # Create ScreenStructure
        screen_structure = ScreenStructure(
            screen_name=screen_node.screen_name,
            file_path=file_path,
            line_number=screen_node.line_number,
            elements=screen_elements,
            screen_type=screen_type,
            has_imagemap=has_imagemap,
            imagemap_ground=imagemap_ground,
            imagemap_hover=imagemap_hover,
            label_context=None,  # Will be set by caller if needed
            total_elements=len(screen_elements),
            interactive_elements=len([e for e in screen_elements if e.destination])
        )
        
        return screen_structure
    
    def _convert_screen_element(self, element: Any, file_path: str, element_index: int) -> Optional[ScreenElement]:
        """Convert a CSAP screen element to ScreenElement."""
        
        if isinstance(element, TextButtonNode):
            return ScreenElement(
                element_type='textbutton',
                text=element.text,
                coordinates=None,
                destination=element.action.destination if element.action else None,
                action_type=element.action.action_type.lower() if element.action else None,
                file_path=file_path,
                line_number=element.line_number,
                element_index=element_index,
                has_condition=False,
                condition=None
            )
        
        elif isinstance(element, ImageButtonNode):
            return ScreenElement(
                element_type='imagebutton',
                text=None,
                coordinates=None,
                destination=element.action.destination if element.action else None,
                action_type=element.action.action_type.lower() if element.action else None,
                file_path=file_path,
                line_number=element.line_number,
                element_index=element_index,
                has_condition=False,
                condition=None
            )
        
        elif isinstance(element, ButtonNode):
            return ScreenElement(
                element_type='button',
                text=None,
                coordinates=None,
                destination=element.action.destination if element.action else None,
                action_type=element.action.action_type.lower() if element.action else None,
                file_path=file_path,
                line_number=element.line_number,
                element_index=element_index,
                has_condition=False,
                condition=None
            )
        
        elif isinstance(element, HotspotNode):
            return ScreenElement(
                element_type='hotspot',
                text=None,
                coordinates=element.coordinates,
                destination=element.action.destination if element.action else None,
                action_type=element.action.action_type.lower() if element.action else None,
                file_path=file_path,
                line_number=element.line_number,
                element_index=element_index,
                has_condition=False,
                condition=None
            )
        
        elif isinstance(element, ImageMapNode):
            # ImageMap nodes contain interactive elements (hotspots, textbuttons, imagebuttons)
            # Convert all of them to ScreenElements
            converted_elements = []
            for i, interactive_element in enumerate(element.hotspots):
                converted_element = self._convert_screen_element(interactive_element, file_path, element_index + i)
                if converted_element:
                    converted_elements.append(converted_element)
            return converted_elements if converted_elements else None
        
        elif isinstance(element, LayoutNode):
            # Layout nodes contain children - convert the children
            # For now, just convert the first interactive child
            for child in element.children:
                converted_child = self._convert_screen_element(child, file_path, element_index)
                if converted_child:
                    return converted_child
        
        elif isinstance(element, ConditionalElementNode):
            # Conditional elements contain branches, each with body elements
            # Convert all interactive elements from all branches
            converted_elements = []
            for branch in element.branches:
                for i, body_element in enumerate(branch.body):
                    converted_element = self._convert_screen_element(body_element, file_path, element_index + i)
                    if converted_element:
                        # Handle both single elements and lists
                        if isinstance(converted_element, list):
                            converted_elements.extend(converted_element)
                        else:
                            converted_elements.append(converted_element)
            return converted_elements if converted_elements else None
        
        # Unknown element type
        return None
    
    def convert_multiple_screens(self, screen_nodes: List[ScreenNode], file_path: str = "") -> List[ScreenStructure]:
        """Convert multiple CSAP ScreenNodes to ScreenStructures."""
        return [self.convert_screen_node_to_structure(node, file_path) for node in screen_nodes]


# Global instance for easy access
compatibility_adapter = CSAPCompatibilityAdapter()


def convert_csap_to_screen_structure(screen_node: ScreenNode, file_path: str = "") -> ScreenStructure:
    """
    Convenience function to convert CSAP ScreenNode to ScreenStructure.
    
    This is the main integration point for replacing regex parsing.
    """
    return compatibility_adapter.convert_screen_node_to_structure(screen_node, file_path)
