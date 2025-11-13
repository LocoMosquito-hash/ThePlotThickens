"""
CMAP Parser Implementation

Custom Menu AST Parser that uses Lark to parse Ren'Py menu structures
and convert them to a structured AST.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from lark import Lark, Transformer, Tree, Token
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedToken
from lark.indenter import Indenter

class RenpyMenuIndenter(Indenter):
    """Custom indenter for Ren'Py menu syntax."""
    NL_type = '_NEWLINE'
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = '_INDENT'
    DEDENT_type = '_DEDENT'
    tab_len = 4

try:
    from .cmap_ast import *
except ImportError:
    from cmap_ast import *


class CMAPTransformer(Transformer):
    """Transforms Lark parse tree into CMAP AST nodes."""
    
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
        
        # Try to get location from first token
        for item in items:
            if hasattr(item, 'line'):
                line = item.line
                column = getattr(item, 'column', 0)
                break
            elif hasattr(item, 'meta') and hasattr(item.meta, 'line'):
                line = item.meta.line
                column = getattr(item.meta, 'column', 0)
                break
        
        return line, column
    
    def _extract_string_value(self, token) -> str:
        """Extract string value from token, removing quotes."""
        value = str(token)
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        return value
    
    def _extract_identifier_value(self, token) -> str:
        """Extract identifier value from token."""
        return str(token)
    
    def _extract_number_value(self, token) -> Union[int, float]:
        """Extract number value from token."""
        value = str(token)
        if '.' in value:
            return float(value)
        return int(value)
    
    # ========================================================================
    # MENU STRUCTURE
    # ========================================================================
    
    def start(self, items):
        """Transform start rule."""
        return items[0]  # Return the menu_definition
    
    def menu_definition(self, items):
        """Transform menu definition."""
        line, column = self._get_node_location(items)
        
        # For simplified grammar: "menu" menu_name? ":" menu_body
        # items can be: [menu_body] or [menu_name, menu_body]
        if len(items) == 1:
            # No menu name: items = [menu_body]
            menu_name = None
            body_items = items[0]
        else:
            # With menu name: items = [menu_name, menu_body]
            menu_name = str(items[0])
            body_items = items[1]
        
        menu_params = []
        
        # Separate choices and conditional items from body
        choices = []
        conditional_items = []
        set_variable = None
        
        if isinstance(body_items, list):
            for item in body_items:
                # Skip None items (descriptive text and character dialogue)
                if item is None:
                    continue
                elif isinstance(item, MenuChoiceNode):
                    choices.append(item)
                elif isinstance(item, ConditionalMenuItemNode):
                    conditional_items.append(item)
                elif hasattr(item, 'variable'):  # set statement
                    set_variable = item.variable
        elif body_items:
            # Single item, not a list
            if isinstance(body_items, MenuChoiceNode):
                choices.append(body_items)
            elif isinstance(body_items, ConditionalMenuItemNode):
                conditional_items.append(body_items)
        
        return MenuNode(
            name=menu_name,
            params=menu_params,
            choices=choices,
            conditional_items=conditional_items,
            set_variable=set_variable,
            line_number=line,
            column=column
        )
    
    def menu_header(self, items):
        """Transform menu header."""
        # items: ["menu", name?, params?, ":"]
        header_info = type('HeaderInfo', (), {})()
        header_info.name = None
        header_info.params = []
        
        for item in items:
            if hasattr(item, 'type') and item.type == 'IDENTIFIER':
                header_info.name = str(item)
            elif isinstance(item, list):  # params
                header_info.params = item
        
        return header_info
    
    def menu_name(self, items):
        """Transform menu name."""
        return str(items[0])
    
    def param_list(self, items):
        """Transform parameter list."""
        return [str(item) for item in items]
    
    def menu_body(self, items):
        """Transform menu body."""
        return items  # List of menu items
    
    def menu_item(self, items):
        """Transform menu item."""
        return items[0]  # Return the choice, text, or dialogue
    
    def menu_text(self, items):
        """Transform menu text (descriptive text)."""
        # Just return None - we ignore descriptive text for flow analysis
        return None
    
    def character_dialogue(self, items):
        """Transform character dialogue in menu."""
        # Just return None - we ignore character dialogue for flow analysis
        return None
    
    # ========================================================================
    # MENU CHOICES
    # ========================================================================
    
    def menu_choice(self, items):
        """Transform menu choice (delegates to simple_choice or conditional_choice)."""
        return items[0]  # Return the actual choice
    
    def simple_choice(self, items):
        """Transform simple choice."""
        line, column = self._get_node_location(items)
        
        # items: [STRING, ":", choice_body?]
        choice_text = self._extract_string_value(items[0])
        body = items[1] if len(items) > 1 else []
        
        return MenuChoiceNode(
            text=choice_text,
            condition=None,
            body=body if isinstance(body, list) else [],
            is_conditional=False,
            line_number=line,
            column=column
        )
    
    def conditional_choice(self, items):
        """Transform conditional choice."""
        line, column = self._get_node_location(items)
        
        # items: [STRING, "if", conditional_expression, ":", choice_body?]
        choice_text = self._extract_string_value(items[0])
        condition_text = str(items[1])  # Raw conditional text
        body = items[2] if len(items) > 2 else []
        
        # Create a simple conditional expression node
        condition = ConditionalExpressionNode(
            variable=condition_text,  # Store the full condition as text
            operator=None,
            value=None,
            line_number=line,
            column=column
        )
        
        return MenuChoiceNode(
            text=choice_text,
            condition=condition,
            body=body if isinstance(body, list) else [],
            is_conditional=True,
            line_number=line,
            column=column
        )
    
    
    def choice_condition(self, items):
        """Transform choice condition."""
        return items[0]  # conditional_expression
    
    def choice_body(self, items):
        """Transform choice body."""
        return items  # List of choice statements
    
    def statement(self, items):
        """Transform statement."""
        return items[0]  # Return the actual statement
    
    # ========================================================================
    # CONDITIONAL EXPRESSIONS
    # ========================================================================
    
    def conditional_expression(self, items):
        """Transform conditional expression."""
        if len(items) == 1:
            # Simple identifier or "not identifier"
            return str(items[0]).strip()
        elif len(items) == 3:
            # identifier operator value
            return f"{items[0]} {items[1]} {items[2]}"
        else:
            # Fallback - join all items
            return " ".join(str(item) for item in items)
    
    def conditional_expression_old(self, items):
        """Transform conditional expression with support for compound conditions."""
        line, column = self._get_node_location(items)
        
        if len(items) == 1:
            # Simple condition
            return items[0]
        
        # Compound condition - chain them together
        first_condition = items[0]
        
        for i in range(1, len(items), 2):  # Skip logical operators
            if i + 1 < len(items):
                logical_op = str(items[i]) if hasattr(items[i], '__str__') else 'and'
                next_condition = items[i + 1]
                
                first_condition.logical_operator = logical_op
                first_condition.next_condition = next_condition
        
        return first_condition
    
    def condition_part(self, items):
        """Transform simple condition."""
        line, column = self._get_node_location(items)
        
        if len(items) == 1:
            # Boolean variable or 'not variable'
            variable = str(items[0])
            return ConditionalExpressionNode(
                variable=variable,
                line_number=line,
                column=column
            )
        elif len(items) == 2 and str(items[0]) == 'not':
            # 'not variable'
            variable = str(items[1])
            return ConditionalExpressionNode(
                variable=variable,
                is_negated=True,
                line_number=line,
                column=column
            )
        else:
            # variable operator value
            variable = str(items[0])
            operator = str(items[1])
            value = items[2]
            
            # Extract value based on type
            if hasattr(value, 'type'):
                if value.type == 'STRING':
                    value = self._extract_string_value(value)
                elif value.type in ('NUMBER', 'DECIMAL'):
                    value = self._extract_number_value(value)
                elif value.type == 'IDENTIFIER':
                    value = self._extract_identifier_value(value)
                elif value.type in ('TRUE', 'FALSE'):
                    value = str(value)  # Keep as 'True' or 'False' string
            else:
                value = str(value)
            
            return ConditionalExpressionNode(
                variable=variable,
                operator=operator,
                value=value,
                line_number=line,
                column=column
            )
    
    def condition_value(self, items):
        """Transform conditional value."""
        return items[0]
    
    def TRUE(self, token):
        """Transform TRUE token."""
        return Token('TRUE', 'True')
    
    def FALSE(self, token):
        """Transform FALSE token."""
        return Token('FALSE', 'False')
    
    # ========================================================================
    # CONDITIONAL MENU ITEMS
    # ========================================================================
    
    def conditional_menu_item(self, items):
        """Transform conditional menu item (if/elif/else)."""
        line, column = self._get_node_location(items)
        
        if_condition = None
        if_body = []
        elif_conditions = []
        elif_bodies = []
        else_body = None
        
        for item in items:
            if hasattr(item, 'condition') and hasattr(item, 'body'):
                if item.type == 'if':
                    if_condition = item.condition
                    if_body = item.body
                elif item.type == 'elif':
                    elif_conditions.append(item.condition)
                    elif_bodies.append(item.body)
                elif item.type == 'else':
                    else_body = item.body
        
        return ConditionalMenuItemNode(
            if_condition=if_condition,
            if_body=if_body,
            elif_conditions=elif_conditions,
            elif_bodies=elif_bodies,
            else_body=else_body,
            line_number=line,
            column=column
        )
    
    def if_menu_statement(self, items):
        """Transform if menu statement."""
        condition = items[0]  # conditional_expression
        body = items[1] if len(items) > 1 else []  # conditional_menu_body
        
        result = type('IfStatement', (), {})()
        result.type = 'if'
        result.condition = condition
        result.body = body
        return result
    
    def elif_menu_statement(self, items):
        """Transform elif menu statement."""
        condition = items[0]  # conditional_expression
        body = items[1] if len(items) > 1 else []  # conditional_menu_body
        
        result = type('ElifStatement', (), {})()
        result.type = 'elif'
        result.condition = condition
        result.body = body
        return result
    
    def else_menu_statement(self, items):
        """Transform else menu statement."""
        body = items[0] if len(items) > 0 else []  # conditional_menu_body
        
        result = type('ElseStatement', (), {})()
        result.type = 'else'
        result.condition = None
        result.body = body
        return result
    
    def conditional_menu_body(self, items):
        """Transform conditional menu body."""
        return items  # List of menu items
    
    # ========================================================================
    # CHOICE STATEMENTS
    # ========================================================================
    
    def if_statement(self, items):
        """Transform if statement in choice body."""
        line, column = self._get_node_location(items)
        
        # items: [conditional_expression, statement]
        condition = str(items[0])  # Condition text
        body_statement = items[1]  # The statement inside the if
        
        # For simplicity, wrap the statement in a list and create a conditional node
        # We'll represent this as a simple conditional wrapper around the statement
        result = type('IfStatementWrapper', (), {})()
        result.condition = condition
        result.statement = body_statement
        result.line_number = line
        result.column = column
        
        # Return the wrapped statement - for now just return the inner statement
        # since we're treating "if True:" as always executing
        return body_statement
    
    def jump_statement(self, items):
        """Transform jump statement."""
        line, column = self._get_node_location(items)
        # Grammar: JUMP IDENTIFIER
        # items: [JUMP, IDENTIFIER]
        target = str(items[1])
        
        return JumpStatementNode(
            target=target,
            line_number=line,
            column=column
        )
    
    def call_statement(self, items):
        """Transform call statement."""
        line, column = self._get_node_location(items)
        # Grammar: CALL IDENTIFIER
        # items: [CALL, IDENTIFIER]
        target = str(items[1])
        params = items[2] if len(items) > 2 else []
        
        return CallStatementNode(
            target=target,
            params=params,
            line_number=line,
            column=column
        )
    
    def return_statement(self, items):
        """Transform return statement."""
        line, column = self._get_node_location(items)
        # Grammar: RETURN
        # items: [RETURN]
        value = None
        
        return ReturnStatementNode(
            value=value,
            line_number=line,
            column=column
        )
    
    def pass_statement(self, items):
        """Transform pass statement."""
        line, column = self._get_node_location(items)
        # Grammar: PASS
        # items: [PASS]
        
        return PassStatementNode(
            line_number=line,
            column=column
        )
    
    def scene_statement(self, items):
        """Transform scene statement."""
        line, column = self._get_node_location(items)
        
        # Grammar: SCENE IDENTIFIER (WITH IDENTIFIER)?
        # items: [SCENE, IDENTIFIER] or [SCENE, IDENTIFIER, WITH, IDENTIFIER]
        image_name = str(items[1])
        
        # Check if there's a transition (4 items means WITH and transition present)
        transition = None
        if len(items) >= 4:
            transition = str(items[3])  # The transition name after WITH
        
        return SceneStatementNode(
            image_name=image_name,
            transition=transition,
            line_number=line,
            column=column
        )
    
    def pause_statement(self, items):
        """Transform pause statement."""
        line, column = self._get_node_location(items)
        
        # Grammar: PAUSE NUMBER?
        # items: [PAUSE] or [PAUSE, NUMBER]
        # We only care about the optional NUMBER (items[1] if present)
        duration = None
        if len(items) > 1:  # Has NUMBER
            duration = self._extract_number_value(items[1])
        
        return PauseStatementNode(
            duration=duration,
            line_number=line,
            column=column
        )
    
    def with_statement(self, items):
        """Transform standalone with statement (transition)."""
        # Grammar: WITH IDENTIFIER
        # items: [WITH, IDENTIFIER]
        # We don't care about transitions for flow analysis, return None
        return None
    
    def empty_char_dialogue(self, items):
        """Transform empty character narrator dialogue ('"" "text"')."""
        # We don't care about dialogue for flow analysis, return None
        return None
    
    def inline_python(self, items):
        """Transform inline Python statement ($ code)."""
        # We don't care about Python code for flow analysis, return None
        return None
    
    def python_statement(self, items):
        """Transform Python statement."""
        line, column = self._get_node_location(items)
        code = str(items[0])
        
        return PythonStatementNode(
            code=code,
            line_number=line,
            column=column
        )
    
    def dialogue_statement(self, items):
        """Transform dialogue statement."""
        line, column = self._get_node_location(items)
        
        speaker = None
        text = ""
        
        if len(items) == 1:
            text = self._extract_string_value(items[0])
        elif len(items) == 2:
            speaker = str(items[0])
            text = self._extract_string_value(items[1])
        
        return DialogueStatementNode(
            speaker=speaker,
            text=text,
            line_number=line,
            column=column
        )
    
    def variable_assignment(self, items):
        """Transform variable assignment."""
        line, column = self._get_node_location(items)
        
        variable = str(items[0])
        operator = str(items[1])
        value = items[2]
        
        # Extract value based on type
        if hasattr(value, 'type'):
            if value.type == 'STRING':
                value = self._extract_string_value(value)
            elif value.type in ('NUMBER', 'DECIMAL'):
                value = self._extract_number_value(value)
            elif value.type == 'IDENTIFIER':
                value = self._extract_identifier_value(value)
            elif value.type in ('TRUE', 'FALSE'):
                value = str(value)  # Keep as 'True' or 'False' string
        else:
            value = str(value)
        
        return VariableAssignmentNode(
            variable=variable,
            operator=operator,
            value=value,
            line_number=line,
            column=column
        )
    
    def menu_set_statement(self, items):
        """Transform menu set statement."""
        line, column = self._get_node_location(items)
        variable = str(items[0])
        
        result = type('SetStatement', (), {})()
        result.variable = variable
        result.line_number = line
        result.column = column
        return result
    
    def generic_statement(self, items):
        """Transform generic statement (catch-all)."""
        line, column = self._get_node_location(items)
        content = str(items[0]) if items else ""
        
        return DialogueStatementNode(
            speaker=None,
            text=content,
            line_number=line,
            column=column
        )
    
    # ========================================================================
    # NESTED MENUS
    # ========================================================================
    
    def nested_menu(self, items):
        """Transform nested menu."""
        line, column = self._get_node_location(items)
        menu = items[0]  # menu_definition
        
        return NestedMenuNode(
            menu=menu,
            line_number=line,
            column=column
        )


class CMAPParser:
    """Custom Menu AST Parser using Lark."""
    
    def __init__(self):
        """Initialize the CMAP parser."""
        self.grammar_file = Path(__file__).parent / "menu_grammar_simple.lark"
        self.parser = None
        self.transformer = CMAPTransformer()
        self._load_grammar()
    
    def _load_grammar(self):
        """Load the Lark grammar for menu parsing."""
        try:
            with open(self.grammar_file, 'r', encoding='utf-8') as f:
                grammar = f.read()
            
            self.parser = Lark(
                grammar,
                parser='lalr',
                start='start'
            )
            
        except Exception as e:
            print(f"[CMAP] Failed to load grammar: {e}")
            self.parser = None
    
    def parse_menu(self, menu_text: str) -> Optional[MenuNode]:
        """
        Parse a menu structure from text.
        
        Args:
            menu_text: The menu text to parse
            
        Returns:
            MenuNode if successful, None if parsing fails
        """
        if not self.parser:
            return None
        
        try:
            # Parse the menu text
            tree = self.parser.parse(menu_text)
            
            # Apply transformer to convert tree to AST
            if tree:
                transformed = self.transformer.transform(tree)
                
                # The result might be wrapped in a Tree, extract the MenuNode
                if isinstance(transformed, MenuNode):
                    return transformed
                elif hasattr(transformed, 'children') and len(transformed.children) > 0:
                    # Extract the first child which should be our MenuNode
                    menu_node = transformed.children[0]
                    if isinstance(menu_node, MenuNode):
                        return menu_node
                    else:
                        print(f"[CMAP] First child is not MenuNode: {type(menu_node)}")
                        return None
                else:
                    print(f"[CMAP] Unexpected transform result type: {type(transformed)}")
                    print(f"[CMAP] Transform result: {transformed}")
                    return None
            else:
                print(f"[CMAP] Parse returned None")
                return None
                
        except LarkError as e:
            # Show first 5 lines of menu_text for context
            menu_lines = menu_text.split('\n') if menu_text else []
            context_lines = menu_lines[:5] if len(menu_lines) > 0 else ["(empty)"]
            print(f"[CMAP] Parse error: {e}")
            print(f"[CMAP] Problem menu context:")
            for idx, line in enumerate(context_lines, 1):
                print(f"[CMAP]   {idx}: {line}")
            return None
        except Exception as e:
            print(f"[CMAP] Unexpected error during parsing: {e}")
            return None
    
    def extract_menu_from_lines(self, lines: List[str], start_line: int) -> tuple[str, int]:
        """
        Extract ONLY the menu block from lines, focusing on menu structure.
        
        Args:
            lines: List of all lines in the file
            start_line: Line number where menu starts (1-indexed)
            
        Returns:
            Tuple of (menu_text, end_line)
        """
        if start_line < 1 or start_line > len(lines):
            return "", start_line
        
        menu_lines = []
        current_line = start_line - 1  # Convert to 0-based
        menu_indent = None
        in_menu_block = False
        in_nested_menu = False
        nested_menu_indent = None
        
        while current_line < len(lines):
            line = lines[current_line]
            
            # Skip empty lines within the menu
            # Don't add them to preserve accurate line number mapping
            if not line.strip():
                current_line += 1
                continue
            
            # Get indentation level
            indent_level = len(line) - len(line.lstrip())
            stripped_line = line.strip()
            
            # If this is the menu declaration line
            if not in_menu_block and stripped_line.startswith('menu'):
                menu_indent = indent_level
                in_menu_block = True
                menu_lines.append(line)
                current_line += 1
                continue
            
            # If we're in the menu block
            if in_menu_block:
                # Stop if we're back to menu indentation or less (except for comments)
                if indent_level <= menu_indent and not stripped_line.startswith('#'):
                    break
                
                # Check if this is a nested menu declaration
                if stripped_line.startswith('menu') and ':' in stripped_line and indent_level > menu_indent:
                    if not in_nested_menu:
                        # Entering nested menu - start skipping
                        in_nested_menu = True
                        nested_menu_indent = indent_level
                        current_line += 1
                        continue
                
                # If we're in a nested menu, skip until we exit it
                if in_nested_menu:
                    # Exit nested menu when we return to the indent level where the nested menu started or less
                    if indent_level <= nested_menu_indent:
                        in_nested_menu = False
                        nested_menu_indent = None
                        # Don't increment current_line - process this line
                    else:
                        # Still in nested menu - skip
                        current_line += 1
                        continue
                
                # Only include menu-relevant content:
                # - Choice definitions (strings with colons)
                # - Choice bodies (jump, call, return, pass, etc.)
                # - Conditional statements within choices
                if (indent_level > menu_indent and 
                    (stripped_line.startswith('"') or stripped_line.startswith("'") or  # Choices
                     stripped_line.startswith('jump ') or stripped_line.startswith('call ') or  # Actions
                     stripped_line.startswith('return') or stripped_line == 'pass' or  # Actions
                     stripped_line.startswith('if ') or stripped_line.startswith('elif ') or  # Conditionals
                     stripped_line.startswith('else:') or stripped_line.startswith('#'))):  # Comments
                    menu_lines.append(line)
                # Skip non-menu statements like 'scene', 'python:', nested menus, etc.
            
            current_line += 1
        
        # Lines from file already have newlines, so just concatenate them
        return ''.join(menu_lines), current_line + 1
    
    def parse_menu_from_lines(self, lines: List[str], start_line: int) -> Optional[MenuNode]:
        """
        Parse a menu from lines starting at a specific line.
        
        Args:
            lines: List of all lines in the file
            start_line: Line number where menu starts (1-indexed)
            
        Returns:
            MenuNode if successful, None if parsing fails
        """
        menu_text, end_line = self.extract_menu_from_lines(lines, start_line)
        
        if not menu_text.strip():
            return None
        
        return self.parse_menu(menu_text)
