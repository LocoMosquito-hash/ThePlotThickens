"""
CSAP Parser Implementation

The main Custom Screen AST Parser that uses Lark to parse Ren'Py screen
elements and convert them to a structured AST.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from lark import Lark, Transformer, Tree, Token
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedToken
from lark.indenter import Indenter

class RenpyIndenter(Indenter):
    """Custom indenter for Ren'Py screen syntax."""
    NL_type = '_NEWLINE'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4

try:
    from .csap_ast import *
    from .csap_exceptions import *
    from .conditional_blind_parser import ConditionalBlindParser
except ImportError:
    from csap_ast import *
    from csap_exceptions import *
    from conditional_blind_parser import ConditionalBlindParser


class CSAPTransformer(Transformer):
    """Transforms Lark parse tree into CSAP AST nodes."""
    
    def __init__(self):
        super().__init__()
        self.current_line = 1
        self.current_column = 1
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _get_node_location(self, items) -> tuple:
        """Extract line/column information from parse tree items."""
        line, column = self.current_line, self.current_column
        
        for item in items:
            if hasattr(item, 'line'):
                line = item.line
            if hasattr(item, 'column'):
                column = item.column
        
        return line, column
    
    def _extract_string_value(self, token: Token) -> str:
        """Extract string value from quoted token."""
        value = str(token)
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]  # Remove double quotes
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]  # Remove single quotes
        return value
    
    def _extract_number_value(self, token: Token) -> Union[int, float]:
        """Extract numeric value from token."""
        value = str(token)
        try:
            if '.' in value:
                # Handle both "1.5" and ".5" formats
                return float(value)
            else:
                return int(value)
        except ValueError:
            return 0
    
    def _extract_identifier_value(self, token: Token) -> str:
        """Extract identifier/variable name from token."""
        return str(token)
    
    # ========================================================================
    # TOP LEVEL TRANSFORMATIONS
    # ========================================================================
    
    def start(self, items):
        """Transform the root of the parse tree."""
        return items[0]  # Should be a screen_definition
    
    def screen_definition(self, items):
        """Transform screen definition."""
        screen_name = str(items[0])
        line, column = self._get_node_location(items)
        
        # Items[1] should be screen_body (list of elements)
        elements = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        
        return ScreenNode(
            screen_name=screen_name,
            parameters=[],  # No parameters in simple grammar
            elements=elements,
            line_number=line,
            column=column
        )
    
    def screen_name(self, items):
        """Transform screen name."""
        return str(items[0])
    
    def screen_params(self, items):
        """Transform screen parameters."""
        if items and len(items) > 0:
            return items[0]  # param_list
        return []
    
    def param_list(self, items):
        """Transform parameter list."""
        return [str(item) for item in items]
    
    def screen_body(self, items):
        """Transform screen body."""
        # Filter out None values (from screen properties) and keep only actual elements
        elements = []
        for item in items:
            if item is not None and hasattr(item, 'element_type'):
                elements.append(item)
        return elements
    
    # ========================================================================
    # CONDITIONAL TRANSFORMATIONS
    # ========================================================================
    
    def conditional_element(self, items):
        """Transform conditional element."""
        return items[0]  # if_statement
    
    def if_statement(self, items):
        """Transform if statement."""
        line, column = self._get_node_location(items)
        
        condition = items[0]  # conditional_expression
        body = items[1] if len(items) > 1 else []  # conditional_body
        
        return ConditionalElementNode(
            condition=condition,
            body=body,
            line_number=line,
            column=column
        )
    
    def conditional_expression(self, items):
        """Transform conditional expression with support for compound conditions."""
        line, column = self._get_node_location(items)
        
        # For now, just take the first simple_condition and ignore compound logic
        # This handles: variable == value, variable > value, etc.
        # TODO: Full compound condition support later if needed
        first_condition = items[0]  # simple_condition
        
        return first_condition
    
    def simple_condition(self, items):
        """Transform simple condition (variable operator value)."""
        line, column = self._get_node_location(items)
        
        variable = str(items[0])  # IDENTIFIER
        operator = str(items[1])  # comparison_operator  
        value = items[2]         # conditional_value
        
        # Extract value based on type
        if hasattr(value, 'type'):
            if value.type == 'STRING':
                value = self._extract_string_value(value)
            elif value.type in ('NUMBER', 'DECIMAL'):
                value = self._extract_number_value(value)
            elif value.type == 'IDENTIFIER':
                value = self._extract_identifier_value(value)
        else:
            value = str(value)
        
        return ConditionalExpressionNode(
            variable=variable,
            operator=operator,
            value=value,
            line_number=line,
            column=column
        )
    
    def conditional_value(self, items):
        """Transform conditional value."""
        return items[0]  # STRING, NUMBER, DECIMAL, or IDENTIFIER token
    
    def comparison_operator(self, items):
        """Transform comparison operator."""
        if not items:
            return "=="  # Default fallback
        return str(items[0])
    
    def logical_operator(self, items):
        """Transform logical operator."""
        return str(items[0])
    
    def conditional_body(self, items):
        """Transform conditional body."""
        return items  # List of screen elements or add statements
    
    def conditional_body_item(self, items):
        """Transform conditional body item."""
        return items[0]  # screen_element or add_statement
    
    def add_statement(self, items):
        """Transform add statement - parse but ignore for flow analysis."""
        line, column = self._get_node_location(items)
        
        # Extract resource (add_content)
        resource = str(items[0]) if items else ""
        properties = items[1] if len(items) > 1 and isinstance(items[1], list) else []
        
        return AddStatementNode(
            resource=resource,
            properties=properties,
            line_number=line,
            column=column
        )
    
    def add_content(self, items):
        """Transform add content."""
        return str(items[0])  # STRING, IDENTIFIER, or dotted_identifier
    
    def dotted_identifier(self, items):
        """Transform dotted identifier like gui.main_menu_background."""
        return ".".join(str(item) for item in items)
    
    def add_properties(self, items):
        """Transform add properties."""
        return items  # List of PropertyNode objects
    
    def add_property(self, items):
        """Transform add property."""
        line, column = self._get_node_location(items)
        prop_name = str(items[0])
        prop_value = items[1] if len(items) > 1 else ""
        
        # Handle different value types
        if hasattr(prop_value, 'type'):
            if prop_value.type == 'STRING':
                prop_value = self._extract_string_value(prop_value)
            elif prop_value.type in ('NUMBER', 'DECIMAL'):
                prop_value = self._extract_number_value(prop_value)
            elif prop_value.type == 'IDENTIFIER':
                prop_value = self._extract_identifier_value(prop_value)
        else:
            prop_value = str(prop_value)
        
        return PropertyNode(
            property_name=prop_name,
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def screen_property(self, items):
        """Transform screen property (metadata, not an element)."""
        # Screen properties are metadata, return None to filter them out
        return None
    
    def modal_property(self, items):
        """Transform modal property."""
        # This is metadata, not an element - return None to filter out
        return None
    
    def screen_element(self, items):
        """Transform screen element."""
        return items[0]  # textbutton_element, imagebutton_element, or hotspot_element
    
    # ========================================================================
    # TEXTBUTTON TRANSFORMATIONS
    # ========================================================================
    
    def textbutton_element(self, items):
        """Transform textbutton element (enhanced)."""
        return items[0]  # Either textbutton_single_line or textbutton_multi_line
    
    def textbutton_single_line(self, items):
        """Transform single-line textbutton with content (Futagenesis style)."""
        line, column = self._get_node_location(items)
        
        text = items[0]  # Should be processed by STRING token handler
        properties = []
        action = None
        
        # Process textbutton_content items
        for item in items[1:]:
            if isinstance(item, list):  # textbutton_content list
                # Handle list of items
                for sub_item in item:
                    if isinstance(sub_item, PropertyNode):
                        properties.append(sub_item)
                    elif isinstance(sub_item, ActionNode):
                        action = sub_item
            elif isinstance(item, PropertyNode):
                properties.append(item)
            elif isinstance(item, ActionNode):
                action = item
        
        return TextButtonNode(
            text=text,
            properties=properties,
            action=action,
            line_number=line,
            column=column
        )
    
    def textbutton_content(self, items):
        """Transform textbutton content."""
        return items[0]  # Either PropertyNode or ActionNode
    
    def textbutton_mixed_content(self, items):
        """Transform textbutton mixed content (property or action)."""
        return items[0]  # Either PropertyNode or ActionNode
    
    def textbutton_multi_line(self, items):
        """Transform multi-line textbutton."""
        line, column = self._get_node_location(items)
        
        text = items[0]  # Should be processed by STRING token handler
        properties = []
        action = None
        
        for item in items[1:]:
            if isinstance(item, list):  # textbutton_properties
                # Filter to ensure only PropertyNode objects
                for prop in item:
                    if isinstance(prop, PropertyNode):
                        properties.append(prop)
            elif isinstance(item, PropertyNode):
                properties.append(item)
            elif isinstance(item, ActionNode):
                action = item
        
        return TextButtonNode(
            text=text,
            properties=properties,
            action=action,
            line_number=line,
            column=column
        )
    
    def textbutton_properties(self, items):
        """Transform textbutton properties."""
        return items  # List of PropertyNode objects
    
    def textbutton_property(self, items):
        """Transform textbutton property (working version)."""
        line, column = self._get_node_location(items)
        prop_name = items[0]
        prop_value = items[1] if len(items) > 1 else ""
        
        result = PropertyNode(
            property_name=prop_name,
            property_value=prop_value,
            line_number=line,
            column=column
        )
        return result
    
    # Property transformers for textbuttons
    def text_color_property(self, items):
        """Transform text_color property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='text_color',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    def text_size_property(self, items):
        """Transform text_size property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='text_size',
            property_value=self._extract_number_value(items[0]),
            line_number=line,
            column=column
        )
    
    def generic_property(self, items):
        """Transform generic property."""
        line, column = self._get_node_location(items)
        prop_name = str(items[0])
        prop_value = ""
        
        if len(items) > 1:
            if isinstance(items[1], Token):
                if items[1].type in ['ESCAPED_STRING', 'SINGLE_QUOTED_STRING']:
                    prop_value = self._extract_string_value(items[1])
                elif items[1].type == 'NUMBER':
                    prop_value = self._extract_number_value(items[1])
                else:
                    prop_value = str(items[1])
            else:
                prop_value = items[1]
        
        return PropertyNode(
            property_name=prop_name,
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def textbutton_body(self, items):
        """Transform textbutton body."""
        return items
    
    def textbutton_line(self, items):
        """Transform textbutton line."""
        return items[0]
    
    # ========================================================================
    # IMAGEBUTTON TRANSFORMATIONS
    # ========================================================================
    
    def imagebutton_element(self, items):
        """Transform imagebutton element."""
        return items[0]  # Either imagebutton_single_line or imagebutton_multi_line
    
    def imagebutton_single_line(self, items):
        """Transform single-line imagebutton."""
        line, column = self._get_node_location(items)
        
        properties = []
        action = None
        
        for item in items:
            if isinstance(item, list):  # imagebutton_properties
                properties.extend(item)
            elif isinstance(item, ActionNode):
                action = item
        
        return ImageButtonNode(
            properties=properties,
            action=action,
            line_number=line,
            column=column
        )
    
    def imagebutton_multi_line(self, items):
        """Transform multi-line imagebutton."""
        line, column = self._get_node_location(items)
        
        anchor = None
        properties = []
        action = None
        
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:  # anchor
                anchor = item
            elif isinstance(item, list):  # imagebutton_body
                for body_item in item:
                    if isinstance(body_item, PropertyNode):
                        properties.append(body_item)
                    elif isinstance(body_item, ActionNode):
                        action = body_item
        
        return ImageButtonNode(
            anchor=anchor,
            properties=properties,
            action=action,
            line_number=line,
            column=column
        )
    
    def imagebutton_body(self, items):
        """Transform imagebutton body."""
        return items
    
    def imagebutton_line(self, items):
        """Transform imagebutton line."""
        return items[0]
    
    def imagebutton_anchor(self, items):
        """Transform imagebutton anchor."""
        if items and isinstance(items[0], tuple):
            return items[0]
        return None
    
    def imagebutton_properties(self, items):
        """Transform imagebutton properties."""
        return items  # List of PropertyNode objects
    
    def imagebutton_property(self, items):
        """Transform imagebutton property."""
        return items[0]
    
    def idle_property(self, items):
        """Transform idle property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='idle',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    def hover_property(self, items):
        """Transform hover property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='hover',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    # ========================================================================
    # BUTTON TRANSFORMATIONS (Battle of the Bulges style)
    # ========================================================================
    
    def button_element(self, items):
        """Transform generic button element."""
        return items[0]  # button body
    
    def button_body(self, items):
        """Transform button body."""
        line, column = self._get_node_location(items)
        
        properties = []
        action = None
        
        for item in items:
            if isinstance(item, list):  # button_properties
                properties.extend(item)
            elif isinstance(item, PropertyNode):
                properties.append(item)
            elif isinstance(item, ActionNode):
                action = item
        
        return ButtonNode(
            properties=properties,
            action=action,
            line_number=line,
            column=column
        )
    
    def button_property(self, items):
        """Transform button property."""
        return items[0]  # Delegate to specific property transformers
    
    def xysize_property(self, items):
        """Transform xysize property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='xysize',
            property_value=items[0],  # coordinate_tuple
            line_number=line,
            column=column
        )
    
    def xpos_property(self, items):
        """Transform xpos property."""
        line, column = self._get_node_location(items)
        # Handle both numbers and variable references
        value = items[0]
        if hasattr(value, 'type') and value.type == 'IDENTIFIER':
            prop_value = self._extract_identifier_value(value)
        else:
            prop_value = self._extract_number_value(value)
            
        return PropertyNode(
            property_name='xpos',
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def ypos_property(self, items):
        """Transform ypos property."""
        line, column = self._get_node_location(items)
        # Handle both numbers and variable references
        value = items[0]
        if hasattr(value, 'type') and value.type == 'IDENTIFIER':
            prop_value = self._extract_identifier_value(value)
        else:
            prop_value = self._extract_number_value(value)
            
        return PropertyNode(
            property_name='ypos',
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    # ========================================================================
    # HOTSPOT TRANSFORMATIONS
    # ========================================================================
    
    def hotspot_element(self, items):
        """Transform hotspot element."""
        line, column = self._get_node_location(items)
        
        coordinates = items[0]  # Should be coordinate_tuple
        action = items[1] if len(items) > 1 else None
        
        return HotspotNode(
            coordinates=coordinates,
            action=action,
            line_number=line,
            column=column
        )
    
    def imagemap_element(self, items):
        """Transform imagemap element."""
        line, column = self._get_node_location(items)
        
        # imagemap_body contains properties and hotspots
        imagemap_body = items[0] if items else []
        
        # Extract ground and hover images from properties
        ground_image = None
        hover_image = None
        hotspots = []
        
        if isinstance(imagemap_body, list):
            for item in imagemap_body:
                if isinstance(item, dict) and 'property_name' in item:
                    # Handle ground/hover properties
                    if item['property_name'] == 'ground':
                        ground_image = item['property_value']
                    elif item['property_name'] == 'hover':
                        hover_image = item['property_value']
                elif isinstance(item, HotspotNode):
                    # Handle hotspot elements
                    hotspots.append(item)
        
        return ImageMapNode(
            ground_image=ground_image or "",
            hover_image=hover_image or "",
            hotspots=hotspots,
            line_number=line,
            column=column
        )
    
    def imagemap_body(self, items):
        """Transform imagemap body."""
        return items  # Return list of properties and hotspots
    
    def imagemap_property(self, items):
        """Transform imagemap property."""
        return items[0]  # Return the ground_property or hover_property
    
    def ground_property(self, items):
        """Transform ground property."""
        return {
            'property_name': 'ground',
            'property_value': self._extract_string_value(items[0]) if items else ""
        }
    
    def hover_property(self, items):
        """Transform hover property."""
        return {
            'property_name': 'hover',
            'property_value': self._extract_string_value(items[0]) if items else ""
        }
    
    def alpha_property(self, items):
        """Transform alpha property."""
        return {
            'property_name': 'alpha',
            'property_value': str(items[0]) == 'True' if items else False
        }
    
    def coordinate_tuple(self, items):
        """Transform coordinate tuple with mixed types."""
        # Extract values from items, handling different types
        coords = []
        for item in items:
            if hasattr(item, 'type'):
                if item.type == 'STRING':
                    coords.append(self._extract_string_value(item))
                elif item.type in ('NUMBER', 'DECIMAL'):
                    coords.append(self._extract_number_value(item))
                elif item.type == 'IDENTIFIER':
                    coords.append(self._extract_identifier_value(item))
                elif item.type == 'BOOLEAN':
                    coords.append(str(item) == 'True')
                else:
                    coords.append(str(item))
            elif isinstance(item, (int, float, str, bool)):
                coords.append(item)
            else:
                coords.append(str(item))
        
        return tuple(coords)
    
    def tuple_item(self, items):
        """Transform tuple item."""
        return items[0]  # STRING, NUMBER, DECIMAL, IDENTIFIER, or BOOLEAN
    
    # ========================================================================
    # ACTION TRANSFORMATIONS
    # ========================================================================
    
    def action_statement(self, items):
        """Transform action statement."""
        return items[0]  # action_list, jump_action, or call_action
    
    def action_list(self, items):
        """Transform list-wrapped action: [Jump("dest")]"""
        return items[0]  # The jump_action or call_action inside the list
    
    def jump_action(self, items):
        """Transform jump action."""
        line, column = self._get_node_location(items)
        destination = self._extract_string_value(items[0])
        
        return ActionNode(
            action_type='Jump',
            destination=destination,
            line_number=line,
            column=column
        )
    
    def call_action(self, items):
        """Transform call action."""
        line, column = self._get_node_location(items)
        destination = self._extract_string_value(items[0])
        
        return ActionNode(
            action_type='Call',
            destination=destination,
            line_number=line,
            column=column
        )
    
    # ========================================================================
    # PROPERTY TRANSFORMATIONS
    # ========================================================================
    
    def textbutton_property(self, items):
        """Transform textbutton property."""
        return items[0]
    
    def imagebutton_property(self, items):
        """Transform imagebutton property."""
        return items[0]
    
    def text_color_prop(self, items):
        """Transform text_color property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='text_color',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    def idle_prop(self, items):
        """Transform idle property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='idle',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    def hover_prop(self, items):
        """Transform hover property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='hover',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    # Add more property transformations as needed...
    
    # ========================================================================
    # LITERAL TRANSFORMATIONS
    # ========================================================================
    
    def string_literal(self, items):
        """Transform string literal."""
        return items[0]  # Token
    
    def list_literal(self, items):
        """Transform list literal."""
        if items:
            return items[0]  # list_items
        return []
    
    def list_items(self, items):
        """Transform list items."""
        result = []
        for item in items:
            if isinstance(item, Token):
                if item.type == 'ESCAPED_STRING' or item.type == 'SINGLE_QUOTED_STRING':
                    result.append(self._extract_string_value(item))
                elif item.type == 'NUMBER':
                    result.append(self._extract_number_value(item))
            else:
                result.append(item)
        return result
    
    def list_item(self, items):
        """Transform list item."""
        return items[0]
    
    # Terminal token handlers (following Lark best practices)
    def STRING(self, token):
        """Handle STRING tokens."""
        return self._extract_string_value(token)
    
    def NUMBER(self, token):
        """Handle NUMBER tokens."""
        return self._extract_number_value(token)
    
    def BOOLEAN(self, token):
        """Handle BOOLEAN tokens."""
        return str(token) == 'True'
    
    def IDENTIFIER(self, token):
        """Handle IDENTIFIER tokens."""
        return str(token)
    
    # ========================================================================
    # MISSING PROPERTY TRANSFORMERS
    # ========================================================================
    
    def textbutton_specific_property(self, items):
        """Transform textbutton specific property."""
        return items[0]  # Delegate to specific property transformers
    
    def generic_property(self, items):
        """Transform generic property."""
        line, column = self._get_node_location(items)
        prop_name = str(items[0])  # property_name
        prop_value = items[1] if len(items) > 1 else ""
        
        # Handle different value types
        if hasattr(prop_value, 'type'):
            if prop_value.type == 'STRING':
                prop_value = self._extract_string_value(prop_value)
            elif prop_value.type in ('NUMBER', 'DECIMAL'):
                prop_value = self._extract_number_value(prop_value)
            elif prop_value.type == 'IDENTIFIER':
                prop_value = self._extract_identifier_value(prop_value)
        else:
            prop_value = str(prop_value)
        
        return PropertyNode(
            property_name=prop_name,
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def property_name(self, items):
        """Transform property name."""
        return str(items[0])
    
    def PROPERTY_IDENTIFIER(self, token):
        """Handle PROPERTY_IDENTIFIER tokens."""
        return str(token)
    
    def xalign_property(self, items):
        """Transform xalign property."""
        line, column = self._get_node_location(items)
        value = items[0]
        if hasattr(value, 'type') and value.type == 'IDENTIFIER':
            prop_value = self._extract_identifier_value(value)
        else:
            prop_value = self._extract_number_value(value)
        return PropertyNode(
            property_name='xalign',
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def yalign_property(self, items):
        """Transform yalign property."""
        line, column = self._get_node_location(items)
        value = items[0]
        if hasattr(value, 'type') and value.type == 'IDENTIFIER':
            prop_value = self._extract_identifier_value(value)
        else:
            prop_value = self._extract_number_value(value)
        return PropertyNode(
            property_name='yalign',
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def xoffset_property(self, items):
        """Transform xoffset property."""
        line, column = self._get_node_location(items)
        value = items[0]
        if hasattr(value, 'type') and value.type == 'IDENTIFIER':
            prop_value = self._extract_identifier_value(value)
        else:
            prop_value = self._extract_number_value(value)
        return PropertyNode(
            property_name='xoffset',
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def yoffset_property(self, items):
        """Transform yoffset property."""
        line, column = self._get_node_location(items)
        value = items[0]
        if hasattr(value, 'type') and value.type == 'IDENTIFIER':
            prop_value = self._extract_identifier_value(value)
        else:
            prop_value = self._extract_number_value(value)
        return PropertyNode(
            property_name='yoffset',
            property_value=prop_value,
            line_number=line,
            column=column
        )


class CSAPParser:
    """Main CSAP parser class."""
    
    def __init__(self):
        """Initialize the parser with the Lark grammar."""
        self.grammar_path = Path(__file__).parent / "grammars" / "enhanced_screen.lark"
        self.conditional_blind_parser = ConditionalBlindParser()  # Fallback parser
        
        if not self.grammar_path.exists():
            raise CSAPGrammarError(f"Grammar file not found: {self.grammar_path}")
        
        try:
            self.parser = Lark.open(str(self.grammar_path), parser='earley')
            self.transformer = CSAPTransformer()
        except Exception as e:
            raise CSAPGrammarError(f"Failed to load grammar: {e}")
    
    def parse_screen_text(self, screen_text: str, filename: str = "<string>") -> ScreenNode:
        """
        Parse screen text and return a ScreenNode AST.
        
        Args:
            screen_text: The screen definition text to parse
            filename: Optional filename for error reporting
            
        Returns:
            ScreenNode: Parsed screen AST
            
        Raises:
            CSAPParseError: If parsing fails
        """
        try:
            # Try full CSAP parsing first
            tree = self.parser.parse(screen_text)
            
            # Transform to AST
            ast_node = self.transformer.transform(tree)
            
            if not isinstance(ast_node, ScreenNode):
                raise CSAPTransformError("Expected ScreenNode from transformation")
            
            # Validate the AST
            validation_errors = ast_node.validate()
            if validation_errors:
                raise CSAPValidationError(
                    f"Screen validation failed: {'; '.join(validation_errors)}",
                    validation_type="semantic"
                )
            
            # Check if CSAP found any interactive elements
            # If not, try conditional-blind fallback for better coverage
            interactive_elements = ast_node.get_interactive_elements()
            if len(interactive_elements) == 0:
                # Try conditional-blind fallback to see if it finds more elements
                try:
                    fallback_node = self._conditional_blind_fallback(screen_text, filename)
                    fallback_interactive = fallback_node.get_interactive_elements()
                    
                    if len(fallback_interactive) > 0:
                        print(f"[CSAP FALLBACK] Full CSAP found 0 elements, fallback found {len(fallback_interactive)} - using fallback")
                        return fallback_node
                except Exception:
                    # Fallback failed, continue with original CSAP result
                    pass
            
            return ast_node
            
        except (LarkError, CSAPError) as e:
            # Try conditional-blind parsing as fallback
            try:
                return self._conditional_blind_fallback(screen_text, filename)
            except Exception:
                # If fallback also fails, raise original error
                if isinstance(e, LarkError):
                    # Convert Lark errors to CSAP errors
                    line = getattr(e, 'line', None)
                    column = getattr(e, 'column', None)
                    
                    if isinstance(e, UnexpectedToken):
                        expected = ', '.join(e.expected) if hasattr(e, 'expected') else None
                        raise CSAPParseError(
                            f"Unexpected token: {e.token}",
                            line=line,
                            column=column,
                            expected=expected,
                            context=screen_text.split('\n')[line-1] if line else None
                        )
                    elif isinstance(e, UnexpectedInput):
                        raise CSAPParseError(
                            f"Unexpected input: {str(e)}",
                            line=line,
                            column=column,
                            context=screen_text.split('\n')[line-1] if line else None
                        )
                    else:
                        raise CSAPParseError(f"Parse error: {str(e)}")
                else:
                    # Re-raise CSAP errors
                    raise
    
    def _conditional_blind_fallback(self, screen_text: str, filename: str = "<string>") -> ScreenNode:
        """
        Fallback parser that ignores conditionals and extracts all interactive elements.
        
        This is used when full CSAP parsing fails due to complex conditionals.
        It extracts all textbuttons/imagebuttons/hotspots with Jump/Call actions.
        """
        # Extract screen name
        screen_name_match = re.search(r'screen\s+(\w+)', screen_text)
        screen_name = screen_name_match.group(1) if screen_name_match else "unknown"
        
        # Use conditional-blind parser to get elements
        simple_elements = self.conditional_blind_parser.parse_screen_text(screen_text)
        
        # Convert to CSAP AST nodes
        csap_elements = []
        for simple_elem in simple_elements:
            if simple_elem.element_type == 'textbutton':
                # Create TextButtonNode
                action = ActionNode(
                    action_type=simple_elem.action_type,
                    destination=simple_elem.destination,
                    line_number=simple_elem.line_number
                )
                
                textbutton = TextButtonNode(
                    text=simple_elem.text,
                    action=action,
                    line_number=simple_elem.line_number
                )
                csap_elements.append(textbutton)
                
            elif simple_elem.element_type == 'imagebutton':
                # Create ImageButtonNode
                action = ActionNode(
                    action_type=simple_elem.action_type,
                    destination=simple_elem.destination,
                    line_number=simple_elem.line_number
                )
                
                imagebutton = ImageButtonNode(
                    action=action,
                    line_number=simple_elem.line_number
                )
                csap_elements.append(imagebutton)
                
            elif simple_elem.element_type == 'hotspot':
                # Create HotspotNode
                action = ActionNode(
                    action_type=simple_elem.action_type,
                    destination=simple_elem.destination,
                    line_number=simple_elem.line_number
                )
                
                hotspot = HotspotNode(
                    coordinates=(0, 0, 0, 0),  # Dummy coordinates
                    action=action,
                    line_number=simple_elem.line_number
                )
                csap_elements.append(hotspot)
        
        # Create ScreenNode
        screen_node = ScreenNode(
            screen_name=screen_name,
            elements=csap_elements,
            line_number=1
        )
        
        return screen_node
    
    def parse_screen_file(self, file_path: Union[str, Path]) -> ScreenNode:
        """
        Parse a .rpy file containing a screen definition.
        
        Args:
            file_path: Path to the .rpy file
            
        Returns:
            ScreenNode: Parsed screen AST
            
        Raises:
            CSAPError: If file cannot be read or parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise CSAPError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                raise CSAPError(f"Failed to read file {file_path}: {e}")
        except Exception as e:
            raise CSAPError(f"Failed to read file {file_path}: {e}")
        
        return self.parse_screen_text(content, str(file_path))
    
    def validate_grammar(self) -> bool:
        """
        Validate that the grammar file is syntactically correct.
        
        Returns:
            bool: True if grammar is valid
            
        Raises:
            CSAPGrammarError: If grammar is invalid
        """
        try:
            # Try to parse a minimal valid screen
            test_screen = '''
screen test_screen:
    textbutton "Test" action Jump("test")
'''
            self.parse_screen_text(test_screen)
            return True
        except Exception as e:
            raise CSAPGrammarError(f"Grammar validation failed: {e}")
