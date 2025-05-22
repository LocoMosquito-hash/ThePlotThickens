import os
from typing import Callable, Dict, List, Optional, Tuple, Any
import logging

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QPushButton, QGroupBox, QComboBox, QCheckBox, 
    QScrollArea, QSizePolicy, QFileDialog, QMessageBox
)

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageEnhancementWidget(QWidget):
    """Widget for enhancing images with various adjustments.
    
    This widget provides sliders and buttons for image enhancement 
    operations such as brightness, contrast, sharpness, etc.
    
    Signals:
        image_changed: Emitted when the image has been modified
        image_saved: Emitted when the image has been saved
    """
    
    # Signal emitted when image changes due to an enhancement
    image_changed = pyqtSignal(QPixmap)
    # Signal emitted when image is saved
    image_saved = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the image enhancement widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Original and current image data
        self.original_image = None  # Original PIL Image
        self.current_image = None   # Current PIL Image
        self.current_cv_image = None  # Current OpenCV image (for operations that use OpenCV)
        
        # Flag to track if image has been modified
        self._image_modified = False
        
        # Enhancement parameters with default values
        self.enhancement_values = {
            'brightness': 100,  # 0-200, 100 is neutral
            'contrast': 100,    # 0-200, 100 is neutral
            'gamma': 100,       # 1-300, 100 is neutral (maps to 0.1-3.0)
            'sharpness': 100,   # 0-200, 100 is neutral
            'saturation': 100,  # 0-200, 100 is neutral
        }
        
        # UI setup
        self.init_ui()
        
        # Set initial state
        self.update_slider_labels()
        self.disable_controls()
    
    def init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout(self)
        
        # Create a scroll area to handle many controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Container widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Create controls for each enhancement type
        
        # Brightness control
        brightness_group = QGroupBox("Brightness")
        brightness_layout = QVBoxLayout(brightness_group)
        
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 200)
        self.brightness_slider.setValue(100)
        self.brightness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.brightness_slider.setTickInterval(25)
        self.brightness_slider.valueChanged.connect(
            lambda v: self.on_slider_changed('brightness', v))
        
        self.brightness_label = QLabel("Brightness: 100%")
        
        brightness_layout.addWidget(self.brightness_label)
        brightness_layout.addWidget(self.brightness_slider)
        
        # Contrast control
        contrast_group = QGroupBox("Contrast")
        contrast_layout = QVBoxLayout(contrast_group)
        
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(0, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.contrast_slider.setTickInterval(25)
        self.contrast_slider.valueChanged.connect(
            lambda v: self.on_slider_changed('contrast', v))
        
        self.contrast_label = QLabel("Contrast: 100%")
        
        contrast_layout.addWidget(self.contrast_label)
        contrast_layout.addWidget(self.contrast_slider)
        
        # Gamma correction
        gamma_group = QGroupBox("Gamma Correction")
        gamma_layout = QVBoxLayout(gamma_group)
        
        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(10, 300)  # 0.1 to 3.0
        self.gamma_slider.setValue(100)  # 1.0
        self.gamma_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.gamma_slider.setTickInterval(50)
        self.gamma_slider.valueChanged.connect(
            lambda v: self.on_slider_changed('gamma', v))
        
        self.gamma_label = QLabel("Gamma: 1.0")
        
        gamma_layout.addWidget(self.gamma_label)
        gamma_layout.addWidget(self.gamma_slider)
        
        # Sharpness control
        sharpness_group = QGroupBox("Sharpness")
        sharpness_layout = QVBoxLayout(sharpness_group)
        
        self.sharpness_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharpness_slider.setRange(0, 200)
        self.sharpness_slider.setValue(100)
        self.sharpness_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sharpness_slider.setTickInterval(25)
        self.sharpness_slider.valueChanged.connect(
            lambda v: self.on_slider_changed('sharpness', v))
        
        self.sharpness_label = QLabel("Sharpness: 100%")
        
        sharpness_layout.addWidget(self.sharpness_label)
        sharpness_layout.addWidget(self.sharpness_slider)
        
        # Saturation control
        saturation_group = QGroupBox("Saturation")
        saturation_layout = QVBoxLayout(saturation_group)
        
        self.saturation_slider = QSlider(Qt.Orientation.Horizontal)
        self.saturation_slider.setRange(0, 200)
        self.saturation_slider.setValue(100)
        self.saturation_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.saturation_slider.setTickInterval(25)
        self.saturation_slider.valueChanged.connect(
            lambda v: self.on_slider_changed('saturation', v))
        
        self.saturation_label = QLabel("Saturation: 100%")
        
        saturation_layout.addWidget(self.saturation_label)
        saturation_layout.addWidget(self.saturation_slider)
        
        # Buttons for actions
        buttons_layout = QHBoxLayout()
        
        # Auto-enhance button
        self.auto_enhance_btn = QPushButton("Auto Enhance")
        self.auto_enhance_btn.clicked.connect(self.auto_enhance)
        buttons_layout.addWidget(self.auto_enhance_btn)
        
        # Reset button
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.clicked.connect(self.reset_all)
        buttons_layout.addWidget(self.reset_btn)
        
        # Compare button
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.setCheckable(True)
        self.compare_btn.toggled.connect(self.on_compare_toggled)
        buttons_layout.addWidget(self.compare_btn)
        
        # Create rotate button layout
        rotate_layout = QHBoxLayout()
        
        # Rotate left button
        self.rotate_left_btn = QPushButton("Rotate Left")
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_image(-90))
        rotate_layout.addWidget(self.rotate_left_btn)
        
        # Rotate right button
        self.rotate_right_btn = QPushButton("Rotate Right")
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_image(90))
        rotate_layout.addWidget(self.rotate_right_btn)
        
        # Save buttons layout
        save_layout = QHBoxLayout()
        
        # Save button (renamed from Save a Copy)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_image)
        save_layout.addWidget(self.save_btn)
        
        # Apply as new button
        self.apply_btn = QPushButton("Apply as New Image")
        self.apply_btn.clicked.connect(self.apply_as_new)
        save_layout.addWidget(self.apply_btn)
        
        # Add all components to the scroll layout
        scroll_layout.addWidget(brightness_group)
        scroll_layout.addWidget(contrast_group)
        scroll_layout.addWidget(gamma_group)
        scroll_layout.addWidget(sharpness_group)
        scroll_layout.addWidget(saturation_group)
        scroll_layout.addLayout(buttons_layout)
        scroll_layout.addLayout(rotate_layout)
        scroll_layout.addLayout(save_layout)
        
        # Add stretch to push all controls to the top
        scroll_layout.addStretch(1)
        
        # Set the scroll content
        scroll_area.setWidget(scroll_content)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
    
    def update_slider_labels(self):
        """Update all slider labels with current values."""
        self.brightness_label.setText(f"Brightness: {self.enhancement_values['brightness']}%")
        self.contrast_label.setText(f"Contrast: {self.enhancement_values['contrast']}%")
        
        # For gamma, convert the 10-300 range to 0.1-3.0
        gamma_value = self.enhancement_values['gamma'] / 100
        self.gamma_label.setText(f"Gamma: {gamma_value:.1f}")
        
        self.sharpness_label.setText(f"Sharpness: {self.enhancement_values['sharpness']}%")
        self.saturation_label.setText(f"Saturation: {self.enhancement_values['saturation']}%")
    
    def set_image(self, pixmap: QPixmap):
        """Set the image to enhance.
        
        Args:
            pixmap: QPixmap to enhance
        """
        if pixmap and not pixmap.isNull():
            logger.debug(f"Setting image: size={pixmap.width()}x{pixmap.height()}, isNull={pixmap.isNull()}")
            
            try:
                # Convert QPixmap to QImage
                qimage = pixmap.toImage()
                logger.debug(f"QImage: format={qimage.format()}, hasAlpha={qimage.hasAlphaChannel()}")
                
                # Convert QImage to numpy array
                width = qimage.width()
                height = qimage.height()
                logger.debug(f"Converting QImage {width}x{height} to numpy array")
                
                # Convert QImage to the correct format for processing
                if qimage.format() != QImage.Format.Format_RGBA8888:
                    logger.debug(f"Converting QImage from format {qimage.format()} to Format_RGBA8888")
                    qimage = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
                
                # Get image data as numpy array
                ptr = qimage.bits()
                ptr.setsize(qimage.sizeInBytes())
                arr = np.array(ptr).reshape(height, width, 4)
                
                # Convert from RGBA to RGB if needed
                if arr.shape[2] == 4:  # If we have an alpha channel
                    logger.debug("Converting from RGBA to RGB")
                    rgb_arr = arr[:, :, :3]  # Just take the first 3 channels (RGB)
                else:
                    rgb_arr = arr
                
                # Create PIL Image from numpy array
                pil_image = Image.fromarray(rgb_arr)
                logger.debug(f"Created PIL image: mode={pil_image.mode}, size={pil_image.size}")
                
                # Store the original image
                self.original_image = pil_image
                self.current_image = pil_image.copy()
                
                # Also convert to OpenCV format for operations that use OpenCV
                self.current_cv_image = self.pil_to_cv(self.current_image)
                
                # Reset modification flag
                self._image_modified = False
                
                # Enable controls
                self.enable_controls()
            except Exception as e:
                logger.error(f"Error converting QImage to PIL: {str(e)}")
                # Fallback to temp file method if numpy approach fails
                try:
                    logger.debug("Falling back to temporary file method")
                    # Convert QPixmap to QImage
                    qimage = pixmap.toImage()
                    
                    # Save to temporary file
                    import tempfile
                    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    temp_filename = temp_file.name
                    temp_file.close()
                    
                    logger.debug(f"Saving QImage to temporary file: {temp_filename}")
                    qimage.save(temp_filename, "PNG")
                    
                    # Load with PIL
                    logger.debug("Loading image with PIL from temporary file")
                    pil_image = Image.open(temp_filename)
                    
                    # Remove temporary file
                    try:
                        os.unlink(temp_filename)
                    except Exception as e2:
                        logger.error(f"Could not remove temporary file: {e2}")
                    
                    logger.debug(f"Created PIL image: mode={pil_image.mode}, size={pil_image.size}")
                    
                    # Store the original image
                    self.original_image = pil_image
                    self.current_image = pil_image.copy()
                    
                    # Also convert to OpenCV format for operations that use OpenCV
                    self.current_cv_image = self.pil_to_cv(self.current_image)
                    
                    # Enable controls
                    self.enable_controls()
                except Exception as e2:
                    logger.error(f"Both conversion methods failed: {e2}")
                    self.original_image = None
                    self.current_image = None
                    self.current_cv_image = None
                    self.disable_controls()
        else:
            logger.debug("Null or invalid pixmap provided")
            self.original_image = None
            self.current_image = None
            self.current_cv_image = None
            self.disable_controls()
    
    def enable_controls(self):
        """Enable all enhancement controls."""
        self.brightness_slider.setEnabled(True)
        self.contrast_slider.setEnabled(True)
        self.gamma_slider.setEnabled(True)
        self.sharpness_slider.setEnabled(True)
        self.saturation_slider.setEnabled(True)
        self.auto_enhance_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)
        self.compare_btn.setEnabled(True)
        self.rotate_left_btn.setEnabled(True)
        self.rotate_right_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)
    
    def disable_controls(self):
        """Disable all enhancement controls."""
        self.brightness_slider.setEnabled(False)
        self.contrast_slider.setEnabled(False)
        self.gamma_slider.setEnabled(False)
        self.sharpness_slider.setEnabled(False)
        self.saturation_slider.setEnabled(False)
        self.auto_enhance_btn.setEnabled(False)
        self.reset_btn.setEnabled(False)
        self.compare_btn.setEnabled(False)
        self.rotate_left_btn.setEnabled(False)
        self.rotate_right_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)
    
    def on_slider_changed(self, name: str, value: int):
        """Handle slider value changes.
        
        Args:
            name: Name of the slider
            value: New value
        """
        logger.debug(f"Slider {name} changed to {value}")
        # Check if the value actually changed
        if self.enhancement_values[name] != value:
            self.enhancement_values[name] = value
            self._image_modified = True
            self.update_slider_labels()
            self.apply_enhancements()
        else:
            logger.debug(f"Slider {name} value unchanged, skipping update")
    
    def apply_enhancements(self):
        """Apply all enhancements to the original image."""
        if not self.original_image:
            logger.debug("No original image available for enhancement")
            return
        
        try:
            # Start with a copy of the original image
            logger.debug(f"Starting enhancements on image: mode={self.original_image.mode}, size={self.original_image.size}")
            enhanced_image = self.original_image.copy()
            
            # Apply brightness
            brightness_factor = self.enhancement_values['brightness'] / 100
            logger.debug(f"Applying brightness: factor={brightness_factor}")
            try:
                enhancer = ImageEnhance.Brightness(enhanced_image)
                enhanced_image = enhancer.enhance(brightness_factor)
            except Exception as e:
                logger.error(f"Error applying brightness: {e}")
                # Continue with unenhanced image
                pass
            
            # Apply contrast
            contrast_factor = self.enhancement_values['contrast'] / 100
            logger.debug(f"Applying contrast: factor={contrast_factor}")
            try:
                enhancer = ImageEnhance.Contrast(enhanced_image)
                enhanced_image = enhancer.enhance(contrast_factor)
            except Exception as e:
                logger.error(f"Error applying contrast: {e}")
                # Continue with unenhanced image
                pass
            
            # Apply gamma correction
            gamma_value = self.enhancement_values['gamma'] / 100
            if gamma_value != 1.0:
                logger.debug(f"Applying gamma correction: value={gamma_value}")
                try:
                    # Convert to OpenCV for gamma correction
                    cv_image = self.pil_to_cv(enhanced_image)
                    
                    # Apply gamma correction
                    # Build a lookup table mapping pixel values [0, 255] to their adjusted gamma values
                    inv_gamma = 1.0 / gamma_value
                    table = np.array([
                        ((i / 255.0) ** inv_gamma) * 255 for i in range(256)
                    ]).astype(np.uint8)
                    
                    # Apply the lookup table
                    cv_image = cv2.LUT(cv_image, table)
                    
                    # Convert back to PIL
                    enhanced_image = self.cv_to_pil(cv_image)
                except Exception as e:
                    logger.error(f"Error applying gamma correction: {e}")
                    # Continue with uncorrected image instead of failing
                    pass
            
            # Apply sharpness
            sharpness_factor = self.enhancement_values['sharpness'] / 100
            logger.debug(f"Applying sharpness: factor={sharpness_factor}")
            try:
                enhancer = ImageEnhance.Sharpness(enhanced_image)
                enhanced_image = enhancer.enhance(sharpness_factor)
            except Exception as e:
                logger.error(f"Error applying sharpness: {e}")
                # Continue with unsharpened image
                pass
            
            # Apply saturation
            saturation_factor = self.enhancement_values['saturation'] / 100
            logger.debug(f"Applying saturation: factor={saturation_factor}")
            try:
                enhancer = ImageEnhance.Color(enhanced_image)
                enhanced_image = enhancer.enhance(saturation_factor)
            except Exception as e:
                logger.error(f"Error applying saturation: {e}")
                # Continue with unsaturated image
                pass
            
            # Verify that enhancements made a difference
            try:
                # Convert to arrays for comparison
                import numpy as np
                orig_array = np.array(self.original_image.convert('RGB'))
                enhanced_array = np.array(enhanced_image.convert('RGB'))
                
                # Check if images are different
                is_different = not np.array_equal(orig_array, enhanced_array)
                logger.debug(f"Enhancement made visible changes: {is_different}")
                
                # If no changes were made, add a small modification to ensure we save differently
                if not is_different and any(abs(v - 100) > 1 for v in self.enhancement_values.values()):
                    logger.debug("No visible changes detected but sliders were moved - forcing a small change")
                    # Make a tiny change to a corner pixel
                    if enhanced_image.mode == 'RGB' and enhanced_image.size[0] > 0 and enhanced_image.size[1] > 0:
                        # Get image as array
                        img_array = np.array(enhanced_image)
                        
                        # Modify bottom right pixel slightly
                        h, w = img_array.shape[0]-1, img_array.shape[1]-1
                        pixel = img_array[h, w].copy()
                        
                        # Modify red channel slightly
                        if len(pixel) >= 3:
                            r_value = int(pixel[0])
                            if r_value < 255:
                                pixel[0] = r_value + 1
                            else:
                                pixel[0] = r_value - 1
                            
                            # Update pixel
                            img_array[h, w] = pixel
                            
                            # Create new image
                            enhanced_image = Image.fromarray(img_array)
                            logger.debug("Applied forced pixel modification")
            except Exception as e:
                logger.error(f"Error checking enhancement differences: {e}")
            
            # Store the current enhanced image
            self.current_image = enhanced_image
            
            try:
                self.current_cv_image = self.pil_to_cv(enhanced_image)
            except Exception as e:
                logger.error(f"Error converting to OpenCV: {e}")
                # Continue without storing CV image
                pass
            
            # Convert to QPixmap and emit signal
            logger.debug("Converting enhanced image to QPixmap")
            try:
                pixmap = self.pil_to_pixmap(enhanced_image)
                logger.debug(f"Final QPixmap: size={pixmap.width()}x{pixmap.height()}, isNull={pixmap.isNull()}")
                
                if not pixmap.isNull():
                    # Emit signal to update the preview
                    self.image_changed.emit(pixmap)
                    
                    # Try to update parent dialog directly to ensure refresh
                    parent_dialog = self.window()
                    if hasattr(parent_dialog, 'image_label') and parent_dialog.image_label:
                        try:
                            # This should update the main image view as well
                            parent_dialog.image_label.set_image(pixmap, pixmap.width(), pixmap.height())
                            logger.debug("Updated parent dialog image directly")
                        except Exception as e:
                            logger.error(f"Failed to update parent dialog image: {e}")
                else:
                    logger.error("Generated null pixmap, not emitting signal")
                    # Show error in parent widget
                    if self.parent():
                        QMessageBox.warning(self.parent(), "Enhancement Error", 
                                          "Failed to process image with current settings.")
            except Exception as e:
                logger.error(f"Error in final conversion: {e}")
                # Show error in UI
                if self.parent():
                    QMessageBox.warning(self.parent(), "Enhancement Error", 
                                      f"Failed to process image: {str(e)}")
        except Exception as e:
            logger.error(f"Error in enhancement process: {e}")
            # Show error in UI
            if self.parent():
                QMessageBox.warning(self.parent(), "Enhancement Error", 
                                  f"Image enhancement failed: {str(e)}")
    
    def reset_all(self):
        """Reset all enhancement parameters to default."""
        logger.debug("Resetting all enhancements to default")
        self.enhancement_values = {
            'brightness': 100,
            'contrast': 100,
            'gamma': 100,
            'sharpness': 100,
            'saturation': 100
        }
        
        # Update sliders - block signals to prevent recursive calls
        self.brightness_slider.blockSignals(True)
        self.brightness_slider.setValue(100)
        self.brightness_slider.blockSignals(False)
        
        self.contrast_slider.blockSignals(True)
        self.contrast_slider.setValue(100)
        self.contrast_slider.blockSignals(False)
        
        self.gamma_slider.blockSignals(True)
        self.gamma_slider.setValue(100)
        self.gamma_slider.blockSignals(False)
        
        self.sharpness_slider.blockSignals(True)
        self.sharpness_slider.setValue(100)
        self.sharpness_slider.blockSignals(False)
        
        self.saturation_slider.blockSignals(True)
        self.saturation_slider.setValue(100)
        self.saturation_slider.blockSignals(False)
        
        # Update labels
        self.update_slider_labels()
        
        # Flag as modified
        self._image_modified = True
        
        # Apply enhancements (resets to original)
        self.apply_enhancements()
    
    def auto_enhance(self):
        """Automatically enhance the image."""
        if not self.original_image:
            logger.debug("No original image to auto-enhance")
            return
        
        logger.debug("Auto-enhancing image")
        try:
            # Convert to OpenCV for processing
            cv_image = self.pil_to_cv(self.original_image)
            
            # Apply automatic contrast and brightness adjustment
            # Convert to LAB color space
            lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
            
            # Split the LAB image into L, A, and B channels
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE to the L channel (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge the enhanced L channel with the original A and B channels
            lab = cv2.merge((l, a, b))
            
            # Convert back to BGR color space
            enhanced_cv = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            # Convert back to PIL
            enhanced_image = self.cv_to_pil(enhanced_cv)
            
            # Apply a mild sharpening
            enhancer = ImageEnhance.Sharpness(enhanced_image)
            enhanced_image = enhancer.enhance(1.5)  # Slightly sharpen
            
            # Apply mild color enhancement
            enhancer = ImageEnhance.Color(enhanced_image)
            enhanced_image = enhancer.enhance(1.2)  # Slightly increase color
            
            # Store the current enhanced image
            self.current_image = enhanced_image
            self.current_cv_image = enhanced_cv
            
            # Update enhancement values to approximate the auto-enhancement
            self.enhancement_values = {
                'brightness': 110,  # Slight brightness increase
                'contrast': 120,    # Increased contrast
                'gamma': 100,       # Neutral gamma
                'sharpness': 150,   # Increased sharpness
                'saturation': 120   # Increased saturation
            }
            
            # Update UI sliders - IMPORTANT: Block signals to prevent recursive calls
            logger.debug("Updating UI sliders to match auto-enhancement")
            
            # Brightness slider
            self.brightness_slider.blockSignals(True)
            self.brightness_slider.setValue(self.enhancement_values['brightness'])
            self.brightness_slider.blockSignals(False)
            
            # Contrast slider
            self.contrast_slider.blockSignals(True)
            self.contrast_slider.setValue(self.enhancement_values['contrast'])
            self.contrast_slider.blockSignals(False)
            
            # Gamma slider
            self.gamma_slider.blockSignals(True)
            self.gamma_slider.setValue(self.enhancement_values['gamma'])
            self.gamma_slider.blockSignals(False)
            
            # Sharpness slider
            self.sharpness_slider.blockSignals(True)
            self.sharpness_slider.setValue(self.enhancement_values['sharpness'])
            self.sharpness_slider.blockSignals(False)
            
            # Saturation slider
            self.saturation_slider.blockSignals(True)
            self.saturation_slider.setValue(self.enhancement_values['saturation'])
            self.saturation_slider.blockSignals(False)
            
            # Update labels after all sliders are set
            self.update_slider_labels()
            
            # Flag the image as modified (for save functionality)
            self._image_modified = True
            logger.debug("Auto-enhancement complete")
            
            # Convert to QPixmap and emit signal
            pixmap = self.pil_to_pixmap(enhanced_image)
            logger.debug(f"Generated enhanced QPixmap: size={pixmap.width()}x{pixmap.height()}, isNull={pixmap.isNull()}")
            self.image_changed.emit(pixmap)
            
            # Update parent dialog image directly if possible
            parent_dialog = self.window()
            if hasattr(parent_dialog, 'image_label') and parent_dialog.image_label:
                try:
                    parent_dialog.image_label.set_image(pixmap, pixmap.width(), pixmap.height())
                    logger.debug("Updated parent dialog image directly after auto-enhance")
                except Exception as e:
                    logger.error(f"Failed to update parent dialog image after auto-enhance: {e}")
        except Exception as e:
            logger.error(f"Auto-enhance failed: {e}")
            # Show error message
            QMessageBox.warning(self, "Auto Enhance Failed", f"Could not enhance image: {str(e)}")
    
    def on_compare_toggled(self, checked: bool):
        """Toggle between original and enhanced image.
        
        Args:
            checked: Whether the compare button is checked
        """
        if checked:
            # Show original
            if self.original_image:
                pixmap = self.pil_to_pixmap(self.original_image)
                self.image_changed.emit(pixmap)
                self.compare_btn.setText("Show Enhanced")
        else:
            # Show enhanced
            if self.current_image:
                pixmap = self.pil_to_pixmap(self.current_image)
                self.image_changed.emit(pixmap)
                self.compare_btn.setText("Compare")
    
    def rotate_image(self, degrees: int):
        """Rotate the image by the specified degrees.
        
        Args:
            degrees: Degrees to rotate (positive for clockwise)
        """
        if not self.original_image:
            logger.debug("No original image to rotate")
            return
        
        logger.debug(f"Rotating image by {degrees} degrees")
        try:
            # Rotate the original image
            rotated_original = self.original_image.rotate(-degrees, expand=True)  # PIL uses negative for clockwise
            
            # Store the rotated original
            self.original_image = rotated_original
            
            # Set the modified flag
            self._image_modified = True
            
            # Apply all enhancements to the new original
            self.apply_enhancements()
        except Exception as e:
            logger.error(f"Error rotating image: {e}")
            QMessageBox.warning(self, "Rotation Failed", f"Could not rotate image: {str(e)}")
    
    def save_image(self):
        """Save the enhanced image by replacing the current image file."""
        if not self.current_image:
            logger.error("No current image to save")
            return
        
        # Check if the image was actually modified
        if not self._image_modified:
            logger.debug("Image not modified, forcing modification")
            # Force a small change to ensure something is saved
            # This helps with the auto-enhance button case
            self._ensure_image_modified()
        
        # Get the parent dialog's current image path
        parent_dialog = self.window()
        current_path = ""
        if hasattr(parent_dialog, 'image_data'):
            image_data = parent_dialog.image_data
            if image_data.get("path") and image_data.get("filename"):
                current_path = os.path.join(image_data.get("path"), image_data.get("filename"))
                logger.debug(f"Found image path: {current_path}")
            else:
                logger.error(f"Missing path or filename in image_data: {image_data}")
        else:
            logger.error("Parent dialog has no image_data attribute")
        
        if not current_path:
            # If no path is available, fall back to Save As dialog
            QMessageBox.warning(
                self,
                "Save Failed",
                "Cannot determine the original image path. Please use 'Apply as New Image' instead."
            )
            return
        
        # Ensure we have a copy to work with
        save_image = self.current_image.copy()
        
        # Create a backup copy of the original file
        try:
            import shutil
            backup_path = current_path + ".backup"
            logger.debug(f"Creating backup at: {backup_path}")
            shutil.copy2(current_path, backup_path)
            logger.debug("Backup created successfully")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            # Continue anyway
        
        try:
            logger.debug(f"Saving image to original path: {current_path}")
            logger.debug(f"Current image mode: {save_image.mode}, size: {save_image.size}")
            
            # Get file modification and creation times before saving
            try:
                # Get original file stats
                file_stats = os.stat(current_path)
                creation_time = file_stats.st_ctime
                modified_time = file_stats.st_mtime
                logger.debug(f"Original file timestamps - created: {creation_time}, modified: {modified_time}")
            except Exception as e:
                logger.error(f"Could not get original file stats: {e}")
                creation_time = None
                modified_time = None
            
            # Ensure RGB mode
            if save_image.mode != 'RGB':
                logger.debug(f"Converting from {save_image.mode} to RGB")
                save_image = save_image.convert('RGB')
            
            # Save copy in memory to verify it works before touching disk
            from io import BytesIO
            img_buffer = BytesIO()
            save_image.save(img_buffer, format='PNG')
            buffer_data = img_buffer.getvalue()
            logger.debug(f"Successfully saved to memory buffer, size: {len(buffer_data)} bytes")
            
            # Determine the format from the extension
            file_format = os.path.splitext(current_path)[1].lower()
            logger.debug(f"Detected file format: {file_format}")
            
            # First try: use PIL's save method
            save_success = False
            try:
                # Save the image using different methods depending on format
                if file_format == '.jpg' or file_format == '.jpeg':
                    logger.debug("Saving as JPEG with quality 95")
                    save_image.save(current_path, 'JPEG', quality=95)
                elif file_format == '.png':
                    logger.debug("Saving as PNG")
                    save_image.save(current_path, 'PNG')
                else:
                    logger.debug(f"Unrecognized format, defaulting to PNG: {file_format}")
                    save_image.save(current_path, 'PNG')
                
                # Verify the file was actually saved
                if os.path.exists(current_path):
                    file_size = os.path.getsize(current_path)
                    logger.debug(f"File saved successfully. Size: {file_size} bytes")
                    if file_size == 0:
                        logger.error("File saved but has zero size!")
                        save_success = False
                    else:6
                        save_success = True
                else:
                    logger.error("File was not created!")
                    save_success = False
            except Exception as e:
                logger.error(f"PIL save failed: {e}")
                save_success = False
            
            # Second try: use direct file writing if PIL's save failed
            if not save_success:
                logger.debug("Trying alternative direct file writing method")
                try:
                    # Determine the format for BytesIO
                    save_format = 'JPEG' if file_format in ('.jpg', '.jpeg') else 'PNG'
                    
                    # Convert image to bytes
                    img_buffer = BytesIO()
                    save_image.save(img_buffer, format=save_format, quality=95 if save_format == 'JPEG' else None)
                    img_data = img_buffer.getvalue()
                    
                    # Write directly to file
                    with open(current_path, 'wb') as f:
                        f.write(img_data)
                    
                    # Verify file was created
                    if os.path.exists(current_path) and os.path.getsize(current_path) > 0:
                        logger.debug(f"Successfully saved using direct file writing. Size: {os.path.getsize(current_path)} bytes")
                        save_success = True
                    else:
                        logger.error("Direct file writing failed - file is empty or not created")
                        save_success = False
                except Exception as e:
                    logger.error(f"Direct file writing failed: {e}")
                    save_success = False
            
            # If both methods failed, raise an exception
            if not save_success:
                raise IOError("Failed to save image using both methods")
            
            # Try to restore the original timestamps
            if creation_time and modified_time:
                try:
                    # On Windows, we can restore the modification time but not creation time
                    # through the os module
                    os.utime(current_path, (modified_time, modified_time))
                    logger.debug("Restored file modification time")
                except Exception as e:
                    logger.error(f"Could not restore file timestamps: {e}")
            
            # Read the file back to verify it was properly saved
            try:
                from PIL import Image
                verification_image = Image.open(current_path)
                logger.debug(f"Successfully verified file can be read: {verification_image.mode}, {verification_image.size}")
            except Exception as e:
                logger.error(f"Failed to verify saved file: {e}")
            
            # Emit signal
            self.image_saved.emit(current_path)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Image Saved", 
                f"Image saved to:\n{current_path}"
            )
            
            # Update the parent dialog's image if applicable
            if hasattr(parent_dialog, 'image_label'):
                logger.debug("Updating parent dialog image")
                pixmap = self.pil_to_pixmap(save_image)
                parent_dialog.image_label.set_image(pixmap, pixmap.width(), pixmap.height())
            else:
                logger.error("Parent dialog has no image_label attribute")
            
            # After successful save, reset the modification flag
            self._image_modified = False
            
        except Exception as e:
            logger.error(f"Failed to save image: {str(e)}")
            QMessageBox.critical(
                self, 
                "Save Failed", 
                f"Failed to save image: {str(e)}"
            )
            
            # Try to restore from backup if it exists
            try:
                backup_path = current_path + ".backup"
                if os.path.exists(backup_path):
                    logger.debug("Restoring from backup")
                    shutil.copy2(backup_path, current_path)
                    logger.debug("Restored from backup successfully")
            except Exception as restore_error:
                logger.error(f"Failed to restore from backup: {restore_error}")
    
    def apply_as_new(self):
        """Apply the enhanced image as a new image in the gallery."""
        if not self.current_image:
            return
        
        # Create a dialog to confirm
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Apply Enhanced Image")
        msg_box.setText("This will add the enhanced image as a new image in the gallery.")
        msg_box.setInformativeText("The original image will remain unchanged. Continue?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            # Get the parent dialog
            parent_dialog = self.window()
            
            # Check if we can access the parent gallery widget
            if hasattr(parent_dialog, 'parent') and parent_dialog.parent():
                gallery_widget = parent_dialog.parent()
                
                # Check if the gallery has the save_image_to_story method
                if hasattr(gallery_widget, 'save_image_to_story'):
                    # Convert PIL to QImage
                    pil_image = self.current_image
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    width, height = pil_image.size
                    data = pil_image.tobytes('raw', 'RGB')
                    qimage = QImage(data, width, height, width * 3, QImage.Format.Format_RGB888)
                    
                    # Call the save method
                    gallery_widget.save_image_to_story(qimage)
                    
                    # Close the parent dialog
                    parent_dialog.accept()
                else:
                    QMessageBox.warning(
                        self,
                        "Feature Not Available",
                        "Could not access the gallery's save function."
                    )
            else:
                QMessageBox.warning(
                    self,
                    "Feature Not Available",
                    "Could not access the parent gallery widget."
                )
    
    # Helper methods for image conversion
    def pil_to_pixmap(self, pil_image: Image.Image) -> QPixmap:
        """Convert PIL Image to QPixmap.
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            QPixmap object
        """
        try:
            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                logger.debug(f"Converting PIL image from {pil_image.mode} to RGB")
                pil_image = pil_image.convert('RGB')
            
            # Try numpy method first
            try:
                # Convert PIL to numpy array
                rgb_array = np.array(pil_image)
                height, width, channels = rgb_array.shape
                logger.debug(f"PIL to numpy: shape={rgb_array.shape}, dtype={rgb_array.dtype}")
                
                # Create QImage from numpy array
                bytes_per_line = channels * width
                qimage = QImage(rgb_array.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Create QPixmap from QImage
                pixmap = QPixmap.fromImage(qimage)
                logger.debug(f"Created QPixmap via numpy: size={pixmap.width()}x{pixmap.height()}, isNull={pixmap.isNull()}")
                return pixmap
            except Exception as e:
                logger.error(f"Numpy conversion failed: {e}, falling back to temp file")
                
            # Fallback to temporary file approach
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_filename = temp_file.name
            temp_file.close()
            
            # Save PIL image to temporary file
            logger.debug(f"Saving PIL image to temporary file: {temp_filename}")
            pil_image.save(temp_filename, "PNG")
            
            # Load into QPixmap
            pixmap = QPixmap(temp_filename)
            
            # Remove temporary file
            try:
                os.unlink(temp_filename)
            except Exception as e:
                logger.error(f"Could not remove temporary file: {e}")
            
            logger.debug(f"Created QPixmap via temp file: size={pixmap.width()}x{pixmap.height()}, isNull={pixmap.isNull()}")
            return pixmap
        except Exception as e:
            logger.error(f"Error converting PIL to QPixmap: {str(e)}")
            return QPixmap()
    
    def pil_to_cv(self, pil_image: Image.Image) -> np.ndarray:
        """Convert PIL Image to OpenCV image.
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            OpenCV image (numpy array)
        """
        try:
            # Ensure RGB mode
            if pil_image.mode != 'RGB':
                logger.debug(f"Converting PIL image from {pil_image.mode} to RGB for OpenCV")
                pil_image = pil_image.convert('RGB')
            
            # Convert PIL to OpenCV
            open_cv_image = np.array(pil_image)
            
            # Convert RGB to BGR (OpenCV uses BGR)
            open_cv_image = open_cv_image[:, :, ::-1].copy()
            logger.debug(f"Converted to OpenCV: shape={open_cv_image.shape}, dtype={open_cv_image.dtype}")
            
            return open_cv_image
        except Exception as e:
            logger.error(f"Error converting PIL to OpenCV: {str(e)}")
            return np.zeros((1, 1, 3), dtype=np.uint8)  # Return small placeholder
    
    def cv_to_pil(self, cv_image: np.ndarray) -> Image.Image:
        """Convert OpenCV image to PIL Image.
        
        Args:
            cv_image: OpenCV image (numpy array)
            
        Returns:
            PIL Image object
        """
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_image)
            logger.debug(f"Converted OpenCV to PIL: mode={pil_image.mode}, size={pil_image.size}")
            
            return pil_image
        except Exception as e:
            logger.error(f"Error converting OpenCV to PIL: {str(e)}")
            return Image.new('RGB', (1, 1), color='black')  # Return small placeholder
    
    def _ensure_image_modified(self):
        """Ensure the image has been modified by making a tiny change."""
        logger.debug("Ensuring image has modifications")
        try:
            if self.current_image:
                # Convert to numpy array
                img_array = np.array(self.current_image)
                
                # Check if we have a valid image
                if img_array.shape[0] > 0 and img_array.shape[1] > 0:
                    # Choose bottom right pixel
                    h, w = img_array.shape[0] - 1, img_array.shape[1] - 1
                    
                    # Get current value
                    pixel = img_array[h, w].copy()
                    
                    # Modify value very slightly (barely noticeable)
                    if len(pixel) >= 3:  # RGB or RGBA
                        # Modify red channel slightly
                        r_value = int(pixel[0])
                        # Toggle between +1 and -1 to ensure change
                        if r_value < 255:
                            pixel[0] = r_value + 1
                        else:
                            pixel[0] = r_value - 1
                        
                        # Update the pixel
                        img_array[h, w] = pixel
                        
                        # Create new image from array
                        self.current_image = Image.fromarray(img_array)
                        logger.debug("Modified a single pixel to force save")
                        self._image_modified = True
                else:
                    logger.warning("Cannot modify image - invalid dimensions")
            else:
                logger.warning("Cannot modify image - no current image")
        except Exception as e:
            logger.error(f"Error ensuring image modification: {e}")
            # Continue anyway - we'll try to save what we have 