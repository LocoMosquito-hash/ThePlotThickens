from typing import List, Dict, Any, Optional, Callable
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QGridLayout, QMessageBox, QDialog,
    QCheckBox, QGroupBox, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QSize

from app.utils.face_recognition_util import FaceRecognitionUtil


class FaceDetectionFrame(QFrame):
    """Frame for displaying a detected face with character suggestion."""
    
    face_confirmed = pyqtSignal(int, int, bool)  # character_id, face_id, accepted
    
    def __init__(self, face_id: int, location: tuple, character_info: Dict[str, Any], 
                 confidence: float, image_path: str, parent=None):
        """Initialize the face detection frame.
        
        Args:
            face_id: Unique ID for this face
            location: Face location as (top, right, bottom, left)
            character_info: Character info dictionary
            confidence: Confidence score (0-1)
            image_path: Path to the image
            parent: Parent widget
        """
        super().__init__(parent)
        self.face_id = face_id
        self.location = location
        self.character_id = character_info.get('id')
        self.confidence = confidence
        self.image_path = image_path
        
        # Set up frame appearance
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Face thumbnail
        self.face_thumbnail = QLabel()
        self.face_thumbnail.setFixedSize(100, 100)
        self.face_thumbnail.setScaledContents(True)
        self.face_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Extract and display face thumbnail
        self._extract_face_thumbnail()
        
        # Character info
        character_name = character_info.get('name', 'Unknown')
        self.character_label = QLabel(f"{character_name}")
        self.character_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.character_label.setWordWrap(True)
        
        # Confidence info
        confidence_percent = int(confidence * 100)
        self.confidence_label = QLabel(f"Match: {confidence_percent}%")
        self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.confirm_button = QPushButton("✓")
        self.confirm_button.setToolTip("Confirm this character match")
        self.confirm_button.clicked.connect(self._on_confirm)
        
        self.reject_button = QPushButton("✗")
        self.reject_button.setToolTip("Reject this character match")
        self.reject_button.clicked.connect(self._on_reject)
        
        buttons_layout.addWidget(self.confirm_button)
        buttons_layout.addWidget(self.reject_button)
        
        # Add widgets to layout
        layout.addWidget(self.face_thumbnail)
        layout.addWidget(self.character_label)
        layout.addWidget(self.confidence_label)
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def _extract_face_thumbnail(self):
        """Extract face thumbnail from the image."""
        try:
            # Load image
            image = QImage(self.image_path)
            if image.isNull():
                self.face_thumbnail.setText("Error loading image")
                return
            
            # Extract face region
            top, right, bottom, left = self.location
            face_rect = QRect(left, top, right - left, bottom - top)
            
            # Extract face image
            face_image = image.copy(face_rect)
            
            # Display face image
            self.face_thumbnail.setPixmap(QPixmap.fromImage(face_image))
        except Exception as e:
            print(f"Error extracting face thumbnail: {e}")
            self.face_thumbnail.setText("Error")
    
    def _on_confirm(self):
        """Handle confirmation of the face match."""
        self.face_confirmed.emit(self.character_id, self.face_id, True)
    
    def _on_reject(self):
        """Handle rejection of the face match."""
        self.face_confirmed.emit(self.character_id, self.face_id, False)


class FaceRecognitionWidget(QWidget):
    """Widget for displaying face recognition results and suggestions."""
    
    recognition_complete = pyqtSignal(list)  # List of confirmed face matches
    
    def __init__(self, db_conn, image_path: str, recognition_results: List[Dict[str, Any]], 
                 characters: List[Dict[str, Any]], parent=None):
        """Initialize the face recognition widget.
        
        Args:
            db_conn: Database connection
            image_path: Path to the image
            recognition_results: Face recognition results
            characters: List of characters in the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.image_path = image_path
        self.recognition_results = recognition_results
        self.characters = {char['id']: char for char in characters}
        self.detected_faces = []  # List of FaceDetectionFrame widgets
        self.confirmed_faces = []  # List of confirmed character IDs for each face
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Heading label
        heading_label = QLabel("Face Recognition Results")
        heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(heading_label)
        
        # No faces found?
        if not self.recognition_results:
            no_faces_label = QLabel("No faces were detected in this image.")
            no_faces_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(no_faces_label)
            return
        
        # Create a scroll area for faces
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        
        # Add face detection frames to grid
        for i, result in enumerate(self.recognition_results):
            character_id = result['character_id']
            location = result['location']
            confidence = result['confidence']
            
            character_info = self.characters.get(character_id, {'id': None, 'name': 'Unknown'})
            
            face_frame = FaceDetectionFrame(
                face_id=i,
                location=location,
                character_info=character_info,
                confidence=confidence,
                image_path=self.image_path,
                parent=self
            )
            face_frame.face_confirmed.connect(self._on_face_confirmed)
            
            # Add to grid: 3 columns
            row = i // 3
            col = i % 3
            scroll_layout.addWidget(face_frame, row, col)
            self.detected_faces.append(face_frame)
        
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # OK button at the bottom
        ok_button = QPushButton("Finish")
        ok_button.clicked.connect(self._on_finish)
        main_layout.addWidget(ok_button)
        
        self.setLayout(main_layout)
    
    def _on_face_confirmed(self, character_id: int, face_id: int, accepted: bool):
        """Handle face confirmation or rejection."""
        # Ensure face_id is within range
        if 0 <= face_id < len(self.recognition_results):
            result = self.recognition_results[face_id]
            
            if accepted:
                self.confirmed_faces.append({
                    'character_id': character_id,
                    'location': result['location'],
                    'confidence': result['confidence']
                })
                
                # Disable the frame to indicate it's been processed
                self.detected_faces[face_id].setEnabled(False)
                self.detected_faces[face_id].setStyleSheet("background-color: rgba(0, 255, 0, 0.1);")
            else:
                # Just disable the frame
                self.detected_faces[face_id].setEnabled(False)
                self.detected_faces[face_id].setStyleSheet("background-color: rgba(255, 0, 0, 0.1);")
    
    def _on_finish(self):
        """Finish the face recognition process."""
        self.recognition_complete.emit(self.confirmed_faces)
        self.close()


class FaceRecognitionDialog(QDialog):
    """Dialog for face recognition results and suggestions."""
    
    def __init__(self, db_conn, image_path: str, image_id: int, story_id: int, parent=None):
        """Initialize the face recognition dialog.
        
        Args:
            db_conn: Database connection
            image_path: Path to the image
            image_id: ID of the image
            story_id: ID of the story
            parent: Parent widget
        """
        super().__init__(parent)
        self.db_conn = db_conn
        self.image_path = image_path
        self.image_id = image_id
        self.story_id = story_id
        self.confirmed_faces = []
        
        # Set window properties
        self.setWindowTitle("Face Recognition")
        self.setMinimumSize(600, 400)
        
        # Run face recognition
        self._run_face_recognition()
        
        # Initialize UI
        self.init_ui()
    
    def _run_face_recognition(self):
        """Run face recognition on the image."""
        try:
            # Initialize face recognition
            face_util = FaceRecognitionUtil(self.db_conn)
            
            # Identify faces in the image
            self.recognition_results = face_util.identify_faces(self.image_path)
            
            # Get characters for this story
            from app.db_sqlite import get_story_characters
            self.characters = get_story_characters(self.db_conn, self.story_id)
            
        except Exception as e:
            print(f"Error running face recognition: {e}")
            self.recognition_results = []
            self.characters = []
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Add face recognition widget
        self.face_widget = FaceRecognitionWidget(
            self.db_conn,
            self.image_path,
            self.recognition_results,
            self.characters,
            self
        )
        self.face_widget.recognition_complete.connect(self._on_recognition_complete)
        
        layout.addWidget(self.face_widget)
        
        self.setLayout(layout)
    
    def _on_recognition_complete(self, confirmed_faces):
        """Handle completion of face recognition."""
        self.confirmed_faces = confirmed_faces
        self.accept()
    
    def get_confirmed_faces(self):
        """Get the list of confirmed faces.
        
        Returns:
            List of confirmed faces
        """
        return self.confirmed_faces 