"""
CMAP Parser Implementation

Custom Menu AST Parser that uses Lark to parse Ren'Py menu structures
and convert them to a structured AST.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from lark import Lark, Transformer, Tree, Token
from lark.exceptions import LarkError, UnexpectedInput, UnexpectedToken
from lark.indenter import Indenter

# ============================================================================
# CSA Integration - Add CSA to path for conditional parsing
# ============================================================================
# Add CSA to path - handle both development and production scenarios
csa_path = Path(__file__).parent.parent.parent.parent.parent / "ideas-lab" / "flow-visualizer-poc"
if str(csa_path) not in sys.path:
    sys.path.insert(0, str(csa_path))

try:
    from CSA import ConditionalStructureAnalyzer, ConditionalBlock, ConditionalBranch
    CSA_AVAILABLE = True
    print("[CMAP] CSA integration available")
except ImportError as e:
    print(f"[CMAP] WARNING: CSA not available: {e}")
    print("[CMAP] Falling back to grammar-based conditional parsing")
    CSA_AVAILABLE = False
    ConditionalStructureAnalyzer = None
    ConditionalBlock = None
    ConditionalBranch = None

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
        """Initialize CMAP transformer."""
        super().__init__()
        self.current_line = 1
        self.current_column = 1
        # CSA flag will be set by CMAPParser
        self.use_csa = False
        self.csa = None
    
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
        
        # Grammar: STRING IF conditional_expression ":" choice_body?
        # items: [STRING, IF, conditional_expression, choice_body?]
        # Lark doesn't include literal tokens like ":" in items
        choice_text = self._extract_string_value(items[0])
        # items[1] is the IF keyword token (skip it)
        condition_expr = items[2]  # The conditional_expression
        body = items[3] if len(items) > 3 else []  # Body is at index 3, not 2
        
        # Create a simple conditional expression node
        # Store the condition expression text for display
        condition_text = str(condition_expr) if condition_expr else "unknown"
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
        # Filter out None items (from statements we don't care about like stop, with, etc.)
        return [item for item in items if item is not None]
    
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
    
    def _parse_conditional_menu_with_csa(
        self,
        items: List[Any],
        line: int,
        column: int
    ) -> ConditionalMenuItemNode:
        """
        Parse conditional menu items using CSA (alternative to grammar-based approach).
        
        This method uses the Conditional Structure Analyzer to parse if/elif/else
        blocks and extract menu items from ALL branches for flow visualization.
        
        Args:
            items: Parse tree items from Lark
            line: Line number of conditional start
            column: Column of conditional start
            
        Returns:
            ConditionalMenuItemNode with all branches parsed
            
        Note:
            This is called when use_csa=True. Falls back to grammar-based
            parsing if CSA analysis fails.
        """
        try:
            # Extract conditions and bodies from grammar output
            # items structure: [if_statement, elif_statement*, else_statement?]
            if_condition = None
            if_body = []
            elif_conditions = []
            elif_bodies = []
            else_body = None
            
            # Process each item from the grammar
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
            
            # Note: For now, CSA integration uses the same structure as grammar-based
            # parsing since the grammar already extracts the branches well.
            # Future enhancement: Use CSA to re-parse raw text for better error handling
            # and to extract from ALL branches in "show all paths" mode.
            
            print(f"[CMAP-CSA] Parsed conditional with {len(elif_conditions) + 2 if else_body else len(elif_conditions) + 1} branches")
            
            return ConditionalMenuItemNode(
                if_condition=if_condition,
                if_body=if_body,
                elif_conditions=elif_conditions,
                elif_bodies=elif_bodies,
                else_body=else_body,
                line_number=line,
                column=column
            )
            
        except Exception as e:
            # Fallback to grammar-based parsing if CSA fails
            print(f"[CMAP-CSA] WARNING: CSA parsing failed: {e}, using fallback")
            return self._parse_conditional_menu_grammar_based(items, line, column)
    
    def _parse_conditional_menu_grammar_based(
        self,
        items: List[Any],
        line: int,
        column: int
    ) -> ConditionalMenuItemNode:
        """
        Parse conditional menu items using grammar-based approach (original method).
        
        This is the original parsing logic, kept as fallback and for comparison.
        """
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
    
    def conditional_menu_item(self, items):
        """
        Transform conditional menu item (if/elif/else).
        
        Routes to either CSA-based or grammar-based parsing depending on use_csa flag.
        """
        line, column = self._get_node_location(items)
        
        # Route to appropriate parser
        if self.use_csa:
            # NEW: Use CSA path
            return self._parse_conditional_menu_with_csa(items, line, column)
        else:
            # EXISTING: Use grammar-based path
            return self._parse_conditional_menu_grammar_based(items, line, column)
    
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
    
    def stop_statement(self, items):
        """Transform stop statement (audio control)."""
        # Grammar: STOP IDENTIFIER (FADEOUT NUMBER)?
        # items: [STOP, channel] or [STOP, channel, FADEOUT, duration]
        # We don't care about audio control for flow analysis, return None
        return None
    
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
    
    def __init__(self, use_csa: bool = False):
        """
        Initialize the CMAP parser.
        
        Args:
            use_csa: If True and CSA is available, use CSA for conditional parsing.
                     If False or CSA unavailable, use grammar-based parsing.
        """
        self.grammar_file = Path(__file__).parent / "menu_grammar.lark"
        self.parser = None
        self.use_csa = use_csa and CSA_AVAILABLE
        self.transformer = CMAPTransformer()
        # Configure transformer to use CSA
        self.transformer.use_csa = self.use_csa
        if self.use_csa:
            self.transformer.csa = ConditionalStructureAnalyzer()
            print("[CMAP-CSA] CSA integration enabled for conditional parsing")
        else:
            if use_csa and not CSA_AVAILABLE:
                print("[CMAP-CSA] WARNING: CSA requested but not available, using grammar-based parsing")
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
    
    def _contains_conditional_menu_items(self, menu_text: str) -> bool:
        """
        Quick detection: Does this menu have if/elif/else at menu item level?
        
        Distinguishes between:
        - Conditional CHOICES: "Text" if condition: ...
        - Conditional MENU ITEMS: if condition: "Text": ...
        
        Returns True only for conditional menu items (which grammar can't handle).
        
        Uses simple regex-based detection for reliability.
        """
        import re
        
        # Pattern: line starts with whitespace, then if/elif/else
        # This catches: "    if condition:" but not '"Text" if condition:'
        conditional_pattern = re.compile(r'^\s+(if\s+|elif\s+|else:)')
        
        in_menu = False
        for line in menu_text.split('\n'):
            # Track when we're inside a menu
            if 'menu' in line and ':' in line:
                in_menu = True
                continue
            
            if not in_menu:
                continue
            
            # Check if this line has a conditional at menu level
            if conditional_pattern.match(line):
                # Make sure it's not a conditional choice ("Text" if cond:)
                # Conditional choices have quotes before the 'if'
                if '"' not in line[:line.find('if')] if 'if' in line else True:
                    return True
        
        return False
    
    def _parse_menu_with_csa(self, menu_text: str) -> Optional[MenuNode]:
        """
        Parse menu using CSA for conditional blocks.
        
        This method:
        1. Extracts menu header
        2. Finds all conditional blocks with CSA
        3. Extracts choices from each branch
        4. Finds regular (non-conditional) choices
        5. Builds complete MenuNode
        
        Args:
            menu_text: Raw menu text
            
        Returns:
            MenuNode if successful, None if parsing fails
        """
        try:
            lines = menu_text.split('\n')
            
            # 1. Extract menu header
            menu_name = None
            menu_start_line = 0
            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith('menu'):
                    # Check for menu name: "menu my_menu:" or just "menu:"
                    if ':' in stripped:
                        header = stripped[4:stripped.index(':')].strip()
                        if header:
                            menu_name = header
                    menu_start_line = i + 1
                    break
            
            # 2. Get menu body (everything after menu header)
            menu_body = '\n'.join(lines[menu_start_line:])
            
            # 3. Use CSA to find all conditional blocks
            conditional_items = []
            regular_choices = []
            
            # Try to parse conditionals with CSA
            if self.transformer.csa:
                conditional_items = self._find_conditional_items_with_csa(menu_body, menu_start_line)
            
            # 4. Find regular choices (not inside conditionals)
            regular_choices = self._find_regular_choices(menu_body, conditional_items)
            
            print(f"[CMAP-CSA] Parsed menu: {len(conditional_items)} conditional items, {len(regular_choices)} regular choices")
            
            # 5. Build MenuNode
            return MenuNode(
                name=menu_name,
                choices=regular_choices,
                conditional_items=conditional_items,
                line_number=1,
                column=1
            )
            
        except Exception as e:
            print(f"[CMAP-CSA] ERROR: CSA parsing failed: {e}")
            print(f"[CMAP-CSA] Falling back to grammar-based parsing")
            # Fallback to grammar parsing
            return self._parse_menu_with_grammar(menu_text)
    
    def _find_conditional_items_with_csa(
        self,
        menu_body: str,
        start_line: int
    ) -> List['ConditionalMenuItemNode']:
        """
        Use CSA to find all if/elif/else blocks at menu level.
        
        Args:
            menu_body: Menu body text (everything after "menu:")
            start_line: Line number where menu body starts
            
        Returns:
            List of ConditionalMenuItemNode objects
        """
        conditional_items = []
        
        try:
            # Use CSA to analyze the menu body
            # CSA will find all if/elif/else structures
            conditional_block = self.transformer.csa.analyze_conditional(
                menu_body,
                start_line=start_line,
                context_stack=['label', 'menu'],
                max_depth=5
            )
            
            if conditional_block:
                # Extract choices from each branch
                conditional_item = self._build_conditional_item_from_csa(conditional_block)
                if conditional_item:
                    conditional_items.append(conditional_item)
                    
        except Exception as e:
            print(f"[CMAP-CSA] Warning: CSA analysis failed: {e}")
        
        return conditional_items
    
    def _build_conditional_item_from_csa(
        self,
        csa_block: 'ConditionalBlock'
    ) -> Optional['ConditionalMenuItemNode']:
        """
        Build ConditionalMenuItemNode from CSA ConditionalBlock.
        
        Extracts menu choices from each branch's content.
        
        Args:
            csa_block: ConditionalBlock from CSA
            
        Returns:
            ConditionalMenuItemNode or None
        """
        if_condition = None
        if_body = []
        elif_conditions = []
        elif_bodies = []
        else_body = None
        
        for branch in csa_block.branches:
            # Extract choices from this branch's content
            choices = self._extract_choices_from_lines(branch.content_lines)
            
            if branch.branch_type == 'if':
                if_condition = branch.condition
                if_body = choices
            elif branch.branch_type == 'elif':
                elif_conditions.append(branch.condition)
                elif_bodies.append(choices)
            elif branch.branch_type == 'else':
                else_body = choices
        
        return ConditionalMenuItemNode(
            if_condition=if_condition,
            if_body=if_body,
            elif_conditions=elif_conditions,
            elif_bodies=elif_bodies,
            else_body=else_body,
            line_number=csa_block.start_line,
            column=1
        )
    
    def _parse_menu_with_grammar(self, menu_text: str) -> Optional[MenuNode]:
        """
        Parse menu using grammar-based approach (original method).
        
        This is the fallback when CSA parsing fails or use_csa=False.
        """
        if not self.parser:
            return None
            
        try:
            tree = self.parser.parse(menu_text)
            if tree:
                transformed = self.transformer.transform(tree)
                if isinstance(transformed, MenuNode):
                    return transformed
                elif hasattr(transformed, 'children') and len(transformed.children) > 0:
                    menu_node = transformed.children[0]
                    if isinstance(menu_node, MenuNode):
                        return menu_node
            return None
        except Exception as e:
            print(f"[CMAP] Grammar parsing error: {e}")
            return None
    
    def _extract_choices_from_lines(self, lines: List[str]) -> List['MenuChoiceNode']:
        """
        Extract menu choices from lines of text.
        
        Looks for pattern: "Choice text": followed by action (jump/call/etc.)
        
        Args:
            lines: Lines of text that may contain choices
            
        Returns:
            List of MenuChoiceNode objects
        """
        choices = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Match choice pattern: "Text":
            if stripped.startswith('"') and '":' in stripped:
                # Extract choice text
                try:
                    end_quote = stripped.index('"', 1)
                    choice_text = stripped[1:end_quote]
                    
                    # Look for action statements on next lines (jump, call, etc.)
                    body_statements = []
                    
                    # Check next few lines for action
                    for j in range(i + 1, min(i + 5, len(lines))):
                        action_line = lines[j].strip()
                        
                        # Jump statement
                        if action_line.startswith('jump '):
                            target = action_line[5:].strip()
                            body_statements.append(JumpStatementNode(
                                target=target,
                                line_number=0,
                                column=0
                            ))
                            break
                        # Call statement
                        elif action_line.startswith('call '):
                            target = action_line[5:].strip()
                            body_statements.append(CallStatementNode(
                                target=target,
                                params=[],
                                line_number=0,
                                column=0
                            ))
                            break
                        # Return statement
                        elif action_line.startswith('return'):
                            return_val = action_line[6:].strip() if len(action_line) > 6 else None
                            body_statements.append(ReturnStatementNode(
                                value=return_val,
                                line_number=0,
                                column=0
                            ))
                            break
                    
                    # Create choice node
                    choice = MenuChoiceNode(
                        text=choice_text,
                        condition=None,  # Regular choice has no condition
                        body=body_statements,
                        is_conditional=False,
                        line_number=0,  # Will be set by parser
                        column=0
                    )
                    choices.append(choice)
                    
                except ValueError:
                    # Malformed choice, skip
                    pass
            
            i += 1
        
        return choices
    
    def _find_regular_choices(
        self,
        menu_body: str,
        conditional_items: List['ConditionalMenuItemNode']
    ) -> List['MenuChoiceNode']:
        """
        Find regular (non-conditional) choices in menu body.
        
        Excludes choices that are inside conditional blocks.
        
        Args:
            menu_body: Menu body text
            conditional_items: List of conditional items (to exclude their lines)
            
        Returns:
            List of MenuChoiceNode objects
        """
        # For now, simple implementation: extract all choices
        # TODO: Filter out lines that belong to conditional blocks
        
        lines = menu_body.split('\n')
        
        # Build set of line ranges covered by conditionals
        conditional_line_ranges = []
        for item in conditional_items:
            # Approximate line range based on item structure
            # This is a simple heuristic - could be improved
            pass
        
        # Extract choices from non-conditional lines
        all_choices = self._extract_choices_from_lines(lines)
        
        # TODO: Filter choices that fall within conditional ranges
        # For MVP, return all choices
        
        return all_choices
    
    def parse_menu(self, menu_text: str) -> Optional[MenuNode]:
        """
        Parse a menu structure from text.
        
        Routes to CSA-based parser if menu has conditional items and use_csa=True,
        otherwise uses grammar-based parser.
        
        Args:
            menu_text: The menu text to parse
            
        Returns:
            MenuNode if successful, None if parsing fails
        """
        # CSA-first routing for conditional menu items
        if self.use_csa and self._contains_conditional_menu_items(menu_text):
            print("[CMAP-CSA] Detected conditional menu items, using CSA parser")
            return self._parse_menu_with_csa(menu_text)
        
        # Standard grammar-based parsing
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
