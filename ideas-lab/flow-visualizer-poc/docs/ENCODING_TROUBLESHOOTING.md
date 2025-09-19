# Encoding Issues Troubleshooting Guide

## 🚨 Common Symptoms

### Missing Labels

- **Problem**: Labels exist in `.rpy` files but don't appear in the flow visualizer
- **Cause**: BOM (Byte Order Mark) or encoding issues preventing parsing
- **Solution**: The encoding validation system automatically handles this

### Garbled Text

- **Problem**: Text appears with strange characters (�, Ã©, etc.)
- **Cause**: File encoding mismatch
- **Solution**: Encoding validation tries multiple encodings automatically

### Silent Parsing Failures

- **Problem**: Some `.rpy` files seem to be ignored
- **Cause**: Encoding errors causing files to be skipped
- **Solution**: Check console output for `[ENCODING]` messages

## 🔍 Diagnostic Messages

### Success Messages

```
[ENCODING] Detected utf-8-sig BOM in path/to/file.rpy
```

**Meaning**: BOM was found and handled correctly

### Warning Messages

```
[ENCODING] Warning: BOM detected but decoding failed with utf-8-sig: [details]
```

**Meaning**: BOM was found but there's a decoding issue - fallback encoding will be tried

```
[ENCODING] Warning: Could not process path/to/file.rpy: [error]
```

**Meaning**: File could not be processed with any supported encoding

## 🛠️ Manual Fixes

### If You're a VN Developer

#### Check File Encoding

1. **VS Code**: Look at bottom-right status bar for encoding
2. **Notepad++**: Check Encoding menu
3. **Sublime Text**: Check bottom status bar

#### Fix UTF-8 BOM Issues

1. **VS Code**:

   - Open file
   - Click encoding in status bar
   - Select "Save with Encoding"
   - Choose "UTF-8" (not "UTF-8 with BOM")

2. **Notepad++**:

   - Open file
   - Encoding → Convert to UTF-8 (not UTF-8-BOM)
   - Save file

3. **Command Line** (Windows):
   ```powershell
   # Remove BOM from file
   $content = Get-Content -Path "file.rpy" -Raw
   $utf8NoBom = New-Object System.Text.UTF8Encoding $false
   [System.IO.File]::WriteAllText("file.rpy", $content, $utf8NoBom)
   ```

#### Batch Fix Multiple Files

```powershell
# PowerShell script to remove BOM from all .rpy files
Get-ChildItem -Path "game" -Filter "*.rpy" -Recurse | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw
    if ($content -and $content.Length -gt 0) {
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($_.FullName, $content, $utf8NoBom)
        Write-Host "Fixed: $($_.Name)"
    }
}
```

### If You're a User

The encoding validation system handles most issues automatically. If you encounter problems:

1. **Check console output** for `[ENCODING]` messages
2. **Report the specific error** if files are being skipped
3. **Provide file samples** if certain files consistently fail

## 📊 Supported Encodings

### Automatically Detected

- **UTF-8 with BOM** (`EF BB BF`)
- **UTF-16 LE with BOM** (`FF FE`)
- **UTF-16 BE with BOM** (`FE FF`)
- **UTF-32 LE with BOM** (`FF FE 00 00`)
- **UTF-32 BE with BOM** (`00 00 FE FF`)

### Fallback Chain

1. **UTF-8** (standard)
2. **UTF-8-sig** (with BOM)
3. **CP1252** (Windows-1252)
4. **Latin-1** (ISO-8859-1)

## 🔧 Editor Configuration

### Recommended Settings

#### VS Code

```json
{
  "files.encoding": "utf8",
  "files.autoGuessEncoding": false,
  "files.insertFinalNewline": true
}
```

#### Notepad++

- Settings → Preferences → New Document
- Encoding: UTF-8 (not UTF-8-BOM)

#### Sublime Text

```json
{
  "default_encoding": "UTF-8",
  "fallback_encoding": "UTF-8"
}
```

## ⚠️ Prevention Tips

### For VN Developers

1. **Configure your editor** to save UTF-8 without BOM
2. **Use consistent encoding** across all project files
3. **Test with different editors** before releasing
4. **Include encoding guidelines** in contributor documentation

### For Content Creators

1. **Stick to UTF-8 without BOM** for maximum compatibility
2. **Avoid copy-pasting** from applications that might introduce BOM
3. **Use version control** that preserves encoding settings
4. **Test your VN** with the flow visualizer during development

## 🆘 Getting Help

### When to Report Issues

- Files consistently fail to parse despite trying multiple encodings
- Specific encoding types are not being detected correctly
- Performance issues with encoding validation

### What to Include in Reports

1. **Console output** showing `[ENCODING]` messages
2. **File samples** (first few lines of problematic files)
3. **Editor/OS information** used to create the files
4. **Steps to reproduce** the issue

### Workarounds

If encoding validation fails for specific files:

1. **Manual conversion** using the methods above
2. **Re-save files** in a different editor
3. **Contact support** with file samples for analysis

## 📚 Additional Resources

- [Unicode Consortium - BOM FAQ](https://unicode.org/faq/utf_bom.html)
- [Python Unicode Documentation](https://docs.python.org/3/howto/unicode.html)
- [File Encoding Best Practices](https://en.wikipedia.org/wiki/Byte_order_mark)

---

**Note**: The encoding validation system was specifically designed to handle these issues automatically. Most users will never need to manually fix encoding problems, but this guide is provided for edge cases and developer reference.
