"""
IMPORTANT: Fixed methods for GalleryWidget class.

The current version of gallery_widget.py has errors in the show_filters_dialog and apply_filters 
methods where they use 'story_id' instead of 'current_story_id'. 

Please manually edit the file app/views/gallery_widget.py to replace:

1. In show_filters_dialog method (around line 4129):
   - Change "if not self.story_id:" to "if not self.current_story_id:"
   - Change "dialog = GalleryFilterDialog(self.db_conn, self.story_id, self)" to
     "dialog = GalleryFilterDialog(self.db_conn, self.current_story_id, self)"

2. In apply_filters method (around line 4159):
   - Change "all_images = get_story_images(self.db_conn, self.story_id)" to
     "all_images = get_story_images(self.db_conn, self.current_story_id)"

Also, add the missing update_filter_status method from the previous file.

Here are the corrected methods:
"""

from app.views.gallery_widget import GalleryFilterDialog

def show_filters_dialog(self):
    """Show the gallery filters dialog."""
    if not self.current_story_id:
        return
        
    # Initialize active filters if needed
    if not hasattr(self, 'active_filters'):
        self.active_filters = []
        
    # Create the dialog
    dialog = GalleryFilterDialog(self.db_conn, self.current_story_id, self)
    
    # Set the current filters
    dialog.character_filters = self.active_filters.copy() if hasattr(self, 'active_filters') else []
    
    # Show the dialog
    if dialog.exec():
        # Get the filters
        self.active_filters = dialog.get_character_filters()
        
        # Apply the filters
        self.apply_filters()
        
        # Update status with filter info
        self.update_filter_status()

def apply_filters(self):
    """Apply the active filters to the gallery."""
    if not hasattr(self, 'active_filters') or not self.active_filters:
        # If no filters, reload all images
        self.load_images()
        return
        
    # Get all images
    from app.db_sqlite import get_story_images, get_image_character_tags
        
    try:
        # Get all images for the story
        all_images = get_story_images(self.db_conn, self.current_story_id)
        filtered_images = []
        
        # For each image, check if it matches the filters
        for image in all_images:
            # Get character tags for this image
            tags = get_image_character_tags(self.db_conn, image['id'])
            tagged_character_ids = [tag['character_id'] for tag in tags]
            
            # Check if image satisfies filter conditions
            satisfies_filters = True
            
            for character_id, include in self.active_filters:
                if include:
                    # Must include this character
                    if character_id not in tagged_character_ids:
                        satisfies_filters = False
                        break
                else:
                    # Must exclude this character
                    if character_id in tagged_character_ids:
                        satisfies_filters = False
                        break
            
            # If image satisfies all filters, add it to the filtered list
            if satisfies_filters:
                filtered_images.append(image)
        
        # Clear all existing thumbnails
        self.clear_thumbnails()
        
        # Handle empty result
        if not filtered_images:
            self.status_label.setText("No images match the current filters.")
            return
            
        # Display the filtered images
        if self.scene_grouping_mode:
            self._display_images_with_scene_grouping(filtered_images)
        else:
            self._display_images_classic_view(filtered_images)
            
        # Update status
        self.update_filter_status()
            
    except Exception as e:
        print(f"Error applying filters: {e}")
        self.status_label.setText(f"Error: {str(e)}")

def update_filter_status(self) -> None:
    """Update the status label with info about current filters."""
    # If no active filters, nothing special to show
    if not hasattr(self, 'active_filters') or not self.active_filters:
        return
        
    # Count included and excluded filters
    include_count = sum(1 for _, include in self.active_filters if include)
    exclude_count = sum(1 for _, include in self.active_filters if not include)
    
    # Get the number of images
    visible_count = len(self.thumbnails) if self.thumbnails else 0
    
    # Create filter status
    filter_parts = []
    if include_count > 0:
        filter_parts.append(f"{include_count} included")
    if exclude_count > 0:
        filter_parts.append(f"{exclude_count} excluded")
        
    if filter_parts:
        filter_text = f"Filters active: {', '.join(filter_parts)}"
        self.status_label.setText(f"Gallery: {visible_count} images • {filter_text}") 