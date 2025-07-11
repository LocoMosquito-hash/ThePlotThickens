#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Copier Utility for The Plot Thickens application.

This module provides functionality to copy discovered media files from 
the Dialog Search tab to the Screenshots tab's image stack, with proper
timestamp manipulation to preserve script order and duplicate detection.
"""

import os
import shutil
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QProgressDialog, QApplication, QMessageBox


class MediaCopyWorker(QThread):
    """Worker thread for copying media files to image stack."""
    
    # Signals
    progress_updated = pyqtSignal(int)  # Progress percentage (0-100)
    status_updated = pyqtSignal(str)   # Status message
    file_copied = pyqtSignal(str)      # File path that was copied
    copy_completed = pyqtSignal(int, int)  # (copied_count, skipped_count)
    copy_failed = pyqtSignal(str)      # Error message
    
    def __init__(self, media_assets: List[Dict[str, Any]], 
                 skip_duplicates: bool = True,
                 image_stack_folder: str = "image-stack",
                 parent=None):
        """Initialize the media copy worker.
        
        Args:
            media_assets: List of media asset dictionaries with 'path', 'type', 'name'
            skip_duplicates: Whether to skip files that already exist
            image_stack_folder: Target folder for copying files
            parent: Parent object
        """
        super().__init__(parent)
        self.media_assets = media_assets
        self.skip_duplicates = skip_duplicates
        self.image_stack_folder = image_stack_folder
        self.cancelled = False
        
        # Supported file extensions
        self.supported_image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}
        self.supported_video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
        
    def cancel(self):
        """Cancel the copy operation."""
        self.cancelled = True
        
    def run(self):
        """Run the copy operation."""
        try:
            # Ensure image stack folder exists
            os.makedirs(self.image_stack_folder, exist_ok=True)
            
            # Filter and prepare media files
            valid_media = self._filter_valid_media()
            if not valid_media:
                self.copy_failed.emit("No valid media files found to copy")
                return
                
            self.status_updated.emit(f"Preparing to copy {len(valid_media)} media files...")
            
            # Get existing files for duplicate checking
            existing_files = set()
            if self.skip_duplicates:
                existing_files = self._get_existing_files()
                
            # Calculate timestamps for preserving script order
            timestamps = self._calculate_timestamps(len(valid_media))
            
            copied_count = 0
            skipped_count = 0
            
            for i, (asset, timestamp) in enumerate(zip(valid_media, timestamps)):
                if self.cancelled:
                    break
                    
                # Update progress
                progress = int((i / len(valid_media)) * 100)
                self.progress_updated.emit(progress)
                
                asset_path = asset.get('path', '')
                if not asset_path or not os.path.exists(asset_path):
                    skipped_count += 1
                    continue
                    
                # Generate destination filename
                dest_filename = self._generate_destination_filename(asset, timestamp)
                dest_path = os.path.join(self.image_stack_folder, dest_filename)
                
                # Check for duplicates
                if self.skip_duplicates and dest_filename in existing_files:
                    self.status_updated.emit(f"Skipping duplicate: {dest_filename}")
                    skipped_count += 1
                    continue
                    
                # Copy file
                try:
                    self.status_updated.emit(f"Copying: {os.path.basename(asset_path)}")
                    self._safe_copy_file(asset_path, dest_path)
                    
                    # Set file timestamps
                    self._set_file_timestamp(dest_path, timestamp)
                    
                    # Create metadata file with original asset name
                    self._create_metadata_file(dest_path, asset)
                    
                    self.file_copied.emit(dest_path)
                    copied_count += 1
                    
                except Exception as e:
                    self.status_updated.emit(f"Failed to copy {os.path.basename(asset_path)}: {str(e)}")
                    skipped_count += 1
                    
            self.progress_updated.emit(100)
            
            if not self.cancelled:
                self.copy_completed.emit(copied_count, skipped_count)
            else:
                self.copy_failed.emit("Copy operation was cancelled")
                
        except Exception as e:
            self.copy_failed.emit(f"Copy operation failed: {str(e)}")
            
    def _filter_valid_media(self) -> List[Dict[str, Any]]:
        """Filter media assets to only include supported image and video files.
        
        Returns:
            List of valid media assets
        """
        valid_media = []
        
        for asset in self.media_assets:
            asset_path = asset.get('path', '')
            if not asset_path or not os.path.exists(asset_path):
                continue
                
            file_ext = Path(asset_path).suffix.lower()
            if file_ext in self.supported_image_extensions or file_ext in self.supported_video_extensions:
                valid_media.append(asset)
                
        return valid_media
        
    def _get_existing_files(self) -> set:
        """Get set of existing filenames in the image stack folder.
        
        Returns:
            Set of existing filenames
        """
        existing_files = set()
        try:
            if os.path.exists(self.image_stack_folder):
                for filename in os.listdir(self.image_stack_folder):
                    if os.path.isfile(os.path.join(self.image_stack_folder, filename)):
                        existing_files.add(filename)
        except Exception:
            pass  # Ignore errors, assume no existing files
            
        return existing_files
        
    def _calculate_timestamps(self, count: int) -> List[float]:
        """Calculate timestamps for files to preserve script order.
        
        Last file gets current time, first file gets last_time - 1 second,
        files in between get fractional timestamps.
        
        Args:
            count: Number of files
            
        Returns:
            List of timestamps (Unix time)
        """
        if count == 0:
            return []
        elif count == 1:
            return [time.time()]
            
        # Last file gets current timestamp
        end_time = time.time()
        # First file gets timestamp 1 second earlier
        start_time = end_time - 1.0
        
        # Calculate incremental timestamps
        timestamps = []
        for i in range(count):
            if count == 1:
                timestamp = end_time
            else:
                # Linear interpolation between start and end times
                fraction = i / (count - 1)
                timestamp = start_time + (end_time - start_time) * fraction
            timestamps.append(timestamp)
            
        return timestamps
        
    def _generate_destination_filename(self, asset: Dict[str, Any], timestamp: float) -> str:
        """Generate destination filename for a media asset.
        
        Args:
            asset: Media asset dictionary
            timestamp: Timestamp for the file
            
        Returns:
            Generated filename
        """
        asset_path = asset.get('path', '')
        file_ext = Path(asset_path).suffix.lower()
        
        # Convert timestamp to formatted string
        dt = datetime.fromtimestamp(timestamp)
        timestamp_str = dt.strftime("%Y%m%d_%H%M%S")
        
        # Add microseconds for uniqueness
        microsecond_str = f"{dt.microsecond:06d}"[:3]  # First 3 digits
        
        # Generate filename: media_YYYYMMDD_HHMMSS_XXX.ext
        filename = f"media_{timestamp_str}_{microsecond_str}{file_ext}"
        
        return filename
        
    def _safe_copy_file(self, src_path: str, dest_path: str):
        """Safely copy a file with error handling.
        
        Args:
            src_path: Source file path
            dest_path: Destination file path
            
        Raises:
            Exception: If copy fails
        """
        try:
            # Use shutil.copy2 to preserve as much metadata as possible
            shutil.copy2(src_path, dest_path)
            
        except Exception as e:
            # If copy2 fails, try basic copy
            try:
                shutil.copy(src_path, dest_path)
            except Exception:
                # If that fails too, re-raise original exception
                raise e
                
    def _set_file_timestamp(self, file_path: str, timestamp: float):
        """Set file modification and access timestamps.
        
        Args:
            file_path: Path to the file
            timestamp: Timestamp to set
        """
        try:
            # Set both access time and modification time
            os.utime(file_path, (timestamp, timestamp))
        except Exception:
            # Ignore errors - timestamp setting is not critical
            pass
            
    def _create_metadata_file(self, media_file_path: str, asset: Dict[str, Any]):
        """Create a metadata file alongside the copied media file.
        
        Args:
            media_file_path: Path to the copied media file
            asset: Original asset dictionary with metadata
        """
        try:
            import json
            
            # Create metadata filename (same name but with .meta extension)
            base_path = os.path.splitext(media_file_path)[0]
            metadata_path = f"{base_path}.meta"
            
            # Extract dialog context if available
            dialog_context = self._extract_dialog_context(asset)
            
            # Debug output to see what asset data we're getting
            print(f"[DEBUG] Creating metadata for asset: {asset.get('name', 'unknown')}")
            print(f"[DEBUG] Asset keys: {list(asset.keys())}")
            line_num = asset.get('line_number', asset.get('line', 0))
            print(f"[DEBUG] Line number found: {line_num}")
            
            # Extract relevant metadata from asset
            metadata = {
                'original_asset_name': asset.get('name', ''),
                'asset_type': asset.get('type', 'unknown'),
                'asset_category': asset.get('category', 'unknown'),
                'source_file': asset.get('file', ''),
                'source_line': line_num,
                'usage_type': asset.get('usage_type', 'unknown'),
                'dialog_context': dialog_context,
                'created_at': datetime.now().isoformat()
            }
            
            # Write metadata file
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            # Don't fail the copy operation if metadata creation fails
            print(f"Warning: Failed to create metadata file for {media_file_path}: {e}")
            pass

    def _extract_dialog_context(self, asset: Dict[str, Any]) -> str:
        """Extract dialog context that appears after this asset in the source script.
        
        Args:
            asset: Asset dictionary containing source file and line information
            
        Returns:
            Dialog context string, or empty string if none found
        """
        try:
            source_file = asset.get('file', '')
            # Try both 'line_number' and 'line' fields for compatibility
            source_line = asset.get('line_number', asset.get('line', 0))
            asset_name = asset.get('name', '')
            
            print(f"[DEBUG] Dialog extraction for {asset_name}: file={source_file}, line={source_line}")
            
            if not source_file or source_line <= 0:
                print(f"[DEBUG] Early return: no file or invalid line number")
                return ""
            
            # Build full path - the source_file might be relative to the game directory
            # Try to infer the game directory from the media asset paths
            full_source_path = source_file
            if not os.path.isabs(source_file):
                # Try to find the game directory by looking at other assets
                game_dir = None
                for media_asset in self.media_assets:
                    media_path = media_asset.get('path', '')
                    if media_path and os.path.exists(media_path):
                        # Work backwards from media path to find game directory
                        # Example: T:/AG/LastCall-0.4-pc/game/chapters/chapter3/images/...
                        # We want: T:/AG/LastCall-0.4-pc/game
                        path_parts = media_path.replace('\\', '/').split('/')
                        for i, part in enumerate(path_parts):
                            if part == 'game':
                                game_dir = '/'.join(path_parts[:i+1])
                                break
                        if game_dir:
                            break
                
                if game_dir:
                    # Convert game_dir back to proper path separators for the OS
                    game_dir = game_dir.replace('/', os.sep)
                    full_source_path = os.path.join(game_dir, source_file)
                    print(f"[DEBUG] Built full path using game directory: {full_source_path}")
                else:
                    # Fallback: try common locations relative to current directory
                    current_dir = os.getcwd()
                    potential_paths = [
                        os.path.join(current_dir, source_file),
                        os.path.join(current_dir, 'game', source_file)
                    ]
                    for path in potential_paths:
                        if os.path.exists(path):
                            full_source_path = path
                            print(f"[DEBUG] Found file at fallback path: {full_source_path}")
                            break
            
            print(f"[DEBUG] Trying to read file: {full_source_path}")
            if not os.path.exists(full_source_path):
                print(f"[DEBUG] File not found: {full_source_path}")
                return ""
                
            # Read the source file
            with open(full_source_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Find dialog lines after the asset line
            dialog_lines = []
            start_line = source_line - 1  # Convert to 0-based index
            
            # Look for dialog lines after the asset line
            print(f"[DEBUG] Scanning lines from {start_line + 1} to {len(lines)} for dialog")
            for i in range(start_line + 1, len(lines)):
                line = lines[i].strip()
                print(f"[DEBUG] Line {i+1}: '{line}'")
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    print(f"[DEBUG] Skipping empty/comment line")
                    continue
                    
                # Stop if we hit another asset line (scene, show, etc.)
                if self._is_asset_line(line):
                    print(f"[DEBUG] Hit another asset line, stopping: {line}")
                    break
                    
                # Stop if we hit control flow (jump, call, return, etc.)
                if self._is_control_flow_line(line):
                    print(f"[DEBUG] Hit control flow line, stopping: {line}")
                    break
                    
                # Check if this is a dialog line
                if self._is_dialog_line(line):
                    print(f"[DEBUG] Found dialog line: {line}")
                    dialog_lines.append(line)
                else:
                    print(f"[DEBUG] Not a dialog line: {line}")
                    
                # Stop after finding a reasonable number of dialog lines
                if len(dialog_lines) >= 5:  # Limit to avoid overly long context
                    print(f"[DEBUG] Hit max dialog lines limit")
                    break
                    
            # Join dialog lines with newlines
            if dialog_lines:
                result = '\n'.join(dialog_lines)
                print(f"[DEBUG] Returning dialog context: '{result}'")
                return result
            else:
                print(f"[DEBUG] No dialog lines found, returning empty string")
                
        except Exception as e:
            print(f"Warning: Failed to extract dialog context for asset {asset.get('name', '')}: {e}")
            
        return ""
        
    def _is_asset_line(self, line: str) -> bool:
        """Check if a line contains an asset reference (scene, show, etc.).
        
        Args:
            line: Line to check
            
        Returns:
            True if line contains an asset reference
        """
        line_lower = line.lower().strip()
        
        # Major asset keywords that should stop dialog extraction
        major_asset_keywords = ['scene ', 'show ', 'image ']
        if any(line_lower.startswith(keyword) for keyword in major_asset_keywords):
            return True
            
        # Audio/music commands - but only if they're not simple background operations
        if line_lower.startswith('play ') or line_lower.startswith('stop '):
            # Don't stop for simple sound effects, only for major audio changes
            if 'sound' in line_lower:
                return False  # Sound effects shouldn't stop dialog extraction
            return True
            
        # Don't treat window show/hide as asset lines - they're just UI directives
        if line_lower.startswith('window '):
            return False
            
        return False
        
    def _is_control_flow_line(self, line: str) -> bool:
        """Check if a line contains control flow (jump, call, return, etc.).
        
        Args:
            line: Line to check
            
        Returns:
            True if line contains control flow
        """
        line_lower = line.lower().strip()
        
        # Major control flow that should stop dialog extraction
        major_control_keywords = ['jump ', 'call ', 'return', 'label ']
        if any(line_lower.startswith(keyword) for keyword in major_control_keywords):
            return True
            
        # Python control flow (but not simple assignments/pauses)
        python_control_keywords = ['if ', 'else:', 'elif ', 'while ', 'for ']
        if any(line_lower.startswith(keyword) for keyword in python_control_keywords):
            return True
            
        # Don't treat Ren'Py $ statements as control flow unless they're complex
        # Simple pauses, assignments, and function calls shouldn't stop dialog extraction
        if line_lower.startswith('$'):
            # Allow simple statements like: $ renpy.pause(), $ variable = value
            simple_python_patterns = [
                'renpy.pause',
                'renpy.transition',
                'renpy.with_statement',
                'renpy.sound',
                'renpy.music'
            ]
            if any(pattern in line_lower for pattern in simple_python_patterns):
                return False
            # Also allow simple variable assignments (single = not ==)
            if '=' in line_lower and '==' not in line_lower and '<=' not in line_lower and '>=' not in line_lower:
                return False
        
        return False
        
    def _is_dialog_line(self, line: str) -> bool:
        """Check if a line is a dialog line.
        
        Args:
            line: Line to check
            
        Returns:
            True if line appears to be dialog
        """
        # Dialog lines typically start with a character name followed by a quote
        # or just a quote for narrator dialog
        if '"' in line:
            # Character dialog: character_name "dialog text"
            # Narrator dialog: "dialog text"
            return True
            
        # Check for common Ren'Py dialog patterns
        if line.startswith('"') and line.endswith('"'):
            return True
            
        # Check for character name followed by dialog
        parts = line.split('"', 1)
        if len(parts) >= 2:
            character_part = parts[0].strip()
            # Character names are typically single words or short phrases
            if character_part and len(character_part.split()) <= 2:
                return True
                
        return False


class MediaCopierDialog:
    """Progress dialog for media copying operations."""
    
    def __init__(self, parent=None):
        """Initialize the progress dialog.
        
        Args:
            parent: Parent widget
        """
        self.parent = parent
        self.progress_dialog: Optional[QProgressDialog] = None
        self.worker: Optional[MediaCopyWorker] = None
        
    def copy_media_files(self, media_assets: List[Dict[str, Any]], 
                        skip_duplicates: bool = True,
                        image_stack_folder: str = "image-stack",
                        completion_callback: Optional[Callable[[int, int], None]] = None) -> bool:
        """Copy media files with progress dialog.
        
        Args:
            media_assets: List of media asset dictionaries
            skip_duplicates: Whether to skip duplicate files
            image_stack_folder: Target folder for copying
            completion_callback: Callback function called on completion with (copied, skipped) counts
            
        Returns:
            True if copy completed successfully, False if cancelled or failed
        """
        if not media_assets:
            QMessageBox.information(self.parent, "No Media", "No media files to copy")
            return False
            
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Preparing media files...", 
            "Cancel", 
            0, 100, 
            self.parent
        )
        self.progress_dialog.setWindowTitle("Copying Media to Stack")
        self.progress_dialog.setModal(True)
        self.progress_dialog.setMinimumDuration(0)  # Show immediately
        
        # Create and configure worker
        self.worker = MediaCopyWorker(media_assets, skip_duplicates, image_stack_folder)
        self.worker.progress_updated.connect(self.progress_dialog.setValue)
        self.worker.status_updated.connect(self.progress_dialog.setLabelText)
        self.worker.copy_completed.connect(self._on_copy_completed)
        self.worker.copy_failed.connect(self._on_copy_failed)
        
        # Connect cancel button
        self.progress_dialog.canceled.connect(self.worker.cancel)
        
        # Store completion callback
        self.completion_callback = completion_callback
        
        # Start worker
        self.worker.start()
        
        # Show dialog and wait for completion
        result = self.progress_dialog.exec()
        
        # Wait for worker to finish
        if self.worker.isRunning():
            self.worker.wait(3000)  # Wait up to 3 seconds
            
        # Clean up
        success = hasattr(self, '_copy_success') and self._copy_success
        self._cleanup()
        
        return success
        
    def _on_copy_completed(self, copied_count: int, skipped_count: int):
        """Handle copy completion.
        
        Args:
            copied_count: Number of files copied
            skipped_count: Number of files skipped
        """
        self._copy_success = True
        
        if self.progress_dialog:
            self.progress_dialog.accept()
            
        # Show completion message
        message = f"Copy completed!\n\n📁 Files copied: {copied_count}"
        if skipped_count > 0:
            message += f"\n⏭️ Files skipped: {skipped_count}"
            
        QMessageBox.information(self.parent, "Copy Complete", message)
        
        # Call completion callback
        if self.completion_callback:
            self.completion_callback(copied_count, skipped_count)
            
    def _on_copy_failed(self, error_message: str):
        """Handle copy failure.
        
        Args:
            error_message: Error description
        """
        self._copy_success = False
        
        if self.progress_dialog:
            self.progress_dialog.reject()
            
        QMessageBox.critical(self.parent, "Copy Failed", f"Failed to copy media files:\n\n{error_message}")
        
    def _cleanup(self):
        """Clean up resources."""
        if self.worker:
            if self.worker.isRunning():
                self.worker.cancel()
                self.worker.wait(1000)
            self.worker = None
            
        if self.progress_dialog:
            self.progress_dialog = None
            
        self.completion_callback = None


def copy_media_to_image_stack(media_assets: List[Dict[str, Any]], 
                             skip_duplicates: bool = True,
                             image_stack_folder: str = "image-stack",
                             parent=None,
                             completion_callback: Optional[Callable[[int, int], None]] = None) -> bool:
    """Convenience function to copy media files to image stack.
    
    Args:
        media_assets: List of media asset dictionaries with 'path', 'type', 'name'
        skip_duplicates: Whether to skip files that already exist (filename-based)
        image_stack_folder: Target folder path
        parent: Parent widget for dialogs
        completion_callback: Callback function called on completion with (copied, skipped) counts
        
    Returns:
        True if copy completed successfully, False if cancelled or failed
    """
    copier = MediaCopierDialog(parent)
    return copier.copy_media_files(
        media_assets, 
        skip_duplicates, 
        image_stack_folder, 
        completion_callback
    ) 