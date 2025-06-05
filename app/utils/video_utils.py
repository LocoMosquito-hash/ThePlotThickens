#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video utility functions for The Plot Thickens application.

This module provides video processing functionality including:
- Video file validation
- Thumbnail generation from video files
- Video metadata extraction
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt

# Configure logging
logger = logging.getLogger(__name__)

# Supported video formats
SUPPORTED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.ogg', '.ogv'}

class VideoProcessor:
    """Utility class for video processing operations."""
    
    def __init__(self):
        """Initialize the video processor."""
        self.ffmpeg_path = self._find_ffmpeg()
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH.
        
        Returns:
            Path to FFmpeg executable or None if not found
        """
        try:
            # Try to run ffmpeg to check if it's available
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                return 'ffmpeg'  # Available in PATH
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Try common installation paths on Windows
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("FFmpeg not found in system PATH or common installation directories")
        return None
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if a file is a supported video format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a supported video format
        """
        return Path(file_path).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
    
    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get video metadata using FFprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video metadata or None if error
        """
        if not self.ffmpeg_path or not os.path.exists(video_path):
            return None
        
        try:
            # Use ffprobe to get video information
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None
            
            import json
            info = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return None
            
            return {
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'duration': float(info.get('format', {}).get('duration', 0)),
                'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                'codec': video_stream.get('codec_name', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
            return None
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from string format like '30/1'.
        
        Args:
            fps_string: FPS string from FFmpeg
            
        Returns:
            FPS as float
        """
        try:
            if '/' in fps_string:
                numerator, denominator = fps_string.split('/')
                return float(numerator) / float(denominator)
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def generate_gif_thumbnail(self, video_path: str, output_path: str, 
                             max_dimension: int = 320, duration: float = 4.0) -> bool:
        """Generate an animated GIF thumbnail from a video.
        
        Args:
            video_path: Path to the source video
            output_path: Path where GIF thumbnail should be saved
            max_dimension: Maximum width or height for the thumbnail
            duration: Duration of the GIF in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.ffmpeg_path or not os.path.exists(video_path):
            logger.error(f"FFmpeg not available or video file not found: {video_path}")
            return False
        
        try:
            # Get video info to calculate proper scaling
            video_info = self.get_video_info(video_path)
            if not video_info:
                logger.error(f"Could not get video info for {video_path}")
                return False
            
            # Calculate scaling to maintain aspect ratio
            width, height = video_info['width'], video_info['height']
            if width > height:
                # Landscape
                new_width = min(width, max_dimension)
                new_height = int((height * new_width) / width)
            else:
                # Portrait or square
                new_height = min(height, max_dimension)
                new_width = int((width * new_height) / height)
            
            # Ensure even dimensions (required by some codecs)
            new_width = new_width if new_width % 2 == 0 else new_width - 1
            new_height = new_height if new_height % 2 == 0 else new_height - 1
            
            # Create temporary palette file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as palette_file:
                palette_path = palette_file.name
            
            try:
                # Step 1: Generate palette for better GIF quality
                palette_cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-t', str(duration),
                    '-vf', f'fps=15,scale={new_width}:{new_height}:flags=lanczos,palettegen',
                    '-y',  # Overwrite output file
                    palette_path
                ]
                
                result = subprocess.run(palette_cmd, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    logger.error(f"Palette generation failed: {result.stderr}")
                    return False
                
                # Step 2: Generate GIF using the palette
                gif_cmd = [
                    self.ffmpeg_path,
                    '-i', video_path,
                    '-i', palette_path,
                    '-t', str(duration),
                    '-filter_complex', 
                    f'[0:v]fps=15,scale={new_width}:{new_height}:flags=lanczos[v];[v][1:v]paletteuse',
                    '-y',  # Overwrite output file
                    output_path
                ]
                
                result = subprocess.run(gif_cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"Successfully generated GIF thumbnail: {output_path}")
                    return True
                else:
                    logger.error(f"GIF generation failed: {result.stderr}")
                    return False
                    
            finally:
                # Clean up palette file
                if os.path.exists(palette_path):
                    os.unlink(palette_path)
                    
        except Exception as e:
            logger.error(f"Error generating GIF thumbnail: {e}")
            return False
    
    def generate_static_thumbnail(self, video_path: str, output_path: str, 
                                max_dimension: int = 320, time_offset: float = 1.0) -> bool:
        """Generate a static image thumbnail from a video frame.
        
        Args:
            video_path: Path to the source video
            output_path: Path where thumbnail should be saved
            max_dimension: Maximum width or height for the thumbnail
            time_offset: Time in seconds to extract the frame from
            
        Returns:
            True if successful, False otherwise
        """
        if not self.ffmpeg_path or not os.path.exists(video_path):
            logger.error(f"FFmpeg not available or video file not found: {video_path}")
            return False
        
        try:
            # Get video info
            video_info = self.get_video_info(video_path)
            if not video_info:
                logger.error(f"Could not get video info for {video_path}")
                return False
            
            # Ensure time_offset is within video duration
            duration = video_info['duration']
            if time_offset >= duration:
                time_offset = duration / 2  # Use middle frame
            
            # Calculate scaling
            width, height = video_info['width'], video_info['height']
            if width > height:
                new_width = min(width, max_dimension)
                new_height = int((height * new_width) / width)
            else:
                new_height = min(height, max_dimension)
                new_width = int((width * new_height) / height)
            
            # Extract frame
            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-ss', str(time_offset),
                '-vframes', '1',
                '-vf', f'scale={new_width}:{new_height}',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info(f"Successfully generated static thumbnail: {output_path}")
                return True
            else:
                logger.error(f"Static thumbnail generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating static thumbnail: {e}")
            return False

# Global instance
video_processor = VideoProcessor()

def is_video_file(file_path: str) -> bool:
    """Check if a file is a supported video format.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is a supported video format
    """
    return video_processor.is_video_file(file_path)

def generate_video_thumbnail(video_path: str, output_path: str, 
                           max_dimension: int = 320, use_gif: bool = True) -> bool:
    """Generate a thumbnail from a video file.
    
    Args:
        video_path: Path to the source video
        output_path: Path where thumbnail should be saved
        max_dimension: Maximum width or height for the thumbnail
        use_gif: If True, generate animated GIF; if False, generate static PNG
        
    Returns:
        True if successful, False otherwise
    """
    if use_gif:
        return video_processor.generate_gif_thumbnail(video_path, output_path, max_dimension)
    else:
        return video_processor.generate_static_thumbnail(video_path, output_path, max_dimension)

def get_video_info(video_path: str) -> Optional[Dict[str, Any]]:
    """Get video metadata.
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with video metadata or None if error
    """
    return video_processor.get_video_info(video_path)