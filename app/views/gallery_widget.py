"""
DEPRECATED: This module is maintained for backward compatibility only.
All classes have been moved to the app.views.gallery package structure.
Please update your imports to use the new module paths.
"""

import warnings

# Show deprecation warning
warnings.warn(
    "The 'gallery_widget' module is deprecated. "
    "Please use the new modular imports from 'app.views.gallery' package instead.",
    DeprecationWarning,
    stacklevel=2
)

# Import all classes from their new locations
from app.views.gallery.core import GalleryWidget
from app.views.gallery.thumbnails import ThumbnailWidget, SeparatorWidget
from app.views.gallery.tagging import TaggableImageLabel, GraphicsTagView
from app.views.gallery.character.widgets import (
    CharacterListWidget, 
    OnSceneCharacterListWidget
)
from app.views.gallery.character.completer import CharacterTagCompleter
from app.views.gallery.dialogs.character_selection import CharacterSelectionDialog
from app.views.gallery.dialogs.image_detail import ImageDetailDialog
from app.views.gallery.dialogs.quick_event_dialog import (
    QuickEventSelectionDialog,
    QuickEventEditor
)
from app.views.gallery.dialogs.region_selection import RegionSelectionDialog
from app.views.gallery.dialogs.tag_suggestion import TagSuggestionDialog
from app.views.gallery.dialogs.tag_position import TagPositionDialog
from app.views.gallery.dialogs.scene_selection import SceneSelectionDialog
from app.views.gallery.dialogs.filter_dialog import GalleryFilterDialog

# Re-export all classes to maintain the same API
__all__ = [
    'GalleryWidget',
    'ThumbnailWidget',
    'SeparatorWidget',
    'TaggableImageLabel',
    'GraphicsTagView',
    'CharacterListWidget',
    'OnSceneCharacterListWidget',
    'CharacterTagCompleter',
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
