# Google for Context and Best Practices

**Always search the web** when you need external knowledge, context, best practices, or when facing unfamiliar concepts.

## When to Google

✅ **Search for:**
- Language/framework syntax you're uncertain about
- Best practices for a specific technology
- Design patterns and architectural approaches
- API documentation and usage examples
- Error messages and their solutions
- Performance optimization techniques
- Security best practices
- Tool/library capabilities and limitations
- Industry standards and conventions
- Alternative approaches to a problem
- Real-world examples of implementations

## What to Search For

### Technical Concepts

```
Examples:
- "Ren'Py menu syntax conditional choices"
- "Python Lark parser LALR vs Earley"
- "PyQt6 layout manager best practices"
- "Python regex lookahead assertions"
- "AST transformation patterns"
```

### Best Practices

```
Examples:
- "Python dataclass performance best practices"
- "Graph visualization layout algorithms"
- "Flow diagram hierarchical layout"
- "Error handling patterns Python"
- "Code organization large Python projects"
```

### Problem-Specific Solutions

```
Examples:
- "Python Unicode encoding Windows PowerShell"
- "Lark grammar ambiguous rules resolution"
- "PyQt6 prevent window blocking main thread"
- "Graph cycle detection algorithms"
- "Menu parsing nested structures"
```

### Tool/Library Usage

```
Examples:
- "Lark parser priority terminals"
- "PyQt6 QGraphicsScene custom items"
- "Python regex named groups"
- "networkx directed graph traversal"
- "Ren'Py screen language imagemap hotspots"
```

## Search Strategy

### 1. **Be Specific with Context**

❌ Bad: "menu parsing"
✅ Good: "Ren'Py menu syntax with conditional choices and nested blocks"

❌ Bad: "graph layout"
✅ Good: "hierarchical graph layout algorithm for directed acyclic graphs"

### 2. **Include Version Numbers When Relevant**

```
- "PyQt6 QGraphicsView" (not PyQt5)
- "Python 3.11 match statement" (if using that version)
- "Lark 1.x grammar syntax" (if relevant)
```

### 3. **Search for Multiple Perspectives**

When facing a design decision, search for:
- Official documentation
- Stack Overflow discussions
- Blog posts with real-world examples
- GitHub issues and discussions
- Academic papers (for algorithms)

### 4. **Verify Information Currency**

- Prefer recent results (last 2-3 years)
- Check if information applies to current versions
- Cross-reference multiple sources

## How to Apply Findings

### Before Implementation

```python
# 1. Google the approach
# Search: "Python parser generator comparison Lark vs PLY"

# 2. Understand the trade-offs
# - Performance: Lark (LALR) vs Lark (Earley)
# - Ease of use: Grammar readability
# - Features: What each supports

# 3. Choose based on requirements
# Decision: Lark with LALR for performance
```

### During Implementation

```python
# Google specific syntax as needed
# Search: "Lark grammar priority terminals syntax"

# Apply immediately:
TRUE.2: "True"  # Priority 2, higher than IDENTIFIER
FALSE.2: "False"
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
```

### When Stuck

```python
# 1. Google the exact error
# Search: "Lark Unexpected token Token('IDENTIFIER')"

# 2. Find similar issues
# - Stack Overflow solutions
# - GitHub issues in Lark repo
# - Documentation examples

# 3. Adapt the solution to your case
```

## Common Scenarios

### Scenario 1: Unfamiliar Syntax

**Situation:** Encountering Ren'Py syntax you haven't seen before

**Action:**
```
1. Search: "Ren'Py [specific syntax] documentation"
2. Search: "Ren'Py [syntax] examples"
3. Check official Ren'Py documentation
4. Look for real game examples on GitHub
```

### Scenario 2: Performance Issue

**Situation:** Parsing is slow for large games

**Action:**
```
1. Search: "Python parser performance optimization"
2. Search: "[specific tool] performance best practices"
3. Search: "profiling Python code bottlenecks"
4. Apply profiling, then search for specific optimizations
```

### Scenario 3: Design Decision

**Situation:** Choosing between multiple approaches

**Action:**
```
1. Search: "[approach A] vs [approach B] pros cons"
2. Search: "when to use [approach A]"
3. Search: "[approach A] real world examples"
4. Make informed decision based on findings
```

### Scenario 4: Error/Bug

**Situation:** Encountering unexpected behavior

**Action:**
```
1. Search: exact error message in quotes
2. Search: "[tool] [specific scenario] not working"
3. Search: "[tool] GitHub issues [keywords]"
4. Check if others have encountered the same issue
```

### Scenario 5: Architectural Pattern

**Situation:** Need to design a system component

**Action:**
```
1. Search: "[pattern name] design pattern Python"
2. Search: "[use case] architecture best practices"
3. Search: "[similar system] implementation examples"
4. Adapt pattern to your specific needs
```

## Quality Checks

After searching, verify:

✅ **Relevance** - Does this apply to your exact situation?
✅ **Recency** - Is this information current?
✅ **Authority** - Is the source reliable?
✅ **Completeness** - Do you understand the trade-offs?
✅ **Applicability** - Can you implement this in your codebase?

## Documentation

After applying findings:

```python
# Document your decisions with sources
# Example:

# Grammar design based on Lark documentation:
# https://lark-parser.readthedocs.io/en/latest/grammar.html#terminals
# Using priority notation (.N) to resolve IDENTIFIER ambiguity
TRUE.2: "True"     # Higher priority than IDENTIFIER
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/  # Default priority
```

## Common Search Patterns

### For Syntax
```
"[technology] [feature] syntax"
"[technology] [feature] documentation"
"[technology] [feature] examples"
```

### For Best Practices
```
"[technology] best practices [year]"
"[technology] [use case] patterns"
"[technology] dos and don'ts"
```

### For Troubleshooting
```
"[tool] [error message]"
"[tool] not working [scenario]"
"[tool] GitHub issues [keywords]"
```

### For Comparisons
```
"[option A] vs [option B]"
"when to use [option A]"
"[option A] pros and cons"
```

### For Implementation
```
"[technology] [feature] tutorial"
"[technology] [feature] step by step"
"how to [specific task] [technology]"
```

## Remember

🔍 **Don't guess** - Google when uncertain
📚 **Learn continuously** - Technology evolves
🎯 **Be specific** - Better searches = better results
✅ **Verify** - Cross-reference multiple sources
📝 **Document** - Share what you learned
🔄 **Adapt** - Tailor solutions to your context

---

**Philosophy:** It's better to spend 2 minutes Googling than 20 minutes debugging incorrect assumptions.

**Frequency:** Google liberally throughout development - it's a core skill, not a weakness.


