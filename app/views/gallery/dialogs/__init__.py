"""
This package contains dialog windows for the gallery module.
"""

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

__all__ = [
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
