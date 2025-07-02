# Ren’Py Code Analysis Integration Strategy

## Understanding Ren’Py Script Structure

Ren’Py projects follow a consistent structure – all game logic and dialogue are defined in `.rpy` script files (usually under a `game/` directory), alongside assets like images and audio. These script files use Ren’Py’s own scripting language (a mix of Python and novel-specific statements for dialogue, menus, etc.). Internally, Ren’Py loads all `.rpy` files and parses them into an **Abstract Syntax Tree (AST)** representation before running the game. Each element of the story (labels, dialogues, menus, jumps, Python blocks, etc.) becomes an AST node defined in the `renpy.ast` module. For example, Ren’Py’s AST classes include `Label` (for `label name:` declarations), `Say` (for dialogue lines), `Menu` (for choice menus), `Jump`/`Call` (for control flow), and so on. This means the _structure_ of a visual novel can be programmatically analyzed by parsing these files into an AST.

Ren’Py’s built-in engine code actually provides a parser (`renpy.parser`) that tokenizes and parses .rpy files into AST nodes. Normally, the engine does this at runtime (and saves a compiled bytecode as `.rpyc` for faster reloads), but we can leverage similar logic for our analysis tool. In fact, Ren’Py’s `Script` class (in `renpy.script`) manages the collection of all parsed statements and maintains a `namemap` for quick lookup of labels and other named nodes. In short, a Ren’Py game’s code can be **read and analyzed** much like source code in any programming language – by parsing it and building data structures that represent the dialogue lines, branching choices, character definitions, etc.

However, parsing Ren’Py script is non-trivial to implement from scratch because the language has unique syntax (indented blocks, dialogue strings, Python segments embedded, etc.). To avoid reinventing the wheel, we should consider existing tools or libraries that already handle Ren’Py script parsing or analysis.

## Existing Tools and Libraries for Ren’Py Parsing

Fortunately, the Ren’Py community and developers have created several tools that can help us achieve “Ren’Py code awareness” in our app:

- **Ren’Py’s Internal Parser and AST** – As mentioned, Ren’Py itself has a robust parser. Its `renpy.parser.parse()` function (invoked during `Script.load_file_core`) can read a script file and produce AST nodes. These AST node classes (like `renpy.ast.Label`, `renpy.ast.Say`, etc.) capture all elements of the script. One approach is to use Ren’Py’s code directly: for example, by installing the Ren’Py SDK as a module or copying the relevant parts (the parser and AST definitions) into our project. This is essentially what some third-party projects have done – they extracted Ren’Py’s parser logic rather than writing their own. Using the official parser ensures we handle the full syntax correctly (including edge cases, Python blocks, the ATL animation language, etc.). The downside is that integrating Ren’Py’s code may require initializing some Ren’Py environment (it might expect certain config or engine variables). Still, it’s arguably the most complete solution if feasible.

- **Ren’Py AST for VS Code** – There is a Visual Studio Code extension called _Ren’Py Text Analyzer_ that includes script parsing capabilities. It can scan an entire project and generate stats like total word count, dialogue count, per-character word counts, and occurrences of Ren’Py statements. Under the hood, this extension has to parse .rpy files to distinguish dialogue lines from code. In fact, it boasts _“intelligent dialogue & script parsing”_ with awareness of Ren’Py syntax (it recognizes character name assignments, dialogues in various formats, and ignores Python code blocks). The extension likely uses a combination of parsing rules or a formal grammar (possibly derived from the Ren’Py language definition). Its existence proves that project-wide Ren’Py analysis can be done reliably outside the game engine. We might not directly reuse the TypeScript code, but we can emulate its approach in Python. For instance, the extension resolves which in-game character is speaking each line by reading `define X = Character("Name", ...)` statements and mapping short speaker codes to full names. It also counts occurrences of keywords like `label`, `menu`, `scene`, `show`, etc.. These are exactly the kinds of features we want. Reading through its documentation or code (if available) could guide our implementation logic.

- **Ren’Py Graphviz Flowchart** – Another great tool is **renpy-graphviz** by Ewen Quim. It’s an open-source project (written in Go) that parses Ren’Py scripts and generates a Graphviz flowchart of the game’s branching structure. Essentially, it reads all `.rpy` files, identifies labels and how they jump or call each other, and produces a node graph of the story flow. This is extremely relevant to our “branching paths” goal. We could use this tool in a couple of ways: either invoke it as an external command to get a graph (it has a CLI that outputs a `.png` or `.dot` file), or consult its source for how it parses the scripts. The repository’s `parser` package is designed to “help understand the structure of a Ren’Py game” and even offers a Go API for retrieving the parsed content. If rewriting that logic in Python, the algorithm would be: load all script files (the tool provides a function to read all lines of all .rpy files into memory), then iterate through lines tracking the current label and any menu choices or jump statements to construct a graph of label-to-label transitions. The existence of renpy-graphviz (149 stars on GitHub) shows that many have needed a clear view of branching; it’s a good model for our branch analysis module.

- **Ren’Py Parser in Other Languages** – There are even attempts to make Ren’Py parsers in other languages. For example, a Rust library **renpy_parser_rs** implements a subset of Ren’Py’s script parser, translating Ren’Py’s own Python parser into Rust. It can produce an AST of dialogues, scenes, and other statements (with some limitations like not handling full Python blocks). Similarly, the official Ren’Py VSCode language support extension has a small parser (a project called “renpy-ast” in TypeScript) extracted from the Ren’Py VSCode plugin. While you may not use these directly in a Python app, they signal that parsing Ren’Py is a solved problem and you could even consider binding one of these (e.g. call the Rust parser via FFI for speed, if needed). In most cases, though, sticking to Python and possibly leveraging Ren’Py’s own parser is simplest, since your app is Python-based.

- **Decompiling Compiled Scripts** – If you ever needed to analyze a VN where only `.rpyc` (compiled scripts) are available (no source), there are tools like **rpycdec** that can decompile `.rpyc` files back into plain text Ren’Py script. This might not be directly needed for your case (you mentioned having the open source code), but it’s good to know such tools exist. They essentially leverage Ren’Py’s own bytecode reader to spit out the script text. For completeness, I mention this in case you integrate analysis into an app that might target installed games without source – you could fall back on decompiling the scripts. (Of course, be mindful of game licenses and permissions before doing that.)

- **Community Tools for Stats** – The Ren’Py community has also shared various script analysis snippets. For example, Ren’Py’s built-in **Lint** feature already gives some basic stats (word count, missing labels or images, etc.). Developers have extended Lint to get more detailed counts. _Lint+_ by KigyoDev is a Ren’Py addon that, when included in a game and run via “Check Script (Lint)”, outputs things like per-character line and word counts, counts per file, number of menus and choices, etc. This is essentially doing in-game what we want to do externally. The existence of Lint+ (and its output) confirms that data like _“Character X has N lines and M words”_ or _“The game has Y menus with Z choices total”_ can be obtained by scanning the AST of the script. We can mirror these calculations in our tool. Similarly, a tool called **renspell** (Ren’Py Script Spell Checker) parses Ren’Py files to isolate just the dialogue text for spell-checking. It’s a pip-installable Python tool, which internally likely ignores code and gathers only strings that are shown to the player. We might peek at renspell’s implementation (on GitLab) to see how it discerns dialogue lines from code – probably using regular expressions or a simple state machine for indent and quote parsing.

In summary, you have a rich set of references. **Leveraging Ren’Py’s own parsing logic or studying these projects will save a ton of time.** For a Python-based solution, a practical route is: use Ren’Py’s parser and AST classes directly if possible, or implement a lightweight parser that covers the main Ren’Py statements (labels, menu, jump, say/dialogue, show/scene, etc.) and skips over Python code blocks. Many of the tools above did exactly that – focused on the novel script structure and ignored the internal Python bits for their analysis.

## Key Features to Implement in the VN API

You mentioned three particularly useful capabilities for the Ren’Py-aware system: **character usage stats**, **branching path mapping**, and **media asset usage**. Let’s break down how the API can implement each, once the script is parsed, as well as **free-text dialogue search** which is another common query type you described (e.g. find where a certain string appears).

### 1. Character Dialogue Usage and Queries

One feature is the ability to query dialogue lines by content (e.g. “find all lines containing _keyword_”) and identify where they occur. Along with this, tracking how many lines or words each character speaks (character usage stats) is valuable. Achieving this requires understanding who the speaker is for each line of dialogue in the script.

After parsing, your tool should have a representation of **“say” statements** – these are lines of dialogue. In Ren’Py AST terms, a dialogue line like:

```renpy
e "Hello, world!"
```

might be represented as an AST node `Say(who="e", what="Hello, world!")`. The `who` could be `None` for narrator lines or a short code like `e` (which stands for a character). Ren’Py dialogue can be written in a few forms (the VSCode analyzer extension had to handle this): it can be a bare string (treated as narrator or generic dialogue), or prefixed by a character name/variable, or use `extend` for multi-line, etc. Your parser should standardize these into a structure like `(speaker, text)` for each line.

**Character mapping:** It’s common in Ren’Py to define characters at startup, e.g. `define e = Character("Eileen")`. Your analysis should read those definitions so you know that speaker code `e` corresponds to the character named “Eileen”. The VSCode tool builds a **character map** by scanning all `define X = Character("DisplayName", ...)` statements. You can do the same: during parsing, note any lines that match the pattern for character definitions. This gives you a dictionary of speaker identifiers to character names. Then for each dialogue line’s `speaker` field, resolve it via this dictionary. This way, your API can return human-friendly names. (If no definition is found, you can default to the literal label used in script.)

**Searching dialogue:** With a list or tree of all dialogue lines (with associated speaker and location), implementing a search query is straightforward. For example, a function `find_dialogue(substring)` can scan through all dialogue texts for occurrences of the substring (case-insensitive maybe) and return a list of matches. Each match might include the line of text, the speaker, and context such as the label or file/line number. It sounds like you also want to retrieve “nearby images” – presumably meaning if there was an image shown around that line. To support that, your data structure for script might link dialogue nodes to other statement nodes around them. For instance, if a dialogue is immediately preceded by a `scene bg_beach` or a `show characterX happy`, you might include that info as context. One approach is to, when a search hit is found, look at the AST nodes just before it in the same label block to see if any are image-related (`scene`, `show`) and include those filenames in the result. This way, if you search for “I love you” and it occurs during a CG scene, the API might return the line along with “\[CG: bg_beach.png shown]”. This is a design choice, but it can make the search results richer.

**Counting lines/words per character:** Once you can iterate all dialogues with speaker info, computing usage stats is easy. You can maintain a counter for each character and increment for each line spoken. Word counts can be computed by splitting the dialogue text (taking care to strip out any inline formatting or tags). The result could be an API endpoint like `GET /stats/characters` that returns a breakdown of how many lines and words each character speaks. This is similar to the Lint+ output (e.g., _“Alice: 120 lines, 900 words”_). It’s also useful for identifying the protagonist vs side characters by volume of dialogue. If you want to get fancy, you could even do sentiment analysis per character or other NLP, but that’s beyond the core scope – the VSCode extension did implement optional sentiment analysis on each character’s lines, which is interesting for writers.

### 2. Branching Paths and Label Flow

Understanding the game’s flow is crucial – this means knowing how the story branches at menu choices and how scenes connect via jumps and calls. Your API should be able to map out the **label structure**: which label leads to which other label, what choices exist, and where they go.

A straightforward way to build this is to gather all `label` statements and any statements that affect flow (`menu` choices, `jump`, `call`, `return`). In the AST, a `Menu` node will contain a list of menu options, each option possibly leading to either a block of dialogue or a direct jump. `Jump` and `Call` nodes explicitly reference a target label. By traversing the AST (or even simpler, by doing regex on the script for “jump”/“call” if parsing is hard), you can create a directed graph where nodes are label names and edges are transitions (e.g. “label `start` -> jump to label `chapter1`”). Also treat each menu option as a branch: from the menu’s label, you have outgoing edges to the start of each option’s block or target.

To present branching info, you might generate something like a **flowchart** or at least a tree structure of choices. The renpy-graphviz project is the gold standard example – it produces a visual graph of all possible routes. You might integrate that directly (for instance, have your app call `renpy-graphviz` to produce an image), or generate a graph data (perhaps in Graphviz DOT format or JSON) that the front-end can display. Even if not visual, an API could answer questions like “what are the possible next scenes after label X” or “list all endings labels”.

For example, a query might ask “what endings does this game have?” – if you define an ending as a label with no further jumps (a terminal label) or one named “Ending”, you could scan for those. Or “show me the path from start to a specific scene” – you could run a graph search on your label network.

One thing to be mindful of is Ren’Py’s flexibility: labels can be called like subroutines and returned from, so the flow isn’t always a simple tree. Also, conditionals (`if` statements in the script or in Python blocks) can gate jumps or menu options. A full static analysis would have to consider that (which might be complex if conditions depend on variables). However, a reasonable approximation is to assume all branches are possible and just show them. Some tools tag conditional jumps differently (e.g. dotted lines in graphs to indicate a maybe-branch). The **renpy-graphviz** tool addresses ambiguous cases by allowing special comments (tags like `# renpy-graphviz: IGNORE` or `BREAK`) to manually adjust the graph, but for our purposes we probably won’t go that deep initially. We can document that some branches might only occur under certain conditions.

**Example:** _The Question_ (Ren’Py’s demo game) has a simple branch: at the start, you choose to propose “right away” or “later”, leading to different scenes (“game” or “book” paths) then merging to the ending. A flow analysis tool would identify labels `start`, `rightaway`, `later`, etc., and how they connect. In fact, renpy-graphviz’s output for The Question looks like this:

&#x20;_Example output from a Ren’Py flowchart tool (visualizing the branching routes of **The Question** demo). Each oval is a label/scene, and arrows show jumps or menu choices leading to new labels._

Your API could provide this data in textual form (e.g., a JSON listing each label and its outgoing connections). It could also answer queries like “what choices lead to the `marry` ending?” by tracing backward through the graph or storing reverse links.

Implementing this in Python: once you have all labels stored (e.g., a dict of {label_name: AST_node}), iterate over each AST node’s content:

- For a `Menu`, collect the label of the block (which would just be the current label until options end) and note transitions. In Ren’Py, a menu’s options either have an associated block under the menu or a `jump`/`call` inside the option. If it’s just a block, that means the flow continues sequentially after the block (no named label break), so in a graph you might just show it as staying within the same label context. (Some approach is needed to represent menu branches in the data, e.g., append something like label “start (choice X)” as pseudo-nodes. The renpy-graphviz tool actually invents fake nodes for menu choices to show them in the graph.)
- For `Jump/Call`, add an edge from current label to target label.
- For `Return`, mark that label as ending or returning to caller (for calls).

This can get detailed, but even a simple approach of “list every jump and menu” yields a useful adjacency list. You can refine it as needed for clarity.

### 3. Media Asset Usage Tracking

The third feature is to track usage of media assets – images, audio, video files referenced in the code – and possibly identify any assets that are present but never used. This is akin to a lightweight asset management or a superset of what Ren’Py’s Lint does (Lint will warn about images defined but not used, etc.).

To implement this, your parser or analyzer can scan for:

- **Image definitions:** Lines that start with `image` (outside of dialogue) define images or layered images. E.g. `image bg beach = "beach.png"`. Here you can extract that `"beach.png"` is used, and map the name “bg beach” to that file path.
- **Image display statements:** `scene` and `show` statements in the script will reference image names. If they reference by the defined name (like `scene bg beach`), you know the actual file if you parsed the definition. If they directly reference a tag that isn’t explicitly defined, Ren’Py will look for a file `<tag>.png` or so – you might try to infer the file name or simply record the tag. Similarly, `show expression` might be used with dynamic images (which is harder to statically resolve).
- **Audio/video:** `play music "theme.ogg"` or `play sound "gunshot.wav"` statements tell you those files are used. Likewise `movie` or `voice` if any. These appear as strings in the script typically, so a regex for quotes ending in `.ogg`, `.mp3`, `.wav`, `.mp4`, etc. could catch them if not parsed.
- **GUI assets:** Some images might be used in GUI (e.g., defined in screens or called via LiveComposite or ATL). Those might require scanning `screens.rpy` or looking at any strings with image file extensions.

A simple implementation is to gather all string literals from the script that look like file paths (or specifically filter by known asset extensions). But a more precise way (if using AST) is to handle known statement types:

- On encountering an AST node of type `Image` (if the AST has that for image definitions) or an `Init` block that defines images, record the file.
- On `Scene` or `Show` nodes, record the image name (and if we have a mapping from image name to file, resolve it).
- On `Play` or `Stop` with filename, record the media file.

After scanning, you’ll have a set of all asset files referenced by code. Then you can list all actual files in the `images/` or `audio/` directory of the project (by scanning the filesystem) and compute the difference: any file that is present but not in the referenced set might be an unused asset. This is useful for cleaning up projects or just reporting. Ren’Py Lint does something similar for images (it can tell if you defined an image that you never show). With an external tool, you can extend that to sounds or videos as well.

The API endpoints could be something like:

- `/assets/images` – returns JSON of all image files used, maybe grouped by character or scene if you want (e.g., how many CGs per route).
- `/assets/unused` – returns assets found in the folder that were never referenced.
- Possibly queries like “find where asset X is used” – which is basically a reverse lookup (you could map filename -> list of locations where it’s referenced, similar to a dialogue search but for asset names).

This feature ensures the “Ren’Py awareness” of your app covers not just text but also the multimedia content of the VN.

## Designing the Ren’Py VN Query API

With the above pieces in mind, the core strategy is to create an **index** or structured representation of the VN’s code, and then expose queries on that data. Here’s a step-by-step outline:

1. **Project Ingestion:** When given a Ren’Py project folder path, the system will locate all `.rpy` files (e.g., by scanning the directory recursively). Typically, you’d exclude certain files like `screens.rpy` or `gui.rpy` from narrative analysis (they contain UI code, not story content). Tools like renpy-graphviz explicitly ignore the `options/gui/screens` files. You can provide configuration for which subfolders to skip (e.g., an `exclude` list).

2. **Parsing Phase:** Use one of the parsing methods discussed to read the .rpy files into an internal model. If you manage to import `renpy.parser`, you could do something like:

   ```python
   import renpy.parser, renpy.ast
   script_txt = open(file.rpy).read()
   ast_nodes = renpy.parser.parse(script_txt, filename=file.rpy)
   ```

   This might return a list of AST statements. Alternatively, Ren’Py’s `renpy.script.load_script()` could populate a `renpy.script.Script` object with a `.namemap` of labels, but using that may require more engine initialization. If direct use of Ren’Py isn’t practical, you can write a simple parser: one approach is reading line by line, tracking indentation and keywords (some community tools effectively do this with regex + state machine). For example, renpy-graphviz’s parser in Go reads all lines and then iterates, keeping a context of the current label and whether inside a menu, etc., creating nodes for the graph as it goes. A Python equivalent could be done with regex: e.g.,

   - If a line matches `^label (\w+):` then start a new label context.
   - If a line starts with an image/audio statement, note the asset.
   - If it’s a menu, identify menu options.
   - If it’s a dialogue line (starts with a quote or a character name and quote), capture it.
   - If it’s a jump or call, record the link.

   This is a bit of work but certainly doable, especially if you constrain to standard Ren’Py syntax. (Using the actual Ren’Py parser is still preferable for robustness.)

3. **Data Structures:** Organize the parsed data into structures that serve your queries. Likely:

   - A list of dialogue entries (each with text, speaker, label, maybe file/line).
   - A mapping of character identifiers to display names (from definitions).
   - A graph structure for labels: e.g., `graph = {label_name: {"jumps": [targets], "calls": [targets], "menu_options": [list of (option_text, target_label)]}}`.
   - An asset usage dictionary: e.g., `assets = {"images": {file_name: [locations...]}, "audio": {file: [locations...]}}`.

   You may also keep the raw AST or line list if needed for more complex queries or for referencing original context.

4. **Query Functions/Endpoints:** Design a set of functions or API endpoints that take a query and use the above data to respond. For instance:

   - `query_dialogue(substring, context=window)` – returns occurrences of the substring in dialogue text. You can allow a `context` parameter for how many lines around the match to include or whether to include preceding image show info. This can draw from the dialogue list.
   - `get_character_stats()` – returns the precomputed line/word counts per character.
   - `get_label_flow(label=None)` – if `label` is given, return what branches out from that label (next possible labels via jumps or menus). If none given, perhaps return a global structure or starting label. You could also have `get_full_flow()` that returns a global graph or a list of all labels with their connections (essentially the adjacency list).
   - `get_menu_summary()` – returns how many menus and choices in total (from scanning all Menu nodes). For example, _“38 menus, 90 choices total”_ like the Lint+ example.
   - `list_assets(type=None, unused=False)` – return assets used (filtered by type “image” vs “audio” or “video”) or unused assets if `unused=True`.
   - `find_asset_usage(filename)` – returns where a given file is referenced (which lines or labels).

   And so on. Having a defined API like this will make it easier to integrate into your app or allow an AI agent to query it.

5. **Output Formatting:** The results can be structured (JSON, lists) since this is an internal API. But since you might be using Cursor AI or another AI to interact, you could also format results as markdown tables or text summaries for direct reading. For example, the AI could ask, “How many lines does character X have?” and the tool would respond with the number from `get_character_stats()`. Because your user might ultimately see the answer via the AI, ensure the data is clear (e.g., use character names in full).

## Caching and Performance Considerations

**Caching** is highly recommended, as you noted. Parsing all .rpy files can be moderately heavy (for a large VN, there could be thousands of lines of script). Doing that on every query would be wasteful. Instead, implement a one-time parse and reuse the results.

Possible caching strategies:

- **In-memory cache:** If the analysis is encapsulated in a persistent process (for example, a daemon or an **MCP server**, which we’ll discuss shortly), then the data structures built can live in memory and be reused for all queries until the VN files change or the process restarts. This is simplest and gives fast query responses (just dictionary lookups and list scans which are fine).
- **On-disk cache:** You could serialize the parsed AST or extracted data to disk (perhaps as JSON or pickle). Ren’Py itself saves compiled AST as `.rpyc` files, so one idea is to actually utilize those – e.g., after parsing, you might keep the .rpyc for each file and next time just load them. But reading .rpyc outside of Ren’Py might require using Ren’Py’s loader or the decompiler. Alternatively, just write your own cache file (like `.vndata` file) containing the info you need (dialogue list, stats, etc.). Then if the source files haven’t changed (check timestamps), you can load that instead of re-parsing.
- **Partial updates:** If you expect the VN script to change (if this is a development tool), then you might integrate a watcher – e.g., if the user edits a script file, invalidate or reparse that file. Otherwise, for a static released game, parsing once is enough.

Memory-wise, storing all dialogue lines and AST nodes of a typical VN is not too heavy (text mainly). Even a large game with say 100k lines of dialogue can be handled. But if you needed to scale to dozens of projects, you might consider caching per project on disk.

**Query performance:** Most queries (searching text, counting, graph traversal) are quick on these scales, but for text search, you might build an index if needed. For example, build a inverted index (word -> list of dialogue ids) if you want very fast full-text search across a huge script. Python’s `re` on a concatenated script might also suffice if performance is okay.

If your app is interactive (like an AI agent that might ask many questions about the script), caching ensures it can do so seamlessly. For instance, the first time you load a project, do the heavy lifting, and subsequent questions like “find line containing X” will hit the precomputed lists.

## Integration via MCP or External Service

Since you mentioned possibly using an **MCP server** approach: this is a great idea for scalability and modularity. _Model Context Protocol (MCP)_ is an emerging standard to let AI systems connect to tools and data via a unified interface. In an MCP setup, you would create a custom server that exposes your VN analysis functions, and the AI (acting as an MCP client) can send requests to it. The benefits:

- The server can maintain state (the parsed project data in memory) between calls.
- The AI can ask complex questions and get structured answers without needing the entire VN script in its prompt (which would be too large).
- Security and sandboxing: MCP encourages a design where the AI only accesses what you expose, making it safer and more reliable.

For example, you could implement an MCP server that has methods like `findDialogue`, `getCharacterStats`, etc., corresponding to the API we outlined. The AI’s query (through Cursor AI or another environment) would trigger those and get a JSON response which it can format into a user-friendly answer. This two-way tool usage is exactly what MCP is meant for – _“secure, two-way connections between AI models and external tools”_.

If you go this route, check if your AI environment provides an easy way to spin up custom MCP servers. There might be templates for Python microservices. Ensure your server efficiently loads the data (maybe on first request or startup) and then listens for queries.

Even outside MCP, a standard REST API or a simple Flask app around the analysis functions would work if an AI can call HTTP endpoints. The idea is to separate the heavy code-understanding logic (handled by your service) from the AI’s reasoning. The AI no longer needs to “read” the raw .rpy files (which could cause it to hallucinate or misunderstand code); instead it just asks, say, “How many endings are in this game?” and your service returns a factual answer like “3 endings (Good, Bad, and True ending)”. This makes the system more scalable and reliable.

## Conclusion and Next Steps

Bringing Ren’Py code awareness into your app is definitely feasible with the right strategy. To summarize the plan: use existing **Ren’Py parsing capabilities** (either the engine’s or custom) to build a model of the VN’s script, including dialogues, characters, labels (branches), and assets. Implement query functions for the key insights – searching dialogue by text, aggregating character dialogue counts, mapping out branching paths, and tracking asset usage. Employ **caching** so this analysis is done once per project and reused. And for scalability and integration with AI assistants (like Cursor AI), encapsulate this logic in a persistent service or **MCP server**, so the AI can query it on demand without ingesting all the code into its context.

By taking advantage of tools like the Ren’Py AST parser and learning from community projects (VS Code analyzer, graphviz mapper, etc.), you’ll avoid a lot of low-level coding and can focus on exposing “neat things” as you described. The end result will be a kind of **“Ren’Py VN API”** that can answer questions about a visual novel’s script structure instantly and accurately – a very powerful addition to your app for visual novel developers or players. Good luck with the implementation!

**Sources:** Ren’Py parsing and AST info, examples of Ren’Py analysis tools and their features, and overview of MCP for AI-tool integration.
