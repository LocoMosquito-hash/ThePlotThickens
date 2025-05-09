"""
This package contains character-related widgets and utilities for the gallery.
"""

from app.views.gallery.character.widgets import (
    CharacterListWidget,
    OnSceneCharacterListWidget
)
from app.views.gallery.character.completer import CharacterTagCompleter

__all__ = [
    'CharacterListWidget',
    'OnSceneCharacterListWidget',
    'CharacterTagCompleter'
]
