# BOM (Byte Order Mark) Encoding Issue Resolution

## 📋 Overview

This document explains the BOM encoding issue that was preventing certain labels from being detected in Ren'Py visual novels, and the comprehensive solution implemented to resolve it.

## 🐛 The Problem

### Issue Description

Labels at the beginning of certain `.rpy` files were not being detected by the flow visualizer, causing them to be missing from the generated flow graph. This resulted in "orphaned" menu choices that pointed to non-existent labels.

### Specific Case

- **File**: `romanceday05script2b_1.rpy` in "16 years later" VN
- **Missing Label**: `day5rom` at line 1
- **Symptom**: Label existed in file but was not created as a visualization node
- **Impact**: Menu choice "I'll go look for [chloe]." had no destination node

## 🔍 Root Cause Analysis

### What is a BOM (Byte Order Mark)?

A **Byte Order Mark (BOM)** is a special Unicode character sequence placed at the beginning of text files to indicate:

- The encoding format (UTF-8, UTF-16, UTF-32)
- The byte order (little-endian or big-endian for multi-byte encodings)

### Common BOM Signatures

| Encoding  | BOM Bytes     | Description                             |
| --------- | ------------- | --------------------------------------- |
| UTF-8     | `EF BB BF`    | UTF-8 with BOM (unnecessary but common) |
| UTF-16 LE | `FF FE`       | UTF-16 Little Endian                    |
| UTF-16 BE | `FE FF`       | UTF-16 Big Endian                       |
| UTF-32 LE | `FF FE 00 00` | UTF-32 Little Endian                    |
| UTF-32 BE | `00 00 FE FF` | UTF-32 Big Endian                       |

### How BOM Caused the Issue

1. **File Creation**: The `romanceday05script2b_1.rpy` file was created with a UTF-8 BOM
2. **Old Parser Logic**: Used simple `open(file, 'r', encoding='utf-8')`
3. **BOM Interference**: The BOM bytes were included in the first line content
4. **Regex Failure**: Label regex `r'^\s*label\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*:'` failed to match because the line started with BOM bytes instead of "label"
5. **Silent Skip**: The label was silently ignored during parsing

### Evidence Found

```
[ENCODING] Detected utf-8-sig BOM in T:\AG\sixteenyearslaternb-episode5.3-pc\game\romanceday05script2b_1.rpy
```

The encoding detection revealed that **multiple files** in the VN had UTF-8 BOMs, indicating this was a systematic issue, not just one problematic file.

## 💡 The Solution

### Comprehensive Encoding Validation

We implemented a proactive encoding validation system that handles BOM detection and removal **before** any parsing begins.

#### New Method: `validate_and_normalize_encoding()`

```python
def validate_and_normalize_encoding(self, file_path: str) -> Tuple[str, str]:
    """
    Validate file encoding and detect/handle BOM issues before parsing.

    Returns:
        Tuple of (detected_encoding, normalized_content)
    """
```

#### Key Features

1. **BOM Detection**: Reads raw bytes and detects all common BOM types
2. **Multiple Encoding Support**: Tries UTF-8, UTF-8-sig, CP1252, Latin-1
3. **BOM Stripping**: Automatically removes BOM bytes from content
4. **Fallback Chain**: Graceful degradation through encoding options
5. **Error Handling**: Comprehensive error reporting for debugging

#### Supported BOMs

```python
boms = [
    (b'\xef\xbb\xbf', 'utf-8-sig'),    # UTF-8 BOM
    (b'\xff\xfe', 'utf-16-le'),        # UTF-16 LE BOM
    (b'\xfe\xff', 'utf-16-be'),        # UTF-16 BE BOM
    (b'\xff\xfe\x00\x00', 'utf-32-le'), # UTF-32 LE BOM
    (b'\x00\x00\xfe\xff', 'utf-32-be'), # UTF-32 BE BOM
]
```

#### Encoding Fallback Chain

```python
encodings_to_try = [
    'utf-8',        # Standard UTF-8 (no BOM)
    'utf-8-sig',    # UTF-8 with BOM
    'cp1252',       # Windows-1252 (common for Windows)
    'latin-1',      # ISO-8859-1 (fallback)
]
```

### Integration Points

The encoding validation was integrated into **two critical methods**:

1. **`parse_file()`** - For individual file parsing
2. **`build_flow_graph()`** - For flow graph construction (the key fix)

#### Before (Problematic):

```python
try:
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
except UnicodeDecodeError:
    try:
        with open(file_path, 'r', encoding='latin-1') as file:
            lines = file.readlines()
    except Exception:
        continue
```

#### After (Fixed):

```python
try:
    # Use the new encoding validation and BOM detection
    detected_encoding, content = self.validate_and_normalize_encoding(file_path)
    lines = content.splitlines()
    # ... continue with parsing
except Exception as e:
    print(f"[ENCODING] Warning: Could not process {file_path}: {e}")
    continue
```

## ✅ Results

### Immediate Fix

- **`day5rom` label now detected**: `[HIERARCHY] Created label node: day5rom (hash: 05647bf5)`
- **`chloepillsvisitrom` label now detected**: `[HIERARCHY] Created label node: chloepillsvisitrom (hash: 3b5dfb75)`
- **Menu choice connection restored**: "I'll go look for [chloe]." → `chloepillsvisitrom`

### Systematic Improvement

The fix detected and resolved BOM issues in **many files** across the VN:

```
[ENCODING] Detected utf-8-sig BOM in T:\AG\sixteenyearslaternb-episode5.3-pc\game\day05script2b_1.rpy
[ENCODING] Detected utf-8-sig BOM in T:\AG\sixteenyearslaternb-episode5.3-pc\game\day06script (2).rpy
[ENCODING] Detected utf-8-sig BOM in T:\AG\sixteenyearslaternb-episode5.3-pc\game\day06scriptromance.rpy
[ENCODING] Detected utf-8-sig BOM in T:\AG\sixteenyearslaternb-episode5.3-pc\game\romanceday05script2b_1.rpy
... and many more
```

## 🛠️ Technical Details

### Why UTF-8 BOM is Problematic

1. **UTF-8 doesn't need BOM**: UTF-8 is byte-order independent
2. **Microsoft Legacy**: Windows tools often add UTF-8 BOM unnecessarily
3. **Text Processing Issues**: Many parsers don't handle BOM correctly
4. **Silent Failures**: BOM bytes are often invisible but break regex matching

### Detection Process

1. **Read Raw Bytes**: `with open(file_path, 'rb') as file: raw_bytes = file.read()`
2. **Check BOM Signatures**: Compare first bytes against known BOM patterns
3. **Strip BOM**: Remove BOM bytes from content: `content_bytes = raw_bytes[content_start:]`
4. **Decode Clean Content**: `content = content_bytes.decode(detected_encoding)`

### Performance Considerations

- **Single Read**: File is read once as bytes, then processed
- **Early Detection**: BOM detection happens before any parsing
- **Minimal Overhead**: Only adds BOM checking to existing file I/O
- **Caching Potential**: Could cache encoding detection results if needed

## 🔧 Usage Guidelines

### For Developers

1. **Always use encoding validation** for text file processing
2. **Don't assume UTF-8 without BOM** - many Windows-created files have BOM
3. **Handle encoding errors gracefully** - provide fallback options
4. **Log encoding detection** for debugging purposes

### For Content Creators

1. **Avoid UTF-8 BOM** when possible - use UTF-8 without BOM
2. **Use consistent encoding** across all `.rpy` files in a project
3. **Test with different editors** - some add BOM automatically
4. **Consider encoding when sharing files** between different systems

## 🚨 Prevention

### Recommended File Creation Practices

1. **Configure editors** to save UTF-8 without BOM
2. **Use version control** that preserves encoding settings
3. **Validate encoding** in build/test processes
4. **Document encoding requirements** for contributors

### Editor Settings

- **VS Code**: Set `"files.encoding": "utf8"` (without BOM)
- **Notepad++**: Format → Encode in UTF-8 (not UTF-8 BOM)
- **Sublime Text**: Set `"default_encoding": "UTF-8"`

## 📚 References

- [Unicode Standard - Byte Order Mark](https://unicode.org/faq/utf_bom.html)
- [Python Unicode HOWTO](https://docs.python.org/3/howto/unicode.html)
- [UTF-8 BOM Issues](https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8)

## 🏁 Conclusion

The BOM encoding issue was a subtle but systematic problem that caused silent parsing failures. By implementing comprehensive encoding validation with BOM detection and removal, we:

1. **Fixed the immediate issue** - `day5rom` label now appears in visualizer
2. **Solved the systematic problem** - all BOM-affected files now parse correctly
3. **Improved robustness** - parser now handles diverse encoding scenarios
4. **Provided debugging visibility** - encoding detection is logged for troubleshooting

This solution ensures that the flow visualizer can handle Ren'Py files created on different systems with different encoding settings, making it more reliable and user-friendly.


