"""
This file contains the update_filter_status method that needs to be added to the 
GalleryWidget class in app/views/gallery_widget.py.

Add this method right after the apply_filters method (around line 4198).
"""

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