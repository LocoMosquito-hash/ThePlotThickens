#!/usr/bin/env python3
"""
Video Conversion Lab - PyQt6 Application
Experiment with video format conversions and quality settings.
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QComboBox, QFileDialog, 
    QMessageBox, QProgressBar, QGroupBox, QTextEdit, QSplitter,
    QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QUrl, QSettings, QSize
)
from PyQt6.QtGui import QFont, QPixmap, QDragEnterEvent, QDropEvent, QClipboard
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class VideoInfo:
    """Container for video file information"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = Path(file_path).name
        self.file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
        self.duration = 0.0
        self.width = 0
        self.height = 0
        self.fps = 0.0


class ConversionWorker(QThread):
    """Worker thread for video conversion"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str, float)  # format, output_path, file_size_mb
    error = pyqtSignal(str, str)  # format, error_message
    all_complete = pyqtSignal()  # Signal when all conversions are done
    
    def __init__(self, input_path: str, output_dir: str, quality_level: str):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.quality_level = quality_level
        self.formats_to_convert = ['gif', 'webp', 'mp4_h264', 'mp4_h265']
        
    def run(self):
        """Run conversion for all formats"""
        total_formats = len(self.formats_to_convert)
        
        for i, format_name in enumerate(self.formats_to_convert):
            try:
                output_path = self._convert_format(format_name)
                if output_path and os.path.exists(output_path):
                    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    self.finished.emit(format_name, output_path, file_size_mb)
                else:
                    self.error.emit(format_name, "Conversion failed - no output file")
            except Exception as e:
                self.error.emit(format_name, str(e))
            
            # Update progress
            progress_percent = int(((i + 1) / total_formats) * 100)
            self.progress.emit(progress_percent)
        
        # Signal that all conversions are complete
        self.all_complete.emit()
    
    def _convert_format(self, format_name: str) -> Optional[str]:
        """Convert to specific format using FFmpeg"""
        input_name = Path(self.input_path).stem
        
        # Define quality settings
        quality_settings = self._get_quality_settings(format_name, self.quality_level)
        
        if format_name == 'gif':
            output_path = os.path.join(self.output_dir, f"{input_name}_{self.quality_level}.gif")
            # Fixed GIF conversion with proper palette generation and scale syntax
            cmd = [
                'ffmpeg', '-i', self.input_path, '-y',
                '-vf', f"fps={quality_settings['fps']},scale={quality_settings['scale']}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                output_path
            ]
        elif format_name == 'webp':
            output_path = os.path.join(self.output_dir, f"{input_name}_{self.quality_level}.webp")
            # Fixed WEBP conversion for animated WEBP
            cmd = [
                'ffmpeg', '-i', self.input_path, '-y',
                '-vcodec', 'libwebp',
                '-vf', f"fps={quality_settings['fps']}",
                '-loop', '0',
                '-quality', str(quality_settings['quality']),
                '-preset', quality_settings['preset'],
                '-an',  # Remove audio
                output_path
            ]
        elif format_name == 'mp4_h264':
            output_path = os.path.join(self.output_dir, f"{input_name}_{self.quality_level}_h264.mp4")
            cmd = [
                'ffmpeg', '-i', self.input_path, '-y',
                '-c:v', 'libx264',
                '-crf', str(quality_settings['crf']),
                '-preset', quality_settings['preset'],
                '-c:a', 'aac',
                '-b:a', '128k',
                output_path
            ]
        elif format_name == 'mp4_h265':
            output_path = os.path.join(self.output_dir, f"{input_name}_{self.quality_level}_h265.mp4")
            cmd = [
                'ffmpeg', '-i', self.input_path, '-y',
                '-c:v', 'libx265',
                '-crf', str(quality_settings['crf']),
                '-preset', quality_settings['preset'],
                '-c:a', 'aac',
                '-b:a', '128k',
                output_path
            ]
        else:
            return None
        
        # Run FFmpeg command
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                return output_path
            else:
                raise Exception(f"FFmpeg error: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("Conversion timed out")
        except FileNotFoundError:
            raise Exception("FFmpeg not found. Please install FFmpeg and add it to PATH.")
    
    def _get_quality_settings(self, format_name: str, quality_level: str) -> Dict:
        """Get quality settings for each format and quality level"""
        settings = {
            'gif': {
                'medium': {'fps': 10, 'scale': '480'},
                'high': {'fps': 15, 'scale': '720'},
                'lossless': {'fps': 24, 'scale': '1080'}
            },
            'webp': {
                'medium': {'fps': 15, 'quality': 75, 'preset': 'default'},
                'high': {'fps': 20, 'quality': 90, 'preset': 'photo'},
                'lossless': {'fps': 24, 'quality': 100, 'preset': 'lossless'}
            },
            'mp4_h264': {
                'medium': {'crf': 28, 'preset': 'medium'},
                'high': {'crf': 20, 'preset': 'slow'},
                'lossless': {'crf': 0, 'preset': 'veryslow'}
            },
            'mp4_h265': {
                'medium': {'crf': 32, 'preset': 'medium'},
                'high': {'crf': 24, 'preset': 'slow'},
                'lossless': {'crf': 0, 'preset': 'veryslow'}
            }
        }
        
        return settings.get(format_name, {}).get(quality_level, {})


class VideoPreviewWidget(QWidget):
    """Widget for displaying video preview with info"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.video_path = None
        self.file_size_mb = 0.0
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title label
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(self.title_label)
        
        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(200, 150)
        self.video_widget.setStyleSheet("border: 1px solid gray;")
        layout.addWidget(self.video_widget)
        
        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        self.audio_output.setVolume(0)  # Mute by default
        
        # Info label
        self.info_label = QLabel("No video loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Auto-loop timer
        self.loop_timer = QTimer()
        self.loop_timer.timeout.connect(self.restart_video)
        self.media_player.durationChanged.connect(self.setup_loop)
        
    def load_video(self, video_path: str, file_size_mb: float):
        """Load video file and display info"""
        self.video_path = video_path
        self.file_size_mb = file_size_mb
        
        if os.path.exists(video_path):
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            
            # Update info
            self.info_label.setText(f"Size: {file_size_mb:.2f} MB")
        else:
            self.info_label.setText("File not found")
    
    def setup_loop(self, duration):
        """Setup auto-loop for video"""
        if duration > 0:
            self.loop_timer.start(duration + 100)  # Small delay to ensure restart
    
    def restart_video(self):
        """Restart video for looping"""
        if self.video_path:
            self.media_player.setPosition(0)
            self.media_player.play()
    
    def clear_video(self):
        """Clear the video and reset display"""
        self.media_player.stop()
        self.loop_timer.stop()
        self.video_path = None
        self.file_size_mb = 0.0
        self.info_label.setText("No video loaded")


class VideoConversionLab(QMainWindow):
    """Main application window for video conversion testing"""
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("VideoConversionLab", "Settings")
        self.current_video_info: Optional[VideoInfo] = None
        self.conversion_worker: Optional[ConversionWorker] = None
        self.temp_dir = tempfile.mkdtemp(prefix="video_conversion_")
        self.preview_widgets: Dict[str, VideoPreviewWidget] = {}
        
        self.setup_ui()
        self.setup_drag_drop()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Video Conversion Lab")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Input section
        input_group = QGroupBox("Input Video")
        input_layout = QHBoxLayout(input_group)
        
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("padding: 5px; border: 1px solid gray;")
        input_layout.addWidget(self.file_path_label)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        input_layout.addWidget(self.browse_button)
        
        self.paste_button = QPushButton("Paste Path")
        self.paste_button.clicked.connect(self.paste_file_path)
        input_layout.addWidget(self.paste_button)
        
        main_layout.addWidget(input_group)
        
        # Quality selection
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QHBoxLayout(quality_group)
        
        quality_layout.addWidget(QLabel("Quality Level:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["medium", "high", "lossless"])
        self.quality_combo.setCurrentText("high")
        self.quality_combo.currentTextChanged.connect(self.quality_changed)
        quality_layout.addWidget(self.quality_combo)
        
        quality_layout.addStretch()
        
        self.convert_button = QPushButton("Convert All Formats")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        quality_layout.addWidget(self.convert_button)
        
        main_layout.addWidget(quality_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Preview grid
        preview_group = QGroupBox("Video Previews")
        preview_layout = QVBoxLayout(preview_group)
        
        # Create scroll area for previews
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.grid_layout = QGridLayout(scroll_widget)
        
        # Create preview widgets
        formats = [
            ("Original", "original"),
            ("GIF", "gif"),
            ("WEBP", "webp"),
            ("MP4 (H.264)", "mp4_h264"),
            ("MP4 (H.265)", "mp4_h265")
        ]
        
        for i, (title, format_key) in enumerate(formats):
            row = i // 3
            col = i % 3
            
            preview_widget = VideoPreviewWidget(title)
            self.preview_widgets[format_key] = preview_widget
            self.grid_layout.addWidget(preview_widget, row, col)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        preview_layout.addWidget(scroll_area)
        
        main_layout.addWidget(preview_group)
        
        # Settings info
        self.settings_info = QTextEdit()
        self.settings_info.setMaximumHeight(100)
        self.settings_info.setPlainText("Quality settings will be displayed here...")
        main_layout.addWidget(self.settings_info)
        
        # Update quality info
        self.update_quality_info()
    
    def setup_drag_drop(self):
        """Enable drag and drop for video files"""
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if self.is_video_file(file_path):
                    event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.load_video_file(file_path)
    
    def is_video_file(self, file_path: str) -> bool:
        """Check if file is a video file"""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        return Path(file_path).suffix.lower() in video_extensions
    
    def browse_file(self):
        """Open file browser to select video file"""
        last_dir = self.settings.value("last_directory", str(Path.home()))
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Video File",
            last_dir,
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm);;All Files (*)"
        )
        
        if file_path:
            self.load_video_file(file_path)
            self.settings.setValue("last_directory", str(Path(file_path).parent))
    
    def paste_file_path(self):
        """Paste file path from clipboard"""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        
        if text and os.path.isfile(text) and self.is_video_file(text):
            self.load_video_file(text)
        else:
            QMessageBox.warning(self, "Invalid Path", "Clipboard does not contain a valid video file path.")
    
    def load_video_file(self, file_path: str):
        """Load video file and update UI"""
        try:
            self.current_video_info = VideoInfo(file_path)
            self.file_path_label.setText(f"{self.current_video_info.file_name} ({self.current_video_info.file_size_mb:.2f} MB)")
            self.convert_button.setEnabled(True)
            
            # Load original video in preview
            self.preview_widgets["original"].load_video(file_path, self.current_video_info.file_size_mb)
            
            # Clear other previews
            for key in ["gif", "webp", "mp4_h264", "mp4_h265"]:
                self.preview_widgets[key].clear_video()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load video file: {str(e)}")
    
    def quality_changed(self):
        """Handle quality level change"""
        self.update_quality_info()
    
    def update_quality_info(self):
        """Update quality settings information"""
        quality_level = self.quality_combo.currentText()
        
        info_text = f"Quality Level: {quality_level.upper()}\n\n"
        
        # Add format-specific settings
        worker = ConversionWorker("", "", quality_level)
        
        formats_info = {
            "GIF": worker._get_quality_settings("gif", quality_level),
            "WEBP": worker._get_quality_settings("webp", quality_level),
            "MP4 H.264": worker._get_quality_settings("mp4_h264", quality_level),
            "MP4 H.265": worker._get_quality_settings("mp4_h265", quality_level)
        }
        
        for format_name, settings in formats_info.items():
            info_text += f"{format_name}: {json.dumps(settings, indent=2)}\n"
        
        self.settings_info.setPlainText(info_text)
    
    def start_conversion(self):
        """Start video conversion process"""
        if not self.current_video_info:
            return
        
        # Disable UI during conversion
        self.convert_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clear previous results
        for key in ["gif", "webp", "mp4_h264", "mp4_h265"]:
            self.preview_widgets[key].clear_video()
        
        # Start conversion worker
        quality_level = self.quality_combo.currentText()
        self.conversion_worker = ConversionWorker(
            self.current_video_info.file_path,
            self.temp_dir,
            quality_level
        )
        
        self.conversion_worker.progress.connect(self.progress_bar.setValue)
        self.conversion_worker.finished.connect(self.conversion_finished)
        self.conversion_worker.error.connect(self.conversion_error)
        self.conversion_worker.all_complete.connect(self.conversion_complete)
        self.conversion_worker.start()
    
    def conversion_finished(self, format_name: str, output_path: str, file_size_mb: float):
        """Handle successful conversion"""
        if format_name in self.preview_widgets:
            self.preview_widgets[format_name].load_video(output_path, file_size_mb)
    
    def conversion_error(self, format_name: str, error_message: str):
        """Handle conversion error"""
        print(f"Conversion error for {format_name}: {error_message}")
        if format_name in self.preview_widgets:
            self.preview_widgets[format_name].info_label.setText(f"Error: {error_message}")
    
    def conversion_complete(self):
        """Handle completion of all conversions"""
        self.progress_bar.setVisible(False)
        self.convert_button.setEnabled(True)
    
    def load_settings(self):
        """Load application settings"""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
    
    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("geometry", self.saveGeometry())
    
    def closeEvent(self, event):
        """Handle application close"""
        self.save_settings()
        
        # Stop any running conversions
        if self.conversion_worker and self.conversion_worker.isRunning():
            self.conversion_worker.terminate()
            self.conversion_worker.wait()
        
        # Clean up temp directory
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
        
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Video Conversion Lab")
    app.setApplicationVersion("1.0")
    
    # Check for FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        QMessageBox.critical(
            None,
            "FFmpeg Required",
            "FFmpeg is required for video conversion but was not found.\n"
            "Please install FFmpeg and add it to your system PATH."
        )
        sys.exit(1)
    
    window = VideoConversionLab()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()