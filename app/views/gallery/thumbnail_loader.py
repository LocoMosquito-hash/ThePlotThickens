#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Threaded Thumbnail Loader for The Plot Thickens application.

This module provides parallel thumbnail loading to improve gallery performance.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, QMutex, QMutexLocker
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QApplication

from app.db_sqlite import get_story_folder_paths


class ThumbnailLoadResult:
    """Result of a thumbnail loading operation."""
    
    def __init__(self, image_id: int, pixmap: Optional[QPixmap] = None, 
                 error: Optional[str] = None):
        self.image_id = image_id
        self.pixmap = pixmap
        self.error = error
        self.success = pixmap is not None


class ThumbnailLoader(QObject):
    """Threaded thumbnail loader for parallel processing."""
    
    # Signals
    thumbnail_loaded = pyqtSignal(int, QPixmap)  # image_id, pixmap
    batch_progress = pyqtSignal(int, int)  # loaded_count, total_count
    batch_completed = pyqtSignal()
    
    def __init__(self, db_conn, max_workers: int = 4):
        """Initialize the thumbnail loader.
        
        Args:
            db_conn: Database connection
            max_workers: Maximum number of worker threads
        """
        super().__init__()
        self.db_conn = db_conn
        self.max_workers = max_workers
        self.mutex = QMutex()
        self.is_loading = False
        self.cancel_requested = False
        
        # Cache for story folder paths
        self._folder_cache = {}
    
    def load_thumbnails_batch(self, images: List[Dict[str, Any]], 
                             pixmap_cache: Dict[int, QPixmap]) -> None:
        """Load thumbnails for a batch of images in parallel.
        
        Args:
            images: List of image data dictionaries
            pixmap_cache: Existing pixmap cache to check
        """
        with QMutexLocker(self.mutex):
            if self.is_loading:
                logging.warning("Thumbnail loading already in progress")
                return
            self.is_loading = True
            self.cancel_requested = False
        
        # Filter out images that already have cached pixmaps
        images_to_load = []
        for image in images:
            image_id = image["id"]
            if image_id not in pixmap_cache:
                images_to_load.append(image)
        
        if not images_to_load:
            self.batch_completed.emit()
            with QMutexLocker(self.mutex):
                self.is_loading = False
            return
        
        # Start loading in a separate thread
        QTimer.singleShot(0, lambda: self._load_thumbnails_threaded(images_to_load))
    
    def cancel_loading(self) -> None:
        """Cancel ongoing thumbnail loading."""
        with QMutexLocker(self.mutex):
            self.cancel_requested = True
    
    def _load_thumbnails_threaded(self, images: List[Dict[str, Any]]) -> None:
        """Load thumbnails using ThreadPoolExecutor."""
        total_count = len(images)
        loaded_count = 0
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all thumbnail loading tasks
                future_to_image = {
                    executor.submit(self._load_single_thumbnail, image): image 
                    for image in images
                }
                
                # Process completed tasks
                for future in as_completed(future_to_image):
                    # Check for cancellation
                    with QMutexLocker(self.mutex):
                        if self.cancel_requested:
                            break
                    
                    image = future_to_image[future]
                    
                    try:
                        result = future.result()
                        if result.success:
                            # Emit signal on main thread
                            self.thumbnail_loaded.emit(result.image_id, result.pixmap)
                        else:
                            logging.warning(f"Failed to load thumbnail for image {result.image_id}: {result.error}")
                    except Exception as e:
                        logging.exception(f"Error loading thumbnail for image {image['id']}: {e}")
                    
                    loaded_count += 1
                    
                    # Only update progress and process events every few images to reduce overhead
                    if loaded_count % 3 == 0 or loaded_count == total_count:  # Every 3 images or at completion
                        self.batch_progress.emit(loaded_count, total_count)
                        
                        # Process events less frequently to reduce overhead with many workers
                        QApplication.processEvents()
        
        except Exception as e:
            logging.exception(f"Error in threaded thumbnail loading: {e}")
        
        finally:
            self.batch_completed.emit()
            with QMutexLocker(self.mutex):
                self.is_loading = False
    
    def _load_single_thumbnail(self, image: Dict[str, Any]) -> ThumbnailLoadResult:
        """Load a single thumbnail (runs in worker thread).
        
        Args:
            image: Image data dictionary
            
        Returns:
            ThumbnailLoadResult
        """
        image_id = image["id"]
        
        try:
            # Get image details
            filename = image.get('filename')
            img_folder = image.get('path')
            story_id = image.get('story_id')
            
            if not filename or not img_folder or not story_id:
                return ThumbnailLoadResult(image_id, error="Missing path, filename, or story_id")
            
            # Get story folder paths (with caching)
            folder_paths = self._get_story_folder_paths_cached(story_id)
            if not folder_paths:
                return ThumbnailLoadResult(image_id, error="Could not determine folder paths")
            
            # Get paths to original image and thumbnail
            original_path = os.path.join(folder_paths['images_folder'], filename)
            thumbnail_path = os.path.join(folder_paths['thumbnails_folder'], filename)
            
            # Try to load existing thumbnail first
            if os.path.exists(thumbnail_path):
                pixmap = QPixmap(thumbnail_path)
                if not pixmap.isNull():
                    return ThumbnailLoadResult(image_id, pixmap)
            
            # If thumbnail doesn't exist, generate it
            if os.path.exists(original_path):
                return self._generate_thumbnail_for_image(image_id, original_path, thumbnail_path)
            
            # Try alternative path (legacy support)
            alt_path = os.path.join(img_folder, filename)
            if os.path.exists(alt_path) and alt_path != original_path:
                return self._generate_thumbnail_for_image(image_id, alt_path, thumbnail_path)
            
            return ThumbnailLoadResult(image_id, error=f"Image file not found: {original_path}")
        
        except Exception as e:
            return ThumbnailLoadResult(image_id, error=str(e))
    
    def _get_story_folder_paths_cached(self, story_id: int) -> Optional[Dict[str, str]]:
        """Get story folder paths with caching.
        
        Args:
            story_id: Story ID
            
        Returns:
            Dictionary with folder paths or None if error
        """
        if story_id in self._folder_cache:
            return self._folder_cache[story_id]
        
        try:
            # Get story data from database
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
            story_data = cursor.fetchone()
            
            if not story_data:
                return None
            
            # Get folder paths
            folder_paths = get_story_folder_paths(dict(story_data))
            self._folder_cache[story_id] = folder_paths
            return folder_paths
        
        except Exception as e:
            logging.exception(f"Error getting folder paths for story {story_id}: {e}")
            return None
    
    def _generate_thumbnail_for_image(self, image_id: int, original_path: str, 
                                    thumbnail_path: str) -> ThumbnailLoadResult:
        """Generate thumbnail for an image.
        
        Args:
            image_id: Image ID
            original_path: Path to original image
            thumbnail_path: Path where thumbnail should be saved
            
        Returns:
            ThumbnailLoadResult
        """
        try:
            # Load original image
            original_image = QImage(original_path)
            if original_image.isNull():
                return ThumbnailLoadResult(image_id, error=f"Failed to load image: {original_path}")
            
            # Generate thumbnail
            thumbnail = self._generate_thumbnail(original_image)
            
            # Ensure thumbnails directory exists
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            
            # Save thumbnail
            if thumbnail.save(thumbnail_path, "PNG"):
                pixmap = QPixmap.fromImage(thumbnail)
                return ThumbnailLoadResult(image_id, pixmap)
            else:
                # Even if save failed, return the pixmap
                pixmap = QPixmap.fromImage(thumbnail)
                return ThumbnailLoadResult(image_id, pixmap)
        
        except Exception as e:
            return ThumbnailLoadResult(image_id, error=str(e))
    
    def _generate_thumbnail(self, image: QImage, max_dimension: int = 320) -> QImage:
        """Generate a thumbnail from an image.
        
        Args:
            image: Source image
            max_dimension: Maximum dimension (width or height) for the thumbnail
            
        Returns:
            Thumbnail image
        """
        # Calculate the target size while maintaining aspect ratio
        width = image.width()
        height = image.height()
        
        if width > height:
            # Landscape
            new_width = min(width, max_dimension)
            new_height = int((height * new_width) / width)
        else:
            # Portrait or square
            new_height = min(height, max_dimension)
            new_width = int((width * new_height) / height)
        
        # Scale the image
        thumbnail = image.scaled(
            new_width, 
            new_height, 
            aspectRatioMode=1,  # Qt.AspectRatioMode.KeepAspectRatio
            transformMode=1     # Qt.TransformationMode.SmoothTransformation
        )
        
        return thumbnail


class BatchThumbnailLoader(QThread):
    """Thread for batch thumbnail loading with progress reporting."""
    
    thumbnail_ready = pyqtSignal(int, QPixmap)  # image_id, pixmap
    progress_updated = pyqtSignal(int, int)  # current, total
    loading_completed = pyqtSignal()
    
    def __init__(self, db_conn, images: List[Dict[str, Any]], 
                 pixmap_cache: Dict[int, QPixmap], parent=None):
        """Initialize the batch loader.
        
        Args:
            db_conn: Database connection
            images: List of image data dictionaries
            pixmap_cache: Existing pixmap cache
            parent: Parent object
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.images = images
        self.pixmap_cache = pixmap_cache
        self.loader = ThumbnailLoader(db_conn, max_workers=4)
        
        # Connect signals
        self.loader.thumbnail_loaded.connect(self.thumbnail_ready)
        self.loader.batch_progress.connect(self.progress_updated)
        self.loader.batch_completed.connect(self.loading_completed)
        self.loader.batch_completed.connect(self.quit)
    
    def run(self):
        """Run the batch loading."""
        self.loader.load_thumbnails_batch(self.images, self.pixmap_cache)
        self.exec()  # Keep thread alive until loading completes 