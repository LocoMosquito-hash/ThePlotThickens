"""
CMAP AST Node Definitions

Custom Menu AST Parser - AST node classes for representing parsed menu structures.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union
from abc import ABC, abstractmethod


@dataclass
class CMAPNode(ABC):
    """Base class for all CMAP AST nodes."""
    line_number: int = 0
    column: int = 0
    
    @abstractmethod
    def validate(self) -> List[str]:
        """Validate the node and return a list of error messages."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        result = {
            'type': self.__class__.__name__,
            'line_number': self.line_number,
            'column': self.column
        }
        
        for key, value in self.__dict__.items():
            if key not in ['line_number', 'column']:
                if isinstance(value, list):
                    result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
                elif hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                else:
                    result[key] = value
        
        return result


@dataclass
class MenuNode(CMAPNode):
    """Represents a complete menu definition."""
    name: Optional[str] = None
    params: List[str] = field(default_factory=list)
    choices: List['MenuChoiceNode'] = field(default_factory=list)
    conditional_items: List['ConditionalMenuItemNode'] = field(default_factory=list)
    set_variable: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Validate the menu node."""
        errors = []
        
        if not self.choices and not self.conditional_items:
            errors.append(f"Menu at line {self.line_number} has no choices or conditional items")
        
        # Validate all choices
        for choice in self.choices:
            errors.extend(choice.validate())
        
        # Validate all conditional items
        for item in self.conditional_items:
            errors.extend(item.validate())
        
        return errors


@dataclass
class MenuChoiceNode(CMAPNode):
    """Represents a single menu choice."""
    text: str = ""
    condition: Optional['ConditionalExpressionNode'] = None
    body: List['ChoiceStatementNode'] = field(default_factory=list)
    is_conditional: bool = False
    
    def validate(self) -> List[str]:
        """Validate the choice node."""
        errors = []
        
        if not self.text.strip():
            errors.append(f"Empty choice text at line {self.line_number}")
        
        # Validate condition if present
        if self.condition:
            errors.extend(self.condition.validate())
        
        # Validate body statements
        for statement in self.body:
            errors.extend(statement.validate())
        
        return errors


@dataclass
class ConditionalMenuItemNode(CMAPNode):
    """Represents if/elif/else conditional menu items."""
    if_condition: Optional['ConditionalExpressionNode'] = None
    if_body: List['MenuItemNode'] = field(default_factory=list)
    elif_conditions: List['ConditionalExpressionNode'] = field(default_factory=list)
    elif_bodies: List[List['MenuItemNode']] = field(default_factory=list)
    else_body: Optional[List['MenuItemNode']] = None
    
    def validate(self) -> List[str]:
        """Validate the conditional menu item."""
        errors = []
        
        # Validate if condition
        if self.if_condition:
            errors.extend(self.if_condition.validate())
        
        # Validate elif conditions
        for condition in self.elif_conditions:
            errors.extend(condition.validate())
        
        # Validate all bodies
        for item in self.if_body:
            errors.extend(item.validate())
        
        for elif_body in self.elif_bodies:
            for item in elif_body:
                errors.extend(item.validate())
        
        if self.else_body:
            for item in self.else_body:
                errors.extend(item.validate())
        
        return errors


@dataclass
class ConditionalExpressionNode(CMAPNode):
    """Represents a conditional expression (variable == value, etc.)."""
    variable: str = ""
    operator: Optional[str] = None  # None for boolean variables
    value: Optional[Any] = None
    logical_operator: Optional[str] = None  # 'and', 'or'
    next_condition: Optional['ConditionalExpressionNode'] = None
    is_negated: bool = False  # For 'not variable'
    
    def validate(self) -> List[str]:
        """Validate the conditional expression."""
        errors = []
        
        if not self.variable:
            errors.append(f"Empty variable name in condition at line {self.line_number}")
        
        # If we have an operator, we should have a value
        if self.operator and self.value is None:
            errors.append(f"Condition at line {self.line_number} has operator '{self.operator}' but no value")
        
        # Validate next condition if chained
        if self.next_condition:
            errors.extend(self.next_condition.validate())
        
        return errors


# Union type for menu items (choices or conditional items)
MenuItemNode = Union[MenuChoiceNode, ConditionalMenuItemNode]


@dataclass
class ChoiceStatementNode(CMAPNode):
    """Base class for statements within choice bodies."""
    pass


@dataclass
class JumpStatementNode(ChoiceStatementNode):
    """Represents a jump statement."""
    target: str = ""
    
    def validate(self) -> List[str]:
        """Validate the jump statement."""
        errors = []
        if not self.target:
            errors.append(f"Empty jump target at line {self.line_number}")
        return errors


@dataclass
class CallStatementNode(ChoiceStatementNode):
    """Represents a call statement."""
    target: str = ""
    params: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate the call statement."""
        errors = []
        if not self.target:
            errors.append(f"Empty call target at line {self.line_number}")
        return errors


@dataclass
class ReturnStatementNode(ChoiceStatementNode):
    """Represents a return statement."""
    value: Optional[Any] = None
    
    def validate(self) -> List[str]:
        """Validate the return statement."""
        return []  # Return statements are always valid


@dataclass
class PassStatementNode(ChoiceStatementNode):
    """Represents a pass statement."""
    
    def validate(self) -> List[str]:
        """Validate the pass statement."""
        return []  # Pass statements are always valid


@dataclass
class PythonStatementNode(ChoiceStatementNode):
    """Represents a Python code statement."""
    code: str = ""
    
    def validate(self) -> List[str]:
        """Validate the Python statement."""
        errors = []
        if not self.code.strip():
            errors.append(f"Empty Python code at line {self.line_number}")
        return errors


@dataclass
class DialogueStatementNode(ChoiceStatementNode):
    """Represents a dialogue statement."""
    speaker: Optional[str] = None
    text: str = ""
    
    def validate(self) -> List[str]:
        """Validate the dialogue statement."""
        errors = []
        if not self.text.strip():
            errors.append(f"Empty dialogue text at line {self.line_number}")
        return errors


@dataclass
class VariableAssignmentNode(ChoiceStatementNode):
    """Represents a variable assignment."""
    variable: str = ""
    operator: str = "="  # =, +=, -=, etc.
    value: Any = None
    
    def validate(self) -> List[str]:
        """Validate the variable assignment."""
        errors = []
        if not self.variable:
            errors.append(f"Empty variable name in assignment at line {self.line_number}")
        if not self.operator:
            errors.append(f"Empty operator in assignment at line {self.line_number}")
        return errors


@dataclass
class NestedMenuNode(ChoiceStatementNode):
    """Represents a nested menu within a choice."""
    menu: Optional['MenuNode'] = None
    
    def validate(self) -> List[str]:
        """Validate the nested menu."""
        if self.menu:
            return self.menu.validate()
        return ["Nested menu is None"]
