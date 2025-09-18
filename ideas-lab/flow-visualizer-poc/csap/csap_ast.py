"""
CSAP AST Node Classes

Defines the Abstract Syntax Tree node classes for representing
parsed Ren'Py screen elements with full type safety and metadata.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod


@dataclass
class CSAPNode(ABC):
    """Base class for all CSAP AST nodes."""
    line_number: int = 0
    column: int = 0
    source_text: str = ""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        pass
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate node semantics. Returns list of error messages."""
        pass


@dataclass
class PropertyNode(CSAPNode):
    """Represents a property assignment (e.g., text_color "#EFEFEF")."""
    property_name: str = ""
    property_value: Union[str, int, float, bool, List[Any]] = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'property',
            'name': self.property_name,
            'value': self.property_value,
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = []
        if not self.property_name:
            errors.append("Property name cannot be empty")
        return errors


@dataclass
class ActionNode(CSAPNode):
    """Represents an action statement (Jump or Call)."""
    action_type: str = ""  # 'Jump' or 'Call'
    destination: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'action',
            'action_type': self.action_type.lower(),
            'destination': self.destination,
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = []
        if self.action_type not in ['Jump', 'Call']:
            errors.append(f"Invalid action type: {self.action_type}")
        if not self.destination:
            errors.append("Action destination cannot be empty")
        return errors


@dataclass
class ScreenElementNode(CSAPNode):
    """Base class for all screen element nodes."""
    element_type: str = ""
    properties: List[PropertyNode] = field(default_factory=list)
    action: Optional[ActionNode] = None
    
    def get_property(self, name: str) -> Optional[PropertyNode]:
        """Get property by name."""
        for prop in self.properties:
            if prop.property_name == name:
                return prop
        return None
    
    def get_property_value(self, name: str, default: Any = None) -> Any:
        """Get property value by name, with default."""
        prop = self.get_property(name)
        return prop.property_value if prop else default
    
    def validate(self) -> List[str]:
        errors = []
        
        # Validate properties
        for prop in self.properties:
            errors.extend(prop.validate())
        
        # Validate action
        if self.action:
            errors.extend(self.action.validate())
        
        return errors


@dataclass
class TextButtonNode(ScreenElementNode):
    """Represents a textbutton element."""
    text: str = ""
    
    def __post_init__(self):
        self.element_type = 'textbutton'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'textbutton',
            'text': self.text,
            'properties': [prop.to_dict() for prop in self.properties],
            'action': self.action.to_dict() if self.action else None,
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = super().validate()
        if not self.text:
            errors.append("TextButton text cannot be empty")
        return errors


@dataclass  
class ImageButtonNode(ScreenElementNode):
    """Represents an imagebutton element."""
    anchor: Optional[Tuple[float, float]] = None
    
    def __post_init__(self):
        self.element_type = 'imagebutton'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'imagebutton',
            'anchor': self.anchor,
            'properties': [prop.to_dict() for prop in self.properties],
            'action': self.action.to_dict() if self.action else None,
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = super().validate()
        
        # Check for required properties
        if not self.get_property('idle'):
            errors.append("ImageButton must have 'idle' property")
        
        # Validate anchor if present
        if self.anchor:
            if len(self.anchor) != 2:
                errors.append("ImageButton anchor must have exactly 2 coordinates")
            for coord in self.anchor:
                if not isinstance(coord, (int, float)) or coord < 0:
                    errors.append("ImageButton anchor coordinates must be non-negative numbers")
        
        return errors


@dataclass
class ButtonNode(ScreenElementNode):
    """Represents a generic button element (Battle of the Bulges style)."""
    
    def __post_init__(self):
        self.element_type = 'button'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'button',
            'properties': [prop.to_dict() for prop in self.properties],
            'action': self.action.to_dict() if self.action else None,
            'line': self.line_number
        }


@dataclass
class HotspotNode(ScreenElementNode):
    """Represents a hotspot element."""
    coordinates: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (x, y, width, height)
    
    def __post_init__(self):
        self.element_type = 'hotspot'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'hotspot',
            'coordinates': self.coordinates,
            'action': self.action.to_dict() if self.action else None,
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = super().validate()
        
        if len(self.coordinates) != 4:
            errors.append("Hotspot must have exactly 4 coordinates (x, y, width, height)")
        
        for i, coord in enumerate(self.coordinates):
            if not isinstance(coord, int) or coord < 0:
                coord_names = ['x', 'y', 'width', 'height']
                errors.append(f"Hotspot {coord_names[i]} must be a non-negative integer")
        
        if not self.action:
            errors.append("Hotspot must have an action")
        
        return errors


@dataclass
class ImageMapNode(CSAPNode):
    """Represents an imagemap container."""
    ground_image: Optional[str] = None
    hover_image: Optional[str] = None
    hotspots: List[HotspotNode] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'imagemap',
            'ground_image': self.ground_image,
            'hover_image': self.hover_image,
            'hotspots': [hotspot.to_dict() for hotspot in self.hotspots],
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = []
        
        # Validate hotspots
        for hotspot in self.hotspots:
            errors.extend(hotspot.validate())
        
        return errors


@dataclass
class LayoutNode(CSAPNode):
    """Represents a layout container (vbox, hbox)."""
    layout_type: str = ""  # 'vbox', 'hbox'
    properties: List[PropertyNode] = field(default_factory=list)
    children: List[ScreenElementNode] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'layout',
            'layout_type': self.layout_type,
            'properties': [prop.to_dict() for prop in self.properties],
            'children': [child.to_dict() for child in self.children],
            'line': self.line_number
        }
    
    def validate(self) -> List[str]:
        errors = []
        
        if self.layout_type not in ['vbox', 'hbox']:
            errors.append(f"Invalid layout type: {self.layout_type}")
        
        # Validate properties
        for prop in self.properties:
            errors.extend(prop.validate())
        
        # Validate children
        for child in self.children:
            errors.extend(child.validate())
        
        return errors


@dataclass
class ScreenNode(CSAPNode):
    """Represents a complete screen definition."""
    screen_name: str = ""
    parameters: List[str] = field(default_factory=list)
    elements: List[Union[ScreenElementNode, ImageMapNode, LayoutNode]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': 'screen',
            'name': self.screen_name,
            'parameters': self.parameters,
            'elements': [element.to_dict() for element in self.elements],
            'line': self.line_number,
            'total_elements': len(self.elements),
            'interactive_elements': len([e for e in self.elements if isinstance(e, ScreenElementNode) and e.action])
        }
    
    def get_interactive_elements(self) -> List[ScreenElementNode]:
        """Get all elements that have actions (clickable elements)."""
        interactive = []
        
        def collect_interactive(elements):
            for element in elements:
                if isinstance(element, ScreenElementNode) and element.action:
                    interactive.append(element)
                elif isinstance(element, ImageMapNode):
                    interactive.extend(element.hotspots)
                elif isinstance(element, LayoutNode):
                    collect_interactive(element.children)
        
        collect_interactive(self.elements)
        return interactive
    
    def validate(self) -> List[str]:
        errors = []
        
        if not self.screen_name:
            errors.append("Screen name cannot be empty")
        
        # Validate all elements
        for element in self.elements:
            errors.extend(element.validate())
        
        # Check for duplicate element types that might conflict
        element_types = {}
        for element in self.elements:
            if isinstance(element, ScreenElementNode):
                elem_type = element.element_type
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        return errors
