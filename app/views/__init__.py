#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Views package for The Plot Thickens application.

This package contains all the UI views and widgets.
"""

# Import main views
from app.views.story_board_modular import StoryBoardWidget
from app.views.character_dialog import CharacterDialog
from app.views.main_window import MainWindow
from app.views.story_manager import StoryManagerWidget
from app.views.settings_dialog import SettingsDialog
from app.views.gallery_widget import GalleryWidget
from app.views.decision_points_tab import DecisionPointsTab
from app.views.relationship_editor import RelationshipEditorDialog
from app.views.relationship_details import RelationshipDetailsDialog
from app.views.relationship_types_manager import RelationshipTypesManager

__all__ = ['StoryBoardWidget', 'CharacterDialog', 'MainWindow', 'StoryManagerWidget', 'SettingsDialog', 'GalleryWidget', 'DecisionPointsTab', 'RelationshipEditorDialog', 'RelationshipDetailsDialog', 'RelationshipTypesManager'] 