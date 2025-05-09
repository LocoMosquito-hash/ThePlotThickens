"""
Gallery module for The Plot Thickens application.

This package contains all gallery-related widgets and functionality,
organized into a modular structure with the following components:

- core: Main GalleryWidget implementation
- thumbnails: Thumbnail and separator widgets
- tagging: Image tagging functionality
- character: Character-related widgets
- dialogs: Dialog windows
"""

# Core gallery widget
from app.views.gallery.core import GalleryWidget

# Basic widgets
from app.views.gallery.thumbnails import ThumbnailWidget, SeparatorWidget
from app.views.gallery.tagging import TaggableImageLabel, GraphicsTagView

# Character-related widgets
from app.views.gallery.character import (
    CharacterListWidget,
    OnSceneCharacterListWidget,
    CharacterTagCompleter
)

# Dialog windows
from app.views.gallery.dialogs import (
    CharacterSelectionDialog,
    ImageDetailDialog,
    QuickEventSelectionDialog,
    QuickEventEditor,
    RegionSelectionDialog,
    TagSuggestionDialog, 
    TagPositionDialog,
    SceneSelectionDialog,
    GalleryFilterDialog
)

__all__ = [
    # Core widget
    'GalleryWidget',
    
    # Basic widgets
    'ThumbnailWidget',
    'SeparatorWidget',
    'TaggableImageLabel',
    'GraphicsTagView',
    
    # Character widgets
    'CharacterListWidget',
    'OnSceneCharacterListWidget',
    'CharacterTagCompleter',
    
    # Dialog windows
    'CharacterSelectionDialog',
    'ImageDetailDialog',
    'QuickEventSelectionDialog',
    'QuickEventEditor',
    'RegionSelectionDialog',
    'TagSuggestionDialog',
    'TagPositionDialog',
    'SceneSelectionDialog',
    'GalleryFilterDialog'
] 