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
        # Grammar: SCREEN IDENTIFIER screen_params? ":" _NEWLINE _INDENT screen_body _DEDENT
        # items[0] = SCREEN token
        # items[1] = IDENTIFIER (screen name)
        # items[2] = screen_params (if present) or screen_body (list)
        # items[3] = screen_body (list) if screen_params is present
        
        # Extract screen name (skip SCREEN token at items[0])
        screen_name = str(items[1])
        line, column = self._get_node_location(items)
        
        # Determine if screen_params is present
        if len(items) == 4:
            # Has screen_params: [SCREEN, name, screen_params, screen_body]
            elements = items[3] if isinstance(items[3], list) else []
        elif len(items) == 3:
            # No screen_params: [SCREEN, name, screen_body]
            elements = items[2] if isinstance(items[2], list) else []
        else:
            elements = []
        
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
        # Filter out None values, newlines (Token objects), and keep only actual elements
        # Include ScreenElementNode (with element_type), ImageMapNode, LayoutNode, and ConditionalElementNode
        elements = []
        for item in items:
            if item is not None and not isinstance(item, Token):
                # Include elements with element_type attribute, or specific node types
                if (hasattr(item, 'element_type') or 
                    isinstance(item, (ImageMapNode, LayoutNode, ConditionalElementNode))):
                    elements.append(item)
        
        return elements
    
    def screen_body_item(self, items):
        """Transform screen body item."""
        return items[0] if items else None
    
    # ========================================================================
    # CONDITIONAL TRANSFORMATIONS
    # ========================================================================
    
    def conditional_element(self, items):
        """Transform conditional element."""
        result = items[0]  # if_statement
        return result
    
    def if_statement(self, items):
        """Transform if statement with elif and else support."""
        line, column = self._get_node_location(items)
        
        # Parse structure from grammar: IF conditional_expression ":" _NEWLINE _INDENT conditional_body _DEDENT elif* else*
        # items[0] = IF token
        # items[1] = conditional_expression (ConditionalExpressionNode)
        # items[2] = conditional_body (list)
        # items[3+] = elif_statement or else_statement (ConditionalBranch)
        branches = []
        
        # First branch: if
        if_condition = items[1]  # conditional_expression
        if_body = items[2] if len(items) > 2 and isinstance(items[2], list) else []
        
        
        if_branch = ConditionalBranch(
            condition=if_condition,
            body=if_body,
            branch_type="if",
            line_number=line,
            column=column
        )
        branches.append(if_branch)
        
        # Process remaining items (elif and else branches)
        for i in range(3, len(items)):
            item = items[i]
            if isinstance(item, ConditionalBranch):
                branches.append(item)
        
        result = ConditionalElementNode(
            branches=branches,
            line_number=line,
            column=column
        )
        return result
    
    def elif_statement(self, items):
        """Transform elif statement."""
        line, column = self._get_node_location(items)
        
        # Parse structure from grammar: ELIF conditional_expression ":" _NEWLINE _INDENT conditional_body _DEDENT
        # items[0] = ELIF token
        # items[1] = conditional_expression (ConditionalExpressionNode)
        # items[2] = conditional_body (list)
        condition = items[1]  # conditional_expression
        body = items[2] if len(items) > 2 and isinstance(items[2], list) else []  # conditional_body
        
        return ConditionalBranch(
            condition=condition,
            body=body,
            branch_type="elif",
            line_number=line,
            column=column
        )
    
    def else_statement(self, items):
        """Transform else statement."""
        line, column = self._get_node_location(items)
        
        # Parse structure from grammar: ELSE ":" _NEWLINE _INDENT conditional_body _DEDENT
        # items[0] = ELSE token
        # items[1] = conditional_body (list)
        body = items[1] if len(items) > 1 and isinstance(items[1], list) else []  # conditional_body
        
        return ConditionalBranch(
            condition=None,
            body=body,
            branch_type="else",
            line_number=line,
            column=column
        )
    
    def conditional_body(self, items):
        """Transform conditional body (list of screen elements)."""
        # items is a list from the + operator in grammar: (conditional_body_item _NEWLINE?)+
        # Each item should already be transformed by conditional_body_item
        # Filter out None values and newlines
        result = []
        for item in items:
            if item is not None and not (hasattr(item, 'type') and item.type == '_NEWLINE'):
                result.append(item)
        return result
    
    def conditional_body_item(self, items):
        """Transform conditional body item."""
        return items[0]  # Either screen_element or add_statement
    
    def conditional_expression(self, items):
        """Transform conditional expression with support for compound conditions."""
        # items[0] is condition_term, rest are (logical_operator, condition_term) pairs
        # For flow visualization, we treat the entire expression as opaque metadata
        if items and len(items) > 0:
            first_condition = items[0]  # condition_term
            return first_condition
        return None
    
    def condition_term(self, items):
        """Transform condition term (with optional NOT)."""
        # items: [NOT?, condition_atom]
        # Return the condition_atom for now (we don't evaluate, just store metadata)
        if items:
            return items[-1]  # Return the condition_atom (last item)
        return None
    
    def condition_atom(self, items):
        """Transform condition atom (function_call, comparison, identifier, etc)."""
        # Return whatever was matched
        return items[0] if items else None
    
    def function_call(self, items):
        """Transform function call in conditional."""
        # items: [function_name, args...]
        # For metadata purposes, create a simple representation
        line, column = self._get_node_location(items)
        function_name = str(items[0])
        # Return a ConditionalExpressionNode with the function name as variable
        return ConditionalExpressionNode(
            variable=function_name,
            operator="()",  # Indicate it's a function call
            value="",
            line_number=line,
            column=column
        )
    
    def comparison(self, items):
        """Transform comparison expression."""
        # items: [identifier, operator, value]
        line, column = self._get_node_location(items)
        
        variable = str(items[0])  # Token with variable name
        
        # operator might be a Token (inlined) or transformed value
        if hasattr(items[1], 'type'):
            operator = str(items[1])  # It's a Token
        else:
            operator = items[1]  # Already transformed
        
        # value might be a Token or transformed value
        if hasattr(items[2], 'type'):
            # Extract value based on type
            if items[2].type in ['STRING', 'ESCAPED_STRING', 'SINGLE_QUOTED_STRING']:
                value = self._extract_string_value(items[2])
            elif items[2].type in ('NUMBER', 'DECIMAL'):
                value = self._extract_number_value(items[2])
            elif items[2].type == 'IDENTIFIER':
                value = self._extract_identifier_value(items[2])
            else:
                value = str(items[2])
        else:
            value = items[2]  # Already transformed
        
        return ConditionalExpressionNode(
            variable=variable,
            operator=operator,
            value=value,
            line_number=line,
            column=column
        )
    
    def conditional_value(self, items):
        """Transform conditional value."""
        if not items:
            return ""
        
        value = items[0]
        
        # Extract value based on type
        if hasattr(value, 'type'):
            if value.type in ['STRING', 'ESCAPED_STRING', 'SINGLE_QUOTED_STRING']:
                return self._extract_string_value(value)
            elif value.type in ('NUMBER', 'DECIMAL'):
                return self._extract_number_value(value)
            elif value.type == 'IDENTIFIER':
                return self._extract_identifier_value(value)
        
        return str(value)
    
    def comparison_operator(self, items):
        """Transform comparison operator."""
        # The comparison_operator in the grammar is a choice of terminals
        # Lark doesn't create a tree node for simple choices, so this might not be called
        # But if it is, just return the token value
        if not items:
            return "=="
        return str(items[0]) if items else "=="
    
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
    
    def focus_mask_property(self, items):
        """Transform focus_mask property."""
        line, column = self._get_node_location(items)
        # items[0] is a BOOLEAN token (True/False)
        prop_value = str(items[0]).strip() if items else "True"
        return PropertyNode(
            property_name='focus_mask',
            property_value=prop_value,
            line_number=line,
            column=column
        )
    
    def hover_sound_property(self, items):
        """Transform hover_sound property."""
        line, column = self._get_node_location(items)
        # items[0] is either a STRING token or an IDENTIFIER (for sound variables)
        if items and isinstance(items[0], Token):
            if items[0].type in ['ESCAPED_STRING', 'STRING']:
                prop_value = self._extract_string_value(items[0])
            else:
                # IDENTIFIER like sound_menu_button
                prop_value = str(items[0])
        else:
            prop_value = str(items[0]) if items else ""
        
        return PropertyNode(
            property_name='hover_sound',
            property_value=prop_value,
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
        """Transform imagebutton body - filter out tokens, keep only items."""
        return [item for item in items if not isinstance(item, Token)]
    
    def imagebutton_body_item(self, items):
        """Transform imagebutton body item."""
        return items[0] if items else None
    
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
        # items[0] = IDLE token
        # items[1] = string_expression
        value = items[1] if len(items) > 1 else ""
        # Convert string_expression to a simple string (flatten it)
        if isinstance(value, str):
            property_value = value
        else:
            property_value = str(value)
        
        return PropertyNode(
            property_name='idle',
            property_value=property_value,
            line_number=line,
            column=column
        )
    
    def hover_property(self, items):
        """Transform hover property."""
        line, column = self._get_node_location(items)
        # items[0] = HOVER token
        # items[1] = string_expression
        value = items[1] if len(items) > 1 else ""
        # Convert string_expression to a simple string (flatten it)
        if isinstance(value, str):
            property_value = value
        else:
            property_value = str(value)
        
        return PropertyNode(
            property_name='hover',
            property_value=property_value,
            line_number=line,
            column=column
        )
    
    def auto_property(self, items):
        """Transform auto property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='auto',
            property_value=self._extract_string_value(items[0]),
            line_number=line,
            column=column
        )
    
    def at_property(self, items):
        """Transform at property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='at',
            property_value=self._extract_identifier_value(items[0]),
            line_number=line,
            column=column
        )
    
    def zorder_property(self, items):
        """Transform zorder property."""
        line, column = self._get_node_location(items)
        return PropertyNode(
            property_name='zorder',
            property_value=int(items[0]),
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
        
        # items[0] = HOTSPOT token
        # items[1] = coordinate_tuple
        # items[2] = action_statement
        coordinates = items[1] if len(items) > 1 else None
        action = items[2] if len(items) > 2 else None
        
        return HotspotNode(
            coordinates=coordinates,
            action=action,
            line_number=line,
            column=column
        )
    
    def imagemap_element(self, items):
        """Transform imagemap element."""
        line, column = self._get_node_location(items)
        
        # imagemap_body contains properties, hotspots, and conditionals
        # items[0] = IMAGEMAP token
        # items[1] = imagemap_body (list)
        imagemap_body = items[1] if len(items) > 1 else []
        
        # Extract ground, idle, and hover images from properties
        ground_image = None
        idle_image = None
        hover_image = None
        hotspots = []
        
        if isinstance(imagemap_body, list):
            for item in imagemap_body:
                if isinstance(item, dict) and 'property_name' in item:
                    # Handle image properties (dictionary format)
                    if item['property_name'] == 'ground':
                        ground_image = item['property_value']
                    elif item['property_name'] == 'idle':
                        idle_image = item['property_value']
                    elif item['property_name'] == 'hover':
                        hover_image = item['property_value']
                elif isinstance(item, PropertyNode):
                    # Handle image properties (PropertyNode format)
                    if item.property_name == 'ground':
                        ground_image = item.property_value
                    elif item.property_name == 'idle':
                        idle_image = item.property_value
                    elif item.property_name == 'hover':
                        hover_image = item.property_value
                elif isinstance(item, (HotspotNode, TextButtonNode, ImageButtonNode)):
                    # Handle interactive elements (hotspots, textbuttons, imagebuttons)
                    hotspots.append(item)
                elif isinstance(item, ConditionalElementNode):
                    # Handle conditional blocks containing interactive elements
                    # Extract elements from all branches (if/elif/else)
                    for branch in item.branches:
                        for body_item in branch.body:
                            if isinstance(body_item, (HotspotNode, TextButtonNode, ImageButtonNode)):
                                hotspots.append(body_item)
        
        return ImageMapNode(
            ground_image=ground_image or idle_image or "",
            hover_image=hover_image or "",
            hotspots=hotspots,
            line_number=line,
            column=column
        )
    
    def imagemap_body(self, items):
        """Transform imagemap body."""
        # Filter out None values, newline tokens, and flatten the list
        return [item for item in items if item is not None and not isinstance(item, Token)]
    
    def imagemap_line(self, items):
        """Transform imagemap line."""
        return items[0] if items else None
    
    def imagemap_property(self, items):
        """Transform imagemap property."""
        return items[0]  # Return the ground_property or hover_property
    
    def ground_property(self, items):
        """Transform ground property."""
        # items[0] = GROUND token
        # items[1] = string_expression
        value = items[1] if len(items) > 1 else ""
        # Convert string_expression to a simple string (flatten it)
        if isinstance(value, str):
            property_value = value
        else:
            property_value = str(value)
        
        return {
            'property_name': 'ground',
            'property_value': property_value
        }
    
    # Note: hover_property is already defined above for imagebuttons (returns PropertyNode)
    # This duplicate would override it. Removing to avoid conflict.
    
    def string_expression(self, items):
        """Transform string expression (supports concatenation)."""
        # items are string_term values, possibly with '+' tokens
        # For metadata purposes, just concatenate them as a description
        if not items:
            return ""
        
        # Filter out '+' tokens and concatenate the terms
        terms = [item for item in items if not isinstance(item, Token) or item.type != 'OP']
        if len(terms) == 1:
            return terms[0]
        else:
            # Multiple terms - represent as concatenation for metadata
            return " + ".join(str(term) for term in terms)
    
    def string_term(self, items):
        """Transform string term."""
        if not items:
            return ""
        
        value = items[0]
        if isinstance(value, Token):
            if value.type in ['STRING', 'ESCAPED_STRING', 'SINGLE_QUOTED_STRING']:
                return self._extract_string_value(value)
            elif value.type == 'IDENTIFIER':
                return self._extract_identifier_value(value)
            else:
                return str(value)
        return str(value)
    
    def text_element(self, items):
        """Transform text element (non-interactive, ignore for flow analysis)."""
        # Text elements are just for display, not part of navigation flow
        return None
    
    def text_property(self, items):
        """Transform text property."""
        return items[0] if items else None
    
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
        # items may contain action_keyword (None) and action_sequence
        # Filter out None values and get the action_sequence
        actions = [item for item in items if item is not None]
        return actions[0] if actions else None
    
    def action_keyword(self, items):
        """Transform action keyword (action or clicked)."""
        # action_keyword is just a marker in the tree, items may be empty
        # We don't actually need to return anything since we only care about the actions
        return None
    
    def action_sequence(self, items):
        """Transform action sequence (single action or chain)."""
        # items[0] is either action_list_wrapped or action_chain
        return items[0]
    
    def action_list_wrapped(self, items):
        """Transform list-wrapped actions: [Action1(...), Action2(...), ...]"""
        # items[0] is action_chain
        return items[0]
    
    def action_chain(self, items):
        """
        Transform chain of actions.
        Extract only the first Jump or Call action for flow analysis.
        Ignore all other actions (Hide, Show, SetVariable, etc.)
        """
        # items is a list of generic_action nodes
        # Find first Jump or Call action
        for action in items:
            if isinstance(action, ActionNode):
                # This is a Jump or Call action - return it
                return action
        
        # No flow-relevant action found
        return None
    
    def generic_action(self, items):
        """Transform generic action (Jump, Call, or other)."""
        # items[0] is either jump_action, call_action, or other_action
        # jump_action and call_action return ActionNode
        # other_action returns None (we ignore non-flow actions)
        return items[0]
    
    def jump_action(self, items):
        """Transform jump action."""
        line, column = self._get_node_location(items)
        # Grammar: JUMP "(" STRING ")"
        # items[0] = JUMP token
        # items[1] = destination string (already extracted by Lark)
        destination = str(items[1]) if len(items) > 1 else ""
        
        return ActionNode(
            action_type='Jump',
            destination=destination,
            line_number=line,
            column=column
        )
    
    def call_action(self, items):
        """Transform call action."""
        line, column = self._get_node_location(items)
        # Grammar: CALL "(" STRING ")"
        # items[0] = CALL token
        # items[1] = destination string (already extracted by Lark)
        destination = str(items[1]) if len(items) > 1 else ""
        
        return ActionNode(
            action_type='Call',
            destination=destination,
            line_number=line,
            column=column
        )
    
    def start_action(self, items):
        """Transform start action - treated like Jump for flow visualization."""
        line, column = self._get_node_location(items)
        # Grammar: START "(" STRING? ")"
        # items[0] = START token
        # items[1] = destination string (if provided), or None
        # When no argument: Start() defaults to starting at "start" label
        if len(items) > 1 and items[1] is not None:
            destination = str(items[1])
        else:
            destination = "start"  # Default Ren'Py behavior
        
        return ActionNode(
            action_type='Start',
            destination=destination,
            line_number=line,
            column=column
        )
    
    def other_action(self, items):
        """
        Transform other actions (Hide, Show, SetVariable, etc.).
        We parse these to avoid syntax errors, but ignore them for flow analysis.
        """
        # items[0] is ACTION_FUNCTION token
        # items[1:] are action_arguments (if any)
        # Return None to indicate this action is not flow-relevant
        return None
    
    def action_arguments(self, items):
        """Transform action arguments."""
        # We don't need to process these, just let them parse
        return items
    
    def action_arg(self, items):
        """Transform single action argument."""
        # We don't need to process these, just let them parse
        return items[0] if items else None
    
    # ========================================================================
    # DUPLICATE CONDITIONAL TRANSFORMATIONS - REMOVED (already defined above)
    # ========================================================================
    
    
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
            # Read grammar from file directly (no caching)
            with open(self.grammar_path, 'r', encoding='utf-8') as f:
                grammar_text = f.read()
            
            self.parser = Lark(
                grammar_text,
                parser='lalr',
                start='start',
                postlex=RenpyIndenter(),
                maybe_placeholders=False
            )
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
