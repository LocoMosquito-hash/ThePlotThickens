# CMAP Integration Guide

## Overview

This guide covers how to integrate CMAP (Custom Menu AST Parser) with existing systems, including the AST Menu Parser, Flow Visualizer, and other components of The Plot Thickens project.

## Integration Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Flow Visualizer   │    │  AST Menu Parser    │    │   Ren'Py Parser    │
│                     │    │                     │    │                     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │ Visualization │  │◄───┤  │     CMAP      │  │◄───┤  │  File Reader  │  │
│  │    Engine     │  │    │  │   Parser      │  │    │  │   & Loader    │  │
│  └───────────────┘  │    │  └───────────────┘  │    │  └───────────────┘  │
│                     │    │         │           │    │                     │
│  ┌───────────────┐  │    │  ┌───────▼───────┐  │    │  ┌───────────────┐  │
│  │  Node/Edge    │  │    │  │ Enhanced Regex │  │    │  │  Legacy Menu  │  │
│  │  Generator    │  │    │  │   Fallback     │  │    │  │    Parser     │  │
│  └───────────────┘  │    │  └───────────────┘  │    │  └───────────────┘  │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Core Integration Points

### 1. AST Menu Parser Integration

CMAP is integrated as the primary parsing method in `ASTMenuParser`:

```python
class ASTMenuParser:
    def __init__(self):
        self.has_ast = HAS_RENPY_AST
        self.has_cmap = HAS_CMAP
        self.cmap_parser = None

        if self.has_cmap:
            try:
                self.cmap_parser = CMAPParser()
                print("[AST_MENU_PARSER] ✅ CMAP parser initialized successfully")
            except Exception as e:
                print(f"[AST_MENU_PARSER] ⚠️ CMAP parser initialization failed: {e}")
                self.has_cmap = False

    def parse_file_menus(self, file_path: str) -> List[EnhancedMenuStructure]:
        """Parse all menus in a file using the best available method."""
        if self.has_ast:
            return self._parse_with_ast(file_path)
        elif self.has_cmap:
            return self._parse_with_cmap(file_path)
        else:
            return self._parse_with_regex_fallback(file_path)
```

### 2. Parsing Priority Chain

The system uses a priority chain for maximum reliability:

1. **Ren'Py AST** (if available) - Most authoritative
2. **CMAP** (if available) - True AST parsing without dependencies
3. **Enhanced Regex** (always available) - Reliable fallback

### 3. Data Structure Conversion

CMAP produces `MenuNode` objects that are converted to `EnhancedMenuStructure` for compatibility:

```python
def _convert_cmap_to_enhanced(self, cmap_menu: 'CMAPMenuNode', file_path: str, line_number: int) -> EnhancedMenuStructure:
    """Convert CMAP MenuNode to EnhancedMenuStructure."""
    enhanced_choices = []

    for choice in cmap_menu.choices:
        # Extract destinations from choice body
        destinations = []
        for statement in choice.body:
            if hasattr(statement, 'target'):  # Jump/Call statements
                destinations.append(statement.target)

        # Analyze condition if present
        condition_text = None
        condition_complexity = "simple"
        if choice.condition:
            condition_text = self._cmap_condition_to_text(choice.condition)
            condition_complexity = self._classify_condition_complexity(condition_text)

        enhanced_choice = EnhancedMenuChoice(
            text=choice.text,
            line_number=choice.line_number,
            destinations=destinations,
            is_conditional=choice.is_conditional,
            primary_condition=condition_text,
            conditional_paths=[],
            choice_complexity=condition_complexity,
            referenced_variables=self._extract_variables_from_condition(condition_text) if condition_text else []
        )
        enhanced_choices.append(enhanced_choice)

    return EnhancedMenuStructure(
        file_path=file_path,
        line_number=line_number,
        menu_name=cmap_menu.name,
        menu_set=cmap_menu.set_variable,
        choices=enhanced_choices,
        total_conditional_paths=len([c for c in enhanced_choices if c.is_conditional]),
        has_complex_conditionals=any(c.choice_complexity in ["complex", "dynamic"] for c in enhanced_choices),
        has_nested_menus=False,  # TODO: Implement nested menu detection
        menu_complexity="conditional" if any(c.is_conditional for c in enhanced_choices) else "simple",
        referenced_variables=list(set(var for choice in enhanced_choices for var in choice.referenced_variables))
    )
```

## Integration Patterns

### 1. Graceful Fallback Pattern

```python
def parse_with_fallback(self, file_path: str):
    """Parse with graceful fallback through parsing methods."""

    # Try CMAP first
    if self.has_cmap:
        try:
            result = self._parse_with_cmap(file_path)
            if result:
                return result
        except Exception as e:
            print(f"[PARSER] CMAP failed: {e}, falling back to regex")

    # Fall back to enhanced regex
    return self._parse_with_regex_fallback(file_path)
```

### 2. Hybrid Results Pattern

```python
def merge_parsing_results(self, cmap_results, regex_results):
    """Merge results from different parsing methods."""

    merged_results = []

    # Use CMAP results where available
    for cmap_menu in cmap_results:
        merged_results.append(cmap_menu)

    # Add regex results for menus CMAP couldn't parse
    cmap_lines = {menu.line_number for menu in cmap_results}
    for regex_menu in regex_results:
        if regex_menu.line_number not in cmap_lines:
            merged_results.append(regex_menu)

    return merged_results
```

### 3. Validation Pattern

```python
def validate_parsing_results(self, results):
    """Validate parsing results for consistency."""

    for menu in results:
        # Validate basic structure
        if not menu.choices:
            warnings.warn(f"Menu at line {menu.line_number} has no choices")

        # Validate conditional detection
        for choice in menu.choices:
            if choice.is_conditional and not choice.primary_condition:
                warnings.warn(f"Conditional choice missing condition at line {choice.line_number}")

        # Validate destinations
        for choice in menu.choices:
            if not choice.destinations and any(isinstance(stmt, (JumpStatementNode, CallStatementNode)) for stmt in choice.body):
                warnings.warn(f"Choice has jump/call but no destinations at line {choice.line_number}")
```

## Flow Visualizer Integration

### 1. Node Creation

CMAP results are used to create flow visualization nodes:

```python
def create_menu_nodes_from_cmap(self, cmap_results):
    """Create visualization nodes from CMAP parsing results."""

    nodes = []

    for menu in cmap_results:
        # Create menu container node
        menu_node = MenuContainerNode(
            id=f"menu_{menu.line_number}",
            label=menu.menu_name or f"Menu (line {menu.line_number})",
            choices=len(menu.choices),
            conditional_choices=len([c for c in menu.choices if c.is_conditional])
        )
        nodes.append(menu_node)

        # Create choice nodes
        for choice in menu.choices:
            choice_node = ChoiceNode(
                id=f"choice_{menu.line_number}_{choice.line_number}",
                text=choice.text,
                is_conditional=choice.is_conditional,
                condition=choice.primary_condition if choice.is_conditional else None,
                destinations=choice.destinations
            )
            nodes.append(choice_node)

    return nodes
```

### 2. Connection Generation

```python
def create_connections_from_cmap(self, cmap_results):
    """Create flow connections from CMAP parsing results."""

    connections = []

    for menu in cmap_results:
        menu_id = f"menu_{menu.line_number}"

        for choice in menu.choices:
            choice_id = f"choice_{menu.line_number}_{choice.line_number}"

            # Connect menu to choice
            connections.append(Connection(
                source=menu_id,
                target=choice_id,
                type="menu_to_choice"
            ))

            # Connect choice to destinations
            for destination in choice.destinations:
                connections.append(Connection(
                    source=choice_id,
                    target=destination,
                    type="choice_to_label",
                    conditional=choice.is_conditional,
                    condition=choice.primary_condition if choice.is_conditional else None
                ))

    return connections
```

## Configuration and Setup

### 1. Environment Setup

```python
# In your main application setup
def setup_cmap_integration():
    """Set up CMAP integration with proper error handling."""

    try:
        # Check if Lark is available
        import lark
        print(f"✅ Lark parser available (version {lark.__version__})")

        # Initialize CMAP
        from renpy_sdk.cmap import CMAPParser
        parser = CMAPParser()
        print("✅ CMAP parser initialized successfully")

        return True

    except ImportError as e:
        print(f"⚠️ CMAP dependencies not available: {e}")
        print("Falling back to regex-only parsing")
        return False
    except Exception as e:
        print(f"⚠️ CMAP initialization failed: {e}")
        return False
```

### 2. Configuration Options

```python
class CMAPConfig:
    """Configuration options for CMAP integration."""

    def __init__(self):
        # Parser options
        self.use_simple_grammar = True  # Use simple grammar by default
        self.enable_fallback = True     # Enable regex fallback
        self.strict_validation = False  # Strict AST validation

        # Performance options
        self.cache_parsed_results = True    # Cache parsing results
        self.max_file_size = 10 * 1024 * 1024  # 10MB max file size
        self.parse_timeout = 30  # 30 second timeout

        # Integration options
        self.merge_with_regex = True    # Merge CMAP and regex results
        self.validate_results = True    # Validate parsing results
        self.log_fallbacks = True       # Log when falling back to regex
```

### 3. Monitoring and Metrics

```python
class CMAPMetrics:
    """Track CMAP performance and usage metrics."""

    def __init__(self):
        self.total_files_parsed = 0
        self.cmap_successes = 0
        self.cmap_failures = 0
        self.regex_fallbacks = 0
        self.average_parse_time = 0.0
        self.total_menus_parsed = 0

    def record_parse_attempt(self, success: bool, parse_time: float, menu_count: int):
        """Record a parsing attempt."""
        self.total_files_parsed += 1

        if success:
            self.cmap_successes += 1
        else:
            self.cmap_failures += 1
            self.regex_fallbacks += 1

        # Update average parse time
        self.average_parse_time = (
            (self.average_parse_time * (self.total_files_parsed - 1) + parse_time)
            / self.total_files_parsed
        )

        self.total_menus_parsed += menu_count

    def get_success_rate(self) -> float:
        """Get CMAP success rate."""
        if self.total_files_parsed == 0:
            return 0.0
        return self.cmap_successes / self.total_files_parsed

    def print_summary(self):
        """Print metrics summary."""
        print(f"CMAP Metrics Summary:")
        print(f"  Files parsed: {self.total_files_parsed}")
        print(f"  Success rate: {self.get_success_rate():.1%}")
        print(f"  Average parse time: {self.average_parse_time:.2f}ms")
        print(f"  Total menus parsed: {self.total_menus_parsed}")
        print(f"  Regex fallbacks: {self.regex_fallbacks}")
```

## Error Handling and Debugging

### 1. Error Categories

```python
class CMAPError(Exception):
    """Base exception for CMAP errors."""
    pass

class CMAPParseError(CMAPError):
    """Error during menu parsing."""
    pass

class CMAPTransformError(CMAPError):
    """Error during AST transformation."""
    pass

class CMAPIntegrationError(CMAPError):
    """Error during integration with other systems."""
    pass
```

### 2. Debug Logging

```python
import logging

def setup_cmap_logging():
    """Set up detailed logging for CMAP operations."""

    logger = logging.getLogger('cmap')
    logger.setLevel(logging.DEBUG)

    # Create file handler
    handler = logging.FileHandler('cmap_debug.log')
    handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

# Usage in CMAP parser
logger = setup_cmap_logging()

def parse_menu_with_logging(self, menu_text):
    """Parse menu with detailed logging."""
    logger.debug(f"Parsing menu: {menu_text[:100]}...")

    try:
        result = self.parse_menu(menu_text)
        logger.info(f"Successfully parsed menu with {len(result.choices)} choices")
        return result
    except Exception as e:
        logger.error(f"Failed to parse menu: {e}")
        logger.debug(f"Menu text: {menu_text}")
        raise
```

### 3. Integration Testing

```python
def test_integration_health():
    """Test the health of CMAP integration."""

    health_checks = []

    # Check CMAP availability
    try:
        from renpy_sdk.cmap import CMAPParser
        parser = CMAPParser()
        health_checks.append(("CMAP Import", True, None))
    except Exception as e:
        health_checks.append(("CMAP Import", False, str(e)))

    # Check grammar loading
    try:
        parser._load_grammar()
        health_checks.append(("Grammar Loading", True, None))
    except Exception as e:
        health_checks.append(("Grammar Loading", False, str(e)))

    # Check basic parsing
    try:
        result = parser.parse_menu('menu:\n    "Test":\n        pass')
        success = result is not None and len(result.choices) == 1
        health_checks.append(("Basic Parsing", success, None))
    except Exception as e:
        health_checks.append(("Basic Parsing", False, str(e)))

    # Print results
    print("CMAP Integration Health Check:")
    for check_name, success, error in health_checks:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {check_name}: {status}")
        if error:
            print(f"    Error: {error}")

    return all(success for _, success, _ in health_checks)
```

## Best Practices

### 1. Integration Design

- **Loose Coupling**: Keep CMAP integration loosely coupled with other systems
- **Graceful Degradation**: Always provide fallback mechanisms
- **Error Isolation**: Don't let CMAP errors crash the entire system
- **Performance Monitoring**: Track performance impact of CMAP integration

### 2. Data Flow

- **Consistent Interfaces**: Maintain consistent data structures across parsing methods
- **Validation**: Validate data at integration boundaries
- **Transformation**: Use clear transformation functions between data formats
- **Caching**: Cache expensive parsing operations when appropriate

### 3. Maintenance

- **Version Compatibility**: Maintain compatibility across CMAP versions
- **Migration Paths**: Provide clear migration paths for updates
- **Documentation**: Keep integration documentation up to date
- **Testing**: Comprehensive integration testing for all scenarios

---

**Remember**: The goal of CMAP integration is to enhance parsing capabilities while maintaining system reliability and performance. Always prioritize graceful degradation and comprehensive error handling.
