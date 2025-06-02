#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimized Gallery Refresh System for The Plot Thickens application.

This module provides high-performance gallery refresh operations using parallel processing.
"""

import logging
from typing import List, Dict, Any, Set, Optional
import time

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap

from app.views.gallery.thumbnail_loader import ThumbnailLoader
from app.db_sqlite import (
    get_images_character_tags_batch, get_images_quick_events_batch,
    get_story_characters, get_image_scenes
)


class OptimizedGalleryRefresh(QObject):
    """Optimized gallery refresh system with parallel processing."""
    
    # Signals
    refresh_started = pyqtSignal()
    refresh_progress = pyqtSignal(str, int, int)  # stage, current, total
    thumbnails_ready = pyqtSignal(list)  # List of (image_id, pixmap) tuples
    refresh_completed = pyqtSignal()
    refresh_failed = pyqtSignal(str)  # error message
    
    def __init__(self, db_conn, gallery_widget, parent=None):
        """Initialize the optimized refresh system.
        
        Args:
            db_conn: Database connection
            gallery_widget: Reference to the gallery widget
            parent: Parent object
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.gallery_widget = gallery_widget
        self.thumbnail_loader = ThumbnailLoader(db_conn, max_workers=16)  # Aggressive parallelism for 745+ images
        
        # Progress tracking
        self.current_operation = ""
        self.is_refreshing = False
        
        # Connect thumbnail loader signals
        self.thumbnail_loader.thumbnail_loaded.connect(self._on_thumbnail_loaded)
        self.thumbnail_loader.batch_progress.connect(self._on_thumbnail_progress)
        self.thumbnail_loader.batch_completed.connect(self._on_thumbnails_completed)
        
        # Batch thumbnail results
        self.loaded_thumbnails = []
    
    def refresh_gallery_optimized(self, story_id: int, force_cache_rebuild: bool = False) -> None:
        """Perform optimized gallery refresh with parallel processing.
        
        Args:
            story_id: Story ID to refresh
            force_cache_rebuild: Whether to force rebuilding all caches
        """
        print(f"[OPTIMIZED_REFRESH] Starting optimized refresh for story {story_id}")
        
        if self.is_refreshing:
            logging.warning("Gallery refresh already in progress")
            return
        
        self.is_refreshing = True
        self.loaded_thumbnails = []
        self.refresh_started.emit()
        
        try:
            # Phase 1: Load image data from database (fast)
            self.current_operation = "Loading image data..."
            print(f"[OPTIMIZED_REFRESH] Phase 1: {self.current_operation}")
            self.refresh_progress.emit(self.current_operation, 0, 100)
            
            images = self._load_images_data(story_id)
            print(f"[OPTIMIZED_REFRESH] Loaded {len(images)} images from database")
            
            if not images:
                print(f"[OPTIMIZED_REFRESH] No images found, completing refresh")
                self.refresh_completed.emit()
                self.is_refreshing = False
                return
            
            # Phase 2: Batch load metadata (character tags, quick events) in parallel
            self.current_operation = "Loading metadata..."
            print(f"[OPTIMIZED_REFRESH] Phase 2: {self.current_operation}")
            self.refresh_progress.emit(self.current_operation, 15, 100)
            
            if force_cache_rebuild or not self._has_valid_cache(images):
                print(f"[OPTIMIZED_REFRESH] Loading metadata batch (force_rebuild={force_cache_rebuild})")
                self._load_metadata_batch(images, story_id)
            else:
                print(f"[OPTIMIZED_REFRESH] Using existing valid cache")
            
            # Phase 3: Apply filters and create placeholder UI immediately
            self.current_operation = "Preparing gallery..."
            print(f"[OPTIMIZED_REFRESH] Phase 3: {self.current_operation}")
            self.refresh_progress.emit(self.current_operation, 30, 100)
            
            # Apply filters first to only process visible images
            filtered_images = self.gallery_widget._filter_images(images)
            print(f"[OPTIMIZED_REFRESH] After filtering: {len(filtered_images)} images")
            
            # Store filtered images for later use
            self.gallery_widget.images = filtered_images
            
            # Phase 4: Create placeholder thumbnails immediately for instant feedback
            self.current_operation = "Creating layout..."
            print(f"[OPTIMIZED_REFRESH] Phase 4: {self.current_operation}")
            self.refresh_progress.emit(self.current_operation, 40, 100)
            
            # Create placeholder thumbnails immediately
            print(f"[OPTIMIZED_REFRESH] Creating placeholder thumbnails")
            self.gallery_widget.create_placeholder_thumbnails(filtered_images)
            
            # Phase 5: Start parallel thumbnail loading in background
            self.current_operation = "Loading thumbnails..."
            print(f"[OPTIMIZED_REFRESH] Phase 5: {self.current_operation}")
            self.refresh_progress.emit(self.current_operation, 50, 100)
            
            # For massive galleries, use burst loading for first thumbnails
            if len(filtered_images) >= self.gallery_widget.smart_refresh_manager.MASSIVE_GALLERY_THRESHOLD:
                print(f"[OPTIMIZED_REFRESH] Using BURST MODE for massive gallery ({len(filtered_images)} images)")
                # Load first batch with priority for immediate feedback
                burst_images = filtered_images[:self.gallery_widget.smart_refresh_manager.BURST_LOAD_COUNT]
                regular_images = filtered_images[self.gallery_widget.smart_refresh_manager.BURST_LOAD_COUNT:]
                
                # Start burst loading first
                if burst_images:
                    print(f"[OPTIMIZED_REFRESH] Burst loading first {len(burst_images)} thumbnails")
                    self.thumbnail_loader.load_thumbnails_batch(
                        burst_images, 
                        self.gallery_widget.pixmap_cache
                    )
                
                # Queue remaining images for regular loading
                if regular_images:
                    print(f"[OPTIMIZED_REFRESH] Queuing {len(regular_images)} remaining thumbnails for parallel loading")
                    QTimer.singleShot(100, lambda: self.thumbnail_loader.load_thumbnails_batch(
                        regular_images, 
                        self.gallery_widget.pixmap_cache
                    ))
            else:
                # Start thumbnail loading (this will emit signals as thumbnails complete)
                print(f"[OPTIMIZED_REFRESH] Starting standard parallel thumbnail loading for {len(filtered_images)} images")
                self.thumbnail_loader.load_thumbnails_batch(
                    filtered_images, 
                    self.gallery_widget.pixmap_cache
                )
            
        except Exception as e:
            print(f"[OPTIMIZED_REFRESH] Error during refresh: {e}")
            logging.exception(f"Error during optimized gallery refresh: {e}")
            self.refresh_failed.emit(str(e))
            self.is_refreshing = False
    
    def _load_images_data(self, story_id: int) -> List[Dict[str, Any]]:
        """Load image data from database with optimized query.
        
        Args:
            story_id: Story ID
            
        Returns:
            List of image data dictionaries
        """
        cursor = self.db_conn.cursor()
        
        # Single optimized query to get all image data
        query = """
            SELECT id, title, path, filename, created_at, width, height, is_featured, story_id
            FROM images
            WHERE story_id = ?
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (story_id,))
        
        images = []
        for row in cursor.fetchall():
            images.append({
                "id": row[0],
                "title": row[1],
                "path": row[2],
                "filename": row[3],
                "created_at": row[4],
                "timestamp": row[4],  # Backward compatibility
                "width": row[5],
                "height": row[6],
                "is_nsfw": False,  # Using is_featured as is_nsfw placeholder
                "story_id": row[8]
            })
        
        return images
    
    def _has_valid_cache(self, images: List[Dict[str, Any]]) -> bool:
        """Check if existing caches are valid for current images.
        
        Args:
            images: List of image data
            
        Returns:
            True if caches are valid, False otherwise
        """
        if not hasattr(self.gallery_widget, 'image_character_tags_cache'):
            return False
        
        if not hasattr(self.gallery_widget, 'image_quick_events_cache'):
            return False
        
        # Check if cache has entries for all images
        image_ids = {img["id"] for img in images}
        cached_character_ids = set(self.gallery_widget.image_character_tags_cache.keys())
        cached_event_ids = set(self.gallery_widget.image_quick_events_cache.keys())
        
        return image_ids.issubset(cached_character_ids) and image_ids.issubset(cached_event_ids)
    
    def _load_metadata_batch(self, images: List[Dict[str, Any]], story_id: int) -> None:
        """Load metadata in optimized batches.
        
        Args:
            images: List of image data
            story_id: Story ID
        """
        image_ids = [img["id"] for img in images]
        
        # Load story characters once
        self.gallery_widget.story_characters = {
            char["id"]: char 
            for char in get_story_characters(self.db_conn, story_id)
        }
        
        # Batch load character tags for all images
        self.gallery_widget.image_character_tags_cache = get_images_character_tags_batch(
            self.db_conn, image_ids
        )
        
        # Batch load quick events for all images
        self.gallery_widget.image_quick_events_cache = get_images_quick_events_batch(
            self.db_conn, image_ids
        )
    
    def _on_thumbnail_loaded(self, image_id: int, pixmap: QPixmap) -> None:
        """Handle individual thumbnail loaded signal.
        
        Args:
            image_id: Image ID
            pixmap: Loaded pixmap
        """
        # Cache the pixmap
        self.gallery_widget.pixmap_cache[image_id] = pixmap
        
        # Store for batch update
        self.loaded_thumbnails.append((image_id, pixmap))
        
        # Update UI in smaller batches to keep it responsive (every 5 thumbnails instead of 10)
        if len(self.loaded_thumbnails) % 5 == 0:  # Update every 5 thumbnails
            self._update_ui_batch()
    
    def _on_thumbnail_progress(self, current: int, total: int) -> None:
        """Handle thumbnail loading progress.
        
        Args:
            current: Current loaded count
            total: Total thumbnail count
        """
        # Update progress more granularly (50-90% range for thumbnail loading)
        progress = 50 + int((current / total) * 40)
        
        # Show more detailed progress information
        percent = int((current / total) * 100)
        self.refresh_progress.emit(f"Loading thumbnails... {current}/{total} ({percent}%)", progress, 100)
    
    def _on_thumbnails_completed(self) -> None:
        """Handle thumbnail loading completion."""
        # Final UI update with any remaining thumbnails
        if self.loaded_thumbnails:
            self._update_ui_batch()
        
        # Phase 4: Final UI setup
        self.current_operation = "Finalizing..."
        self.refresh_progress.emit(self.current_operation, 95, 100)
        
        # Let the UI update complete, then finish
        QTimer.singleShot(100, self._complete_refresh)
    
    def _update_ui_batch(self) -> None:
        """Update UI with a batch of loaded thumbnails."""
        if not self.loaded_thumbnails:
            return
        
        # Emit batch signal for UI to process
        self.thumbnails_ready.emit(self.loaded_thumbnails.copy())
        self.loaded_thumbnails.clear()
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def _complete_refresh(self) -> None:
        """Complete the refresh operation."""
        self.refresh_progress.emit("Complete", 100, 100)
        self.refresh_completed.emit()
        self.is_refreshing = False
    
    def cancel_refresh(self) -> None:
        """Cancel ongoing refresh operation."""
        if self.is_refreshing:
            self.thumbnail_loader.cancel_loading()
            self.is_refreshing = False


class SmartRefreshManager(QObject):
    """Intelligent refresh manager that chooses the best refresh strategy."""
    
    def __init__(self, gallery_widget, parent=None):
        """Initialize the smart refresh manager.
        
        Args:
            gallery_widget: Gallery widget reference
            parent: Parent object
        """
        super().__init__(parent)
        self.gallery_widget = gallery_widget
        self.optimized_refresh = OptimizedGalleryRefresh(
            gallery_widget.db_conn, 
            gallery_widget, 
            self
        )
        
        # Performance thresholds
        self.LARGE_GALLERY_THRESHOLD = 50  # Lower threshold - use optimization sooner
        self.MASSIVE_GALLERY_THRESHOLD = 300  # Use aggressive optimization for 300+ images
        self.BURST_LOAD_COUNT = 20  # Load first 20 thumbnails immediately for instant feedback
        
        # Connect optimized refresh signals
        self.optimized_refresh.refresh_started.connect(self._on_optimized_refresh_started)
        self.optimized_refresh.refresh_progress.connect(self._on_optimized_refresh_progress)
        self.optimized_refresh.thumbnails_ready.connect(self._on_thumbnails_ready)
        self.optimized_refresh.refresh_completed.connect(self._on_optimized_refresh_completed)
        self.optimized_refresh.refresh_failed.connect(self._on_optimized_refresh_failed)
        
        # Status bar access (no more progress dialog)
        self._status_bar = None
    
    def _get_status_bar(self):
        """Get the main window's status bar.
        
        Returns:
            Status bar or None if not available
        """
        if self._status_bar:
            return self._status_bar
            
        # Try to get status bar from main window through gallery widget
        try:
            # Navigate up the widget hierarchy to find the main window
            parent = self.gallery_widget.parent()
            while parent:
                if hasattr(parent, 'status_bar'):
                    self._status_bar = parent.status_bar
                    return self._status_bar
                parent = parent.parent()
        except Exception as e:
            logging.debug(f"Could not find status bar: {e}")
        
        return None
    
    def refresh_gallery_smart(self, operation_type: str = "general") -> None:
        """Intelligently choose refresh strategy based on gallery size.
        
        Args:
            operation_type: Type of operation ('filter', 'batch_tag', 'scene_move', 'general')
        """
        if not self.gallery_widget.story_id:
            logging.warning("No story selected for refresh")
            return
        
        # Get image count for decision making
        image_count = 0
        try:
            cursor = self.gallery_widget.db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM images WHERE story_id = ?", (self.gallery_widget.story_id,))
            result = cursor.fetchone()
            image_count = result[0] if result else 0
        except Exception as e:
            logging.error(f"Error getting image count: {e}")
            # Fallback to current images count
            image_count = len(self.gallery_widget.images) if self.gallery_widget.images else 0
        
        print(f"[SMART_REFRESH] Smart refresh for {image_count} images, operation: {operation_type}")
        print(f"[SMART_REFRESH] Large gallery threshold: {self.LARGE_GALLERY_THRESHOLD}")
        
        # Choose strategy based on image count and operation type
        if image_count >= self.LARGE_GALLERY_THRESHOLD:
            # Use optimized refresh for large galleries
            print(f"[SMART_REFRESH] Using OPTIMIZED refresh (image_count={image_count} >= {self.LARGE_GALLERY_THRESHOLD})")
            force_cache_rebuild = operation_type in ['batch_tag', 'scene_move']
            self._refresh_optimized(force_cache_rebuild)
        else:
            # Use standard refresh for small galleries
            print(f"[SMART_REFRESH] Using STANDARD refresh (image_count={image_count} < {self.LARGE_GALLERY_THRESHOLD})")
            self._refresh_standard()
    
    def _refresh_optimized(self, force_cache_rebuild: bool = False) -> None:
        """Perform optimized refresh with status bar messages."""
        # Show status message instead of popup dialog
        status_bar = self._get_status_bar()
        if status_bar:
            status_bar.showMessage("Refreshing gallery...")
        
        # Start optimized refresh
        self.optimized_refresh.refresh_gallery_optimized(
            self.gallery_widget.story_id,
            force_cache_rebuild
        )
    
    def _refresh_standard(self) -> None:
        """Perform standard refresh (fallback for small galleries)."""
        # Show status message for standard refresh too
        status_bar = self._get_status_bar()
        if status_bar:
            status_bar.showMessage("Refreshing gallery...")
            
        # Call the actual legacy method
        self.gallery_widget.load_images()
        
        # Complete status message
        if status_bar:
            status_bar.showMessage("Gallery refresh completed", 3000)
    
    def _on_optimized_refresh_started(self) -> None:
        """Handle optimized refresh started."""
        # Status message already shown in _refresh_optimized, nothing more needed
        pass
    
    def _on_optimized_refresh_progress(self, stage: str, current: int, total: int) -> None:
        """Handle optimized refresh progress.
        
        Args:
            stage: Current stage description
            current: Current progress
            total: Total progress
        """
        # Show detailed progress in status bar instead of popup
        status_bar = self._get_status_bar()
        if status_bar:
            percent = int((current / total) * 100) if total > 0 else 0
            status_bar.showMessage(f"{stage} ({percent}%)")
    
    def _on_thumbnails_ready(self, thumbnails: List[tuple]) -> None:
        """Handle batch of thumbnails ready.
        
        Args:
            thumbnails: List of (image_id, pixmap) tuples
        """
        # Update existing thumbnails progressively
        for image_id, pixmap in thumbnails:
            if image_id in self.gallery_widget.thumbnails:
                # Update existing thumbnail widget with the real pixmap
                thumbnail_widget = self.gallery_widget.thumbnails[image_id]
                thumbnail_widget.update_pixmap(pixmap)
                
                # Ensure the widget is visible and properly styled
                thumbnail_widget.setVisible(True)
                
        # Process events to keep UI responsive during updates
        QApplication.processEvents()
    
    def _on_optimized_refresh_completed(self) -> None:
        """Handle optimized refresh completion."""
        # Show completion message in status bar
        status_bar = self._get_status_bar()
        if status_bar:
            status_bar.showMessage("Gallery refresh completed", 3000)
        
        # Final UI updates
        try:
            self.gallery_widget.update_thumbnail_visibility()
            self.gallery_widget.update_filter_status()
            
            # Set focus back to gallery for keyboard navigation
            self.gallery_widget.setFocus()
            
        except Exception as e:
            logging.error(f"Error during final UI updates: {e}")
        
        logging.info("Optimized gallery refresh completed successfully")
    
    def _on_optimized_refresh_failed(self, error: str) -> None:
        """Handle optimized refresh failure.
        
        Args:
            error: Error message
        """
        # Show error in status bar
        status_bar = self._get_status_bar()
        if status_bar:
            status_bar.showMessage(f"Gallery refresh failed: {error}", 5000)
        
        logging.error(f"Optimized refresh failed: {error}")
        
        # Fallback to standard refresh - call load_images directly to avoid recursion
        try:
            self.gallery_widget.load_images()
            # Show fallback success message
            if status_bar:
                status_bar.showMessage("Gallery refresh completed (fallback mode)", 3000)
        except Exception as fallback_error:
            logging.error(f"Fallback refresh also failed: {fallback_error}")
            if status_bar:
                status_bar.showMessage(f"Gallery refresh failed completely", 5000)
            self.gallery_widget.show_error("Refresh Failed", 
                f"Both optimized and standard refresh failed.\nOptimized: {error}\nStandard: {fallback_error}") 