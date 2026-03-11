# 🤖 AI Debug Assistant - Quick Start

## 🎯 Quick Guide (30 seconds)

### When You See a Bug:

```
1. Bug Alert appears with 🚨
   ↓
2. Click "🤖 Ask AI" button
   ↓
3. Press Cmd+L (Mac) or Ctrl+L (Windows)
   ↓
4. Press Cmd+V (Mac) or Ctrl+V (Windows)
   ↓
5. AI analyzes and suggests fix
   ↓
6. Apply fix → Click "✅ Mark Latest Fix Applied"
```

That's it! 🎉

---

## 🔥 What You Get

### Automatically Captured:
✅ Bug message & root cause analysis  
✅ Editor state (zoom, pan, mode, objects)  
✅ Recent 10 user actions before bug  
✅ Last 15 debug log entries  
✅ Code conflicts detected  
✅ Execution flow trace  
✅ Environment info  
✅ Stack trace  

### AI Provides:
✅ Root cause verification  
✅ Exact file & line numbers  
✅ Fix strategy explanation  
✅ Before/after code solution  
✅ Prevention suggestions  

---

## 📍 Where to Find It

### Bug Alert (Top of Debugger)
```
🚨 BUG DETECTED!
[Bug message]
Click to jump to bug details ↓  [🤖 Ask AI]
```

### AI Debug Panel (After clicking Ask AI)
```
🤖 AI DEBUG ASSISTANT
Context captured and copied to clipboard!

📋 What was copied:
• Bug: ...
• Category: ...
• Recent Actions: 10 captured
• State: Zoom 100%, Mode: BASE
• Root Cause: Analyzed ✓

Next steps:
1. Open Cursor AI Chat (Cmd+L or Ctrl+L)
2. Paste the context (Cmd+V or Ctrl+V)
3. AI will analyze and suggest fixes
4. Review and apply the suggested fix

[📋 Copy Again]
```

### AI Debug History (Collapsible Section)
```
🤖 AI DEBUG HISTORY

📊 STATISTICS
Total Bugs Analyzed: 5
Fixes Applied: 4
Fix Rate: 80%

🏷️ BUG CATEGORIES
• POSITION_JUMP: 2
• STATE_SYNC: 1
• COORDINATE_TRANSFORM: 2

📝 RECENT SESSIONS
[Shows last 5 with ✅ or ⏳ indicators]

[✅ Mark Latest Fix Applied]
```

---

## 💡 Pro Tips

1. **Use immediately** - Context is freshest right when bug occurs
2. **Be specific** - When marking fixes, describe what you changed
3. **Review patterns** - Check which bug types recur most
4. **Track progress** - Watch your fix rate improve!

---

## 🎨 Visual Indicators

| Color | Meaning |
|-------|---------|
| 🟣 Purple | AI features |
| 🟢 Green | Fixed bugs, good stats |
| 🟠 Orange | Pending bugs |
| 🔴 Red | Critical bugs, low fix rate |

---

## ⚡ Keyboard Shortcuts

| Action | Mac | Windows/Linux |
|--------|-----|---------------|
| Open AI Chat | `Cmd+L` | `Ctrl+L` |
| Paste Context | `Cmd+V` | `Ctrl+V` |

---

## 📊 What Gets Tracked

- Total bugs analyzed by AI
- Number of fixes applied
- Fix success rate (%)
- Bug category breakdown
- Recent session history (last 5)
- Fix descriptions

All saved in localStorage - persists across sessions!

---

## 🚀 Example Workflow

**Scenario**: Device jumps during drag

```
1. You drag a device
2. It jumps unexpectedly
3. 🚨 Bug alert appears: "POSITION_JUMP detected"
4. Click "🤖 Ask AI"
5. AI panel shows: "Context captured!"
6. Press Cmd+L to open Cursor chat
7. Paste with Cmd+V
8. AI responds:

   "I found the issue! In topology.js line 745,
    the getMousePos() function isn't accounting
    for backing store scaling. Here's the fix:
    
    [Shows before/after code]
    
    This will prevent coordinate mismatches."

9. Apply the fix
10. Click "✅ Mark Latest Fix Applied"
11. Enter: "Fixed coordinate transform in getMousePos"
12. Bug tracked as resolved! 🎉
```

---

## 🎁 Benefits

### Before AI Assistant:
- 😓 Manually gather bug context
- 😓 Search through logs
- 😓 Guess at root causes
- 😓 Trial and error fixes
- 😓 No fix tracking

### After AI Assistant:
- 😊 **One-click** context capture
- 😊 **Automatic** root cause analysis
- 😊 **Comprehensive** state snapshot
- 😊 **AI-powered** fix suggestions
- 😊 **Tracked** debugging progress

---

## 🔧 Technical Notes

### Storage
- `localStorage.ai_debug_history`
- Limited to 20 sessions
- Survives browser refresh

### Clipboard
- Modern API with fallback
- Works across all browsers
- Handles large contexts

### Performance
- Context capture: ~1ms
- No impact on app speed
- Efficient history management

---

## 🆘 Need Help?

See full documentation: `AI_DEBUG_ASSISTANT.md`

**Common Issues:**
- Button not showing? → Make sure debugger is open
- Not copying? → Check clipboard permissions
- History not saving? → Check localStorage enabled

---

**Built with ❤️ to make debugging easier!**

Start using it now - just wait for a bug and click "🤖 Ask AI"! 🚀

