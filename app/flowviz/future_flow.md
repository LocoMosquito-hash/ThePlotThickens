# PT: Flow Visualizer and SDK Parsing.

## Future workflow.

### Setup:

- Every game will now have several versions available for analysis and extraction of metadata. This approach aims to:

  - Try to have a working (untouched, originally compiled) version of the game.
  - At the same time have decompiled versions of the same game.
  - Deal with game versioning.
  - Deal better with tasks that may include deleting, renaming or editing files.

-
- For that purpose, every game will have an unlimited number of "slots". Each slot is in itself a working copy of the game. Not a literal copy, because sometimes they will contain different versions.
- When the user already has created a story in the Story Manager, they will need to create a new slot and add the actual game there.

- Next step is running an SDK-based extraction of the game slot's AST metadata. Just like we do in the Flow Visualizer POC (FlowVizPOC)

- The metadata will be stored in an immediately consummable format; JSON files, db, parquet or whatever works best. The aim here is caching the metadata from the game slot, capturing elements like labels, menus, screens, jumps, calls, etc.

### For the Flow Visualizer (FlowViz):

- Based on the Flow Visualizer POC. A pilot of an idea to make it possible to plot all the narrative flows, according to the game source.
- It extracts the AST metadata via Renpy SDK, to extract the contents of key narrative nodes, like labels, menus, screens, jumps, and indicate what other nodes come in and go out of it.

- The AHS (Authoritative Hierarchical System) assigns unique hashes to each node, to prevent ambiguities and make the connections more precise.
- Finally, the UI is presented as interconnected nodes representing the basic blocks of narrative flow in a renpy game: labels, menus, menu choices, screens and screen buttons. Starting with the start label and exploring all the possible paths in parent-child and sibling relationships.

### Integration with existing features in TPT:

- Dialog Search tab (to be renamed or even replaced because it has been, and will be expanded to more than that):

  - It will be able to consume the metadata in the caches coming from the SDK parser, allowing label searches by name or partial dialog lines.
  - It will need to be able to resolve renpy "scene" statements to actual graphic files like images and videos. Audio files will not be needed.
  - By pinpointing a particular label, it will be able to locate all the graphic files used in that context, just like it does now.
  - Just as it works now, it will be able to copy the files it finds to the stack in the Screenshots tab.
  - Summarizing, the most important change is making the Dialog Search consume Renpy SDK provided data, instead of grep and regex-based extractions as it does now, which has proven to be severely limited and exhaustingly escalabe and maintainable.

- Decision Points:
  - Same as the current state of the Dialog search, the Source Lookup tab in the Edit Decision Point window greps for partial dialogues and brings back the menus that contain it to help create a decision point.
  - It will consume the game AST cache, and be able to search menus and choices more precisely. It could also use the same approach for screen elements.

### Important guidelines for the migration:

- For some of the many components I will ask you to make it capable of being launched standalone. It means that in the process of debugging and testing we may need to launch that component many times, so it makes sense to write it in a way that can be independent of the TPT app, so we don't need to launch it, load a game, and make several clicks to make sure it's working correctly.
