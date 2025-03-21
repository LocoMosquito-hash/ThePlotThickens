# Timeline Feature for The Plot Thickens

The Timeline feature allows you to create, visualize, and manage events in your story's chronology. This document explains how to use the timeline feature effectively.

## Overview

The Timeline tab provides a visual representation of your story's events, allowing you to:

- Create and manage story events (scenes, chapters, arcs, etc.)
- Visualize events chronologically
- Filter events by type
- Create multiple timeline views for different purposes
- Track character participation in events

## Event Types

Events can be categorized into different types:

- **Scene**: A specific moment or interaction in your story
- **Chapter**: A larger story unit containing multiple scenes
- **Arc**: A story arc spanning multiple chapters
- **Subplot**: A secondary storyline
- **Other**: Any other event type

## Creating Events

To create a new event:

1. Click the "Add Event" button in the toolbar
2. Fill in the event details:
   - Title (required)
   - Description
   - Event Type
   - Start/End Dates
   - Location
   - Importance (1-5)
   - Color
   - Milestone status

## Timeline Views

The Timeline supports two visualization modes:

1. **Chronological View**: Events are displayed on a horizontal timeline based on their dates or sequence numbers
2. **Hierarchical View**: Events are displayed in a list format

You can create multiple named timeline views for different purposes (e.g., "Main Plot", "Character Arc", etc.) using the "+" button next to the view selector.

## Filtering Events

Use the filter dropdown to show only specific types of events:

- All
- Scenes
- Chapters
- Arcs
- Milestones

## Event Details

Click on any event to view its details in the panel at the bottom of the screen. From there, you can:

- Edit the event
- Delete the event

## Database Schema

The timeline feature uses the following database tables:

### events

- `id`: Unique identifier
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `title`: Event title
- `description`: Event description
- `event_type`: Type of event (SCENE, CHAPTER, etc.)
- `start_date`: Start date of the event
- `end_date`: End date of the event
- `location`: Location of the event
- `importance`: Importance level (1-5)
- `color`: Color for the event in the timeline
- `is_milestone`: Whether this is a milestone event
- `story_id`: ID of the story
- `parent_event_id`: ID of the parent event (for hierarchical events)
- `sequence_number`: Order in the timeline

### event_characters

- `event_id`: ID of the event
- `character_id`: ID of the character
- `role`: Role of the character in the event
- `notes`: Additional notes

### timeline_views

- `id`: Unique identifier
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `name`: View name
- `description`: View description
- `view_type`: Type of view (CHRONOLOGICAL, CHARACTER_FOCUSED, etc.)
- `layout_data`: JSON string with layout data
- `story_id`: ID of the story

## Future Enhancements

Planned enhancements for the timeline feature include:

1. Character participation management in events
2. More sophisticated date handling
3. Timeline zooming and navigation controls
4. Drag-and-drop event reordering
5. Event relationships and dependencies
6. Export timeline as image
