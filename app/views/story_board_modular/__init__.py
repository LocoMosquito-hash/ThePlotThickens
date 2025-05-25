#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Story Board modular package.

This package provides the same interface as the original story_board.py module
while organizing the code into separate modules for better maintainability.
"""

# Import all the main classes to maintain compatibility
from .graphics_components import (
    CharacterCardSignals,
    CharacterCard,
    RoundedRectItem,
    RelationshipLine,
    BendPoint,
    load_bendpoints
)

from .scene_view import (
    StoryBoardScene,
    StoryBoardView
)

from .story_board_widget import StoryBoardWidget

from .utils import (
    create_vertical_line,
    calculate_grid_position,
    calculate_grid_layout,
    CARD_WIDTH,
    CARD_HEIGHT
)

# For compatibility, export the main widget class as the primary interface
__all__ = [
    'StoryBoardWidget',
    'StoryBoardScene', 
    'StoryBoardView',
    'CharacterCard',
    'CharacterCardSignals',
    'RelationshipLine',
    'RoundedRectItem',
    'BendPoint',
    'load_bendpoints',
    'create_vertical_line',
    'calculate_grid_position',
    'calculate_grid_layout',
    'CARD_WIDTH',
    'CARD_HEIGHT'
] 