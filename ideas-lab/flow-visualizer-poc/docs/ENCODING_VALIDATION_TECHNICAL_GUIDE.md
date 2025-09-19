# Encoding Validation Technical Implementation Guide

## 🔧 Quick Reference

### Method Signature

```python
def validate_and_normalize_encoding(self, file_path: str) -> Tuple[str, str]:
    """
    Validate file encoding and detect/handle BOM issues before parsing.

    Args:
        file_path: Path to the .rpy file

    Returns:
        Tuple of (detected_encoding, normalized_content)

    Raises:
        RenpyParseError: If file cannot be read with any supported encoding
    """
```

### Usage Pattern

```python
# Replace old file reading:
with open(file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# With new encoding validation:
detected_encoding, content = self.validate_and_normalize_encoding(file_path)
lines = content.splitlines()
```

## 🎯 Integration Points

### 1. Individual File Parsing (`parse_file`)

```python
def parse_file(self, file_path: str) -> List[RenpyLine]:
    try:
        # Use encoding validation and BOM detection
        detected_encoding, content = self.validate_and_normalize_encoding(file_path)

        # Parse the normalized content line by line
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            parsed_line = self._parse_line(file_path, line_num, line)
            if parsed_line:
                parsed_lines.append(parsed_line)
    except Exception as e:
        raise RenpyParseError(f"Failed to parse file: {e}", file_path)
```

### 2. Flow Graph Construction (`build_flow_graph`)

```python
for rpy_file in rpy_files:
    file_path = os.path.join(project_path, rpy_file)

    try:
        # Use the new encoding validation and BOM detection
        detected_encoding, content = self.validate_and_normalize_encoding(file_path)
        lines = content.splitlines()

        for line_num, line in enumerate(lines, 1):
            # Process lines with guaranteed clean content
            label_match = self.patterns['label'].match(line)
            if label_match:
                label_name = label_match.group(1)
                label_definitions[label_name] = (file_path, line_num)
    except Exception as e:
        print(f"[ENCODING] Warning: Could not process {file_path}: {e}")
        continue
```

## 🔍 BOM Detection Logic

### Supported BOMs

```python
boms = [
    (b'\xef\xbb\xbf', 'utf-8-sig'),      # UTF-8 BOM (most common issue)
    (b'\xff\xfe', 'utf-16-le'),          # UTF-16 LE BOM
    (b'\xfe\xff', 'utf-16-be'),          # UTF-16 BE BOM
    (b'\xff\xfe\x00\x00', 'utf-32-le'),  # UTF-32 LE BOM
    (b'\x00\x00\xfe\xff', 'utf-32-be'),  # UTF-32 BE BOM
]
```

### Detection Process

```python
# Read raw bytes
with open(file_path, 'rb') as file:
    raw_bytes = file.read()

# Check for BOM
for bom_bytes, encoding in boms:
    if raw_bytes.startswith(bom_bytes):
        detected_encoding = encoding
        content_start = len(bom_bytes)  # Skip BOM bytes
        break

# Decode without BOM
if detected_encoding:
    content_bytes = raw_bytes[content_start:]
    content = content_bytes.decode(detected_encoding.replace('-sig', ''))
```

## 📊 Fallback Chain

### Encoding Priority

1. **BOM-detected encoding** (if BOM found)
2. **UTF-8** (standard, no BOM)
3. **UTF-8-sig** (UTF-8 with BOM)
4. **CP1252** (Windows-1252, common on Windows)
5. **Latin-1** (ISO-8859-1, universal fallback)

### Fallback Implementation

```python
encodings_to_try = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']

for encoding in encodings_to_try:
    try:
        content = raw_bytes.decode(encoding)
        if content and len(content.strip()) > 0:
            return encoding, content
    except (UnicodeDecodeError, UnicodeError):
        continue
```

## 🚨 Error Handling

### Exception Types

- **`IOError`**: File cannot be read (permissions, not found, etc.)
- **`UnicodeDecodeError`**: Content cannot be decoded with any encoding
- **`RenpyParseError`**: Wrapped error with file context

### Error Messages

```python
# File access error
raise RenpyParseError(f"Could not read file: {e}", file_path)

# Encoding error
raise RenpyParseError(f"Could not decode file with any supported encoding: {encodings_to_try}", file_path)

# Processing warning (non-fatal)
print(f"[ENCODING] Warning: Could not process {file_path}: {e}")
```

## 📝 Logging Output

### Successful BOM Detection

```
[ENCODING] Detected utf-8-sig BOM in T:\path\to\file.rpy
```

### BOM Detection with Decode Failure

```
[ENCODING] Warning: BOM detected but decoding failed with utf-8-sig: [error details]
```

### Processing Warning

```
[ENCODING] Warning: Could not process T:\path\to\file.rpy: [error details]
```

## 🧪 Testing

### Test Cases to Verify

1. **UTF-8 with BOM** - Should detect and strip BOM
2. **UTF-8 without BOM** - Should decode normally
3. **UTF-16 files** - Should detect BOM and decode correctly
4. **CP1252 files** - Should fallback and decode
5. **Binary files** - Should fail gracefully
6. **Empty files** - Should return empty content
7. **Permission errors** - Should raise appropriate error

### Test File Creation

```python
# Create test file with UTF-8 BOM
with open('test_bom.rpy', 'wb') as f:
    f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
    f.write('label test:\n    "Hello"'.encode('utf-8'))
```

## 🔄 Migration Guide

### Before (Old Pattern)

```python
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
except UnicodeDecodeError:
    try:
        with open(file_path, 'r', encoding='latin-1') as file:
            lines = file.readlines()
    except Exception:
        continue  # Silent failure
```

### After (New Pattern)

```python
try:
    detected_encoding, content = self.validate_and_normalize_encoding(file_path)
    lines = content.splitlines()
    # Process lines normally
except Exception as e:
    print(f"[ENCODING] Warning: Could not process {file_path}: {e}")
    continue  # Logged failure
```

## 🎯 Benefits

### Reliability

- **Handles all common encoding issues**
- **Provides clear error messages**
- **Graceful fallback chain**

### Performance

- **Single file read** (as bytes, then decode)
- **Early BOM detection** (before parsing)
- **Minimal overhead** (only adds BOM check)

### Maintainability

- **Centralized encoding logic**
- **Comprehensive logging**
- **Clear error handling**

### Compatibility

- **Works with all Python text encodings**
- **Handles Windows/Mac/Linux file differences**
- **Supports legacy encoding formats**
