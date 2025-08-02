# 🚨 CRITICAL GIT WORKFLOW WARNING 🚨

## ⛔ NEVER TOUCH GIT WITHOUT EXPLICIT USER PERMISSION ⛔

**USER IS IN COMPLETE CONTROL OF ALL GIT OPERATIONS**

### 🔒 ABSOLUTE RULES:

- **NO AUTOMATIC STAGING** - Ever, under any circumstances
- **NO AUTOMATIC COMMITS** - User stages and commits manually
- **NO GIT COMMANDS** - Unless explicitly requested by user
- **NO "HELPFUL" GIT SUGGESTIONS** - User manages their own workflow

### ❌ FORBIDDEN ACTIONS:

```bash
# NEVER RUN THESE WITHOUT USER REQUEST:
git add .
git add <file>
git commit
git push
git pull
git merge
git rebase
git stash
git reset
git checkout
```

### ✅ ALLOWED ONLY WHEN USER EXPLICITLY REQUESTS:

- Git status checks (if specifically asked)
- Git diff (if specifically asked)
- Specific git commands (only when user provides the exact command)

### 🎯 THE RULE:

**"I am the one in charge of git changes"** - User

### 📋 WHAT HAPPENED:

During MCP server installation/testing, changes were automatically staged without user permission. This violated the user's workflow control and must never happen again.

### 🛡️ PROTECTION PROTOCOL:

1. **Before any operation that might affect git**: Ask user first
2. **No assumptions**: Don't assume user wants git operations
3. **Explicit permission only**: Wait for clear git command requests
4. **Respect workflow**: User controls their development process completely

---

**REMEMBER: The user is a professional developer who manages their own git workflow. Respect that completely.**
